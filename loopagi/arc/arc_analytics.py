"""Polars-powered analytics engine for the ARC-AGI solver.

Provides three capabilities:

1. **Grid analysis** — vectorized grid comparison, diff computation,
   wrong-cell summaries using Polars DataFrames.
2. **Candidate tracking** — rank and select from multiple synthesized
   programs (Best-of-N sampling, mutation populations).
3. **Eval analytics** — load JSONL results, compute summaries, compare
   evaluation runs side-by-side.

Usage:
    from loopagi.arc.arc_analytics import ArcAnalytics

    analytics = ArcAnalytics()
    analytics.add_candidate("task1", hyp_id=0, sample_id=0, ...)
    best = analytics.best_candidate("task1")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import polars as pl

logger = logging.getLogger(__name__)

# Type alias used across the ARC modules.
Grid = list[list[int]]


# ---------------------------------------------------------------------------
# Grid analysis helpers
# ---------------------------------------------------------------------------


def grid_to_df(grid: Grid, label: str = "") -> pl.DataFrame:
    """Convert a 2-D grid to a flat Polars DataFrame.

    Columns: ``row`` (Int32), ``col`` (Int32), ``value`` (Int32),
    ``label`` (Utf8).
    """
    rows: list[int] = []
    cols: list[int] = []
    vals: list[int] = []
    for r, row in enumerate(grid):
        for c, val in enumerate(row):
            rows.append(r)
            cols.append(c)
            vals.append(val)
    return pl.DataFrame(
        {
            "row": pl.Series(rows, dtype=pl.Int32),
            "col": pl.Series(cols, dtype=pl.Int32),
            "value": pl.Series(vals, dtype=pl.Int32),
            "label": [label] * len(rows),
        }
    )


def grid_diff(expected: Grid, actual: Grid) -> pl.DataFrame:
    """Compute a cell-level diff between two grids.

    Returns a DataFrame with columns ``row``, ``col``,
    ``expected``, ``actual`` containing only the cells that differ.
    Returns an empty DataFrame when the grids are identical.
    """
    exp_df = grid_to_df(expected, "expected").rename({"value": "expected"}).drop("label")
    act_df = grid_to_df(actual, "actual").rename({"value": "actual"}).drop("label")

    merged = exp_df.join(act_df, on=["row", "col"])
    return merged.filter(pl.col("expected") != pl.col("actual"))


def wrong_cell_summary(expected: Grid, actual: Grid) -> dict[str, Any]:
    """Return a compact summary of wrong cells between two grids.

    Keys: ``total_cells``, ``wrong_cells``, ``similarity``,
    ``wrong_positions`` (list of (row, col, expected, actual)).
    """
    diff = grid_diff(expected, actual)
    exp_rows = len(expected)
    exp_cols = len(expected[0]) if expected else 0
    total = exp_rows * exp_cols

    wrong_positions: list[tuple[int, int, int, int]] = []
    for row_dict in diff.iter_rows(named=True):
        wrong_positions.append(
            (row_dict["row"], row_dict["col"], row_dict["expected"], row_dict["actual"])
        )

    return {
        "total_cells": total,
        "wrong_cells": diff.height,
        "similarity": 1.0 - diff.height / total if total else 0.0,
        "wrong_positions": wrong_positions,
    }


# ---------------------------------------------------------------------------
# Candidate tracking
# ---------------------------------------------------------------------------

_CANDIDATE_SCHEMA = {
    "task_id": pl.Utf8,
    "hyp_id": pl.Int32,
    "sample_id": pl.Int32,
    "similarity": pl.Float64,
    "wrong_cells": pl.Int32,
    "total_cells": pl.Int32,
    "shape_match": pl.Boolean,
    "exec_ms": pl.Float64,
    "error": pl.Utf8,
}

_MUTATION_SCHEMA = {
    "task_id": pl.Utf8,
    "parent_id": pl.Int32,
    "generation": pl.Int32,
    "mutation_type": pl.Utf8,
    "target": pl.Utf8,
    "similarity": pl.Float64,
    "delta": pl.Float64,
}

_ITERATION_SCHEMA = {
    "task_id": pl.Utf8,
    "iteration": pl.Int32,
    "hyp_id": pl.Int32,
    "similarity": pl.Float64,
    "delta": pl.Float64,
    "stagnant": pl.Boolean,
}


class ArcAnalytics:
    """Polars-powered analytics engine for ARC solver evaluation."""

    def __init__(self) -> None:
        self._candidates: list[dict[str, Any]] = []
        self._mutations: list[dict[str, Any]] = []
        self._iterations: list[dict[str, Any]] = []

    # -- Candidates -----------------------------------------------------------

    def add_candidate(
        self,
        task_id: str,
        hyp_id: int,
        sample_id: int,
        similarity: float,
        wrong_cells: int = 0,
        total_cells: int = 0,
        shape_match: bool = True,
        exec_ms: float = 0.0,
        error: str | None = None,
    ) -> None:
        """Record a candidate program evaluation."""
        self._candidates.append(
            {
                "task_id": task_id,
                "hyp_id": hyp_id,
                "sample_id": sample_id,
                "similarity": similarity,
                "wrong_cells": wrong_cells,
                "total_cells": total_cells,
                "shape_match": shape_match,
                "exec_ms": exec_ms,
                "error": error,
            }
        )

    @property
    def candidates(self) -> pl.DataFrame:
        """Return all candidates as a Polars DataFrame."""
        if not self._candidates:
            return pl.DataFrame(schema=_CANDIDATE_SCHEMA)
        return pl.DataFrame(self._candidates)

    def best_candidate(self, task_id: str) -> dict[str, Any] | None:
        """Return the best candidate for a task by composite score."""
        df = self.candidates.filter(pl.col("task_id") == task_id)
        if df.is_empty():
            return None
        scored = df.filter(pl.col("error").is_null()).with_columns(
            (
                pl.col("similarity") * 0.7
                + pl.col("shape_match").cast(pl.Float64) * 0.2
                + (1.0 / (1.0 + pl.col("exec_ms") / 1000.0)) * 0.1
            ).alias("composite")
        )
        if scored.is_empty():
            return None
        return scored.sort("composite", descending=True).row(0, named=True)

    def top_candidates(self, task_id: str, n: int = 5) -> pl.DataFrame:
        """Return the top N candidates for a task."""
        return (
            self.candidates
            .filter((pl.col("task_id") == task_id) & pl.col("error").is_null())
            .sort("similarity", descending=True)
            .head(n)
        )

    # -- Mutations ------------------------------------------------------------

    def add_mutation(
        self,
        task_id: str,
        parent_id: int,
        generation: int,
        mutation_type: str,
        target: str,
        similarity: float,
        delta: float,
    ) -> None:
        """Record a mutation evaluation."""
        self._mutations.append(
            {
                "task_id": task_id,
                "parent_id": parent_id,
                "generation": generation,
                "mutation_type": mutation_type,
                "target": target,
                "similarity": similarity,
                "delta": delta,
            }
        )

    @property
    def mutations(self) -> pl.DataFrame:
        """Return all mutations as a Polars DataFrame."""
        if not self._mutations:
            return pl.DataFrame(schema=_MUTATION_SCHEMA)
        return pl.DataFrame(self._mutations)

    def mutation_stats(self, task_id: str) -> pl.DataFrame:
        """Aggregate mutation stats by type for a task."""
        df = self.mutations.filter(pl.col("task_id") == task_id)
        if df.is_empty():
            return df
        return (
            df.group_by("mutation_type")
            .agg(
                pl.len().alias("count"),
                pl.col("delta").mean().alias("mean_delta"),
                pl.col("delta").max().alias("max_delta"),
                (pl.col("delta") > 0).sum().alias("improvements"),
                pl.col("similarity").max().alias("best_sim"),
            )
            .sort("best_sim", descending=True)
        )

    # -- Iterations -----------------------------------------------------------

    def add_iteration(
        self,
        task_id: str,
        iteration: int,
        hyp_id: int,
        similarity: float,
        delta: float = 0.0,
        stagnant: bool = False,
    ) -> None:
        """Record an iteration result."""
        self._iterations.append(
            {
                "task_id": task_id,
                "iteration": iteration,
                "hyp_id": hyp_id,
                "similarity": similarity,
                "delta": delta,
                "stagnant": stagnant,
            }
        )

    @property
    def iterations(self) -> pl.DataFrame:
        """Return all iterations as a Polars DataFrame."""
        if not self._iterations:
            return pl.DataFrame(schema=_ITERATION_SCHEMA)
        return pl.DataFrame(self._iterations)

    def improvement_curve(self, task_id: str) -> pl.DataFrame:
        """Return the similarity improvement curve for a task."""
        return (
            self.iterations
            .filter(pl.col("task_id") == task_id)
            .sort("iteration")
        )

    # -- Eval analytics (static) ----------------------------------------------

    @staticmethod
    def load_eval(jsonl_path: str | Path) -> pl.LazyFrame:
        """Load a JSONL eval results file as a Polars LazyFrame."""
        return pl.scan_ndjson(str(jsonl_path))

    @staticmethod
    def eval_summary(lf: pl.LazyFrame) -> pl.DataFrame:
        """Compute per-complexity summary from an eval LazyFrame."""
        return (
            lf.group_by("complexity")
            .agg(
                pl.col("similarity").mean().alias("mean_sim"),
                pl.col("similarity").median().alias("median_sim"),
                (pl.col("similarity") >= 0.9).sum().alias("near_misses_90"),
                (pl.col("similarity") >= 0.95).sum().alias("near_misses_95"),
                (pl.col("similarity") >= 1.0).sum().alias("solved"),
                pl.col("iterations").mean().alias("mean_iters"),
                pl.col("time_seconds").sum().alias("total_time"),
                pl.len().alias("task_count"),
            )
            .sort("complexity")
            .collect()
        )

    @staticmethod
    def compare_evals(
        run_a_path: str | Path,
        run_b_path: str | Path,
        label_a: str = "run_a",
        label_b: str = "run_b",
    ) -> pl.DataFrame:
        """Compare two eval runs side-by-side on matching task_ids."""
        a = pl.scan_ndjson(str(run_a_path)).select(
            ["task_id", "similarity", "time_seconds"]
        )
        b = pl.scan_ndjson(str(run_b_path)).select(
            ["task_id", "similarity", "time_seconds"]
        )

        return (
            a.rename({"similarity": f"sim_{label_a}", "time_seconds": f"time_{label_a}"})
            .join(
                b.rename({"similarity": f"sim_{label_b}", "time_seconds": f"time_{label_b}"}),
                on="task_id",
            )
            .with_columns(
                (pl.col(f"sim_{label_b}") - pl.col(f"sim_{label_a}")).alias("sim_delta"),
            )
            .sort("sim_delta", descending=True)
            .collect()
        )

    # -- Export ---------------------------------------------------------------

    def export_candidates(self, path: Path) -> None:
        """Write candidates DataFrame to a Parquet file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        self.candidates.write_parquet(str(path))
        logger.info("Exported %d candidates to %s", len(self._candidates), path)

    def export_report(self, path: Path) -> None:
        """Write a Markdown summary report."""
        cands = self.candidates
        muts = self.mutations

        lines = ["# ARC Analytics Report\n"]

        if not cands.is_empty():
            lines.append("## Candidates\n")
            lines.append(f"- Total candidates: {cands.height}")
            lines.append(f"- Unique tasks: {cands['task_id'].n_unique()}")
            lines.append(f"- Mean similarity: {cands['similarity'].mean():.4f}")
            lines.append(f"- Max similarity: {cands['similarity'].max():.4f}")
            lines.append(f"- Errors: {cands.filter(pl.col('error').is_not_null()).height}")
            lines.append("")

        if not muts.is_empty():
            lines.append("## Mutations\n")
            lines.append(f"- Total mutations: {muts.height}")
            lines.append(f"- Improvements: {muts.filter(pl.col('delta') > 0).height}")
            lines.append(f"- Best delta: {muts['delta'].max():.4f}")
            lines.append("")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Exported report to %s", path)
