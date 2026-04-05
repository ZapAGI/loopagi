"""Tests for loopagi.arc.arc_analytics — Polars analytics engine."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import polars as pl
import pytest

from loopagi.arc.arc_analytics import (
    ArcAnalytics,
    grid_diff,
    grid_to_df,
    wrong_cell_summary,
)


# ---------------------------------------------------------------------------
# grid_to_df
# ---------------------------------------------------------------------------

class TestGridToDf:
    """Tests for grid_to_df helper."""

    def test_basic_grid(self):
        grid = [[1, 2], [3, 4]]
        df = grid_to_df(grid, "test")
        assert df.height == 4
        assert set(df.columns) == {"row", "col", "value", "label"}
        assert df["label"][0] == "test"

    def test_values_correct(self):
        grid = [[0, 5], [9, 1]]
        df = grid_to_df(grid)
        vals = df.sort(["row", "col"])["value"].to_list()
        assert vals == [0, 5, 9, 1]

    def test_single_cell(self):
        grid = [[7]]
        df = grid_to_df(grid)
        assert df.height == 1
        assert df["value"][0] == 7

    def test_empty_label(self):
        grid = [[0]]
        df = grid_to_df(grid)
        assert df["label"][0] == ""

    def test_dtypes(self):
        grid = [[1, 2], [3, 4]]
        df = grid_to_df(grid)
        assert df["row"].dtype == pl.Int32
        assert df["col"].dtype == pl.Int32
        assert df["value"].dtype == pl.Int32


# ---------------------------------------------------------------------------
# grid_diff
# ---------------------------------------------------------------------------

class TestGridDiff:
    """Tests for grid_diff helper."""

    def test_identical_grids(self):
        grid = [[1, 2], [3, 4]]
        diff = grid_diff(grid, grid)
        assert diff.is_empty()

    def test_single_cell_different(self):
        expected = [[1, 2], [3, 4]]
        actual = [[1, 2], [3, 0]]
        diff = grid_diff(expected, actual)
        assert diff.height == 1
        row = diff.row(0, named=True)
        assert row["row"] == 1
        assert row["col"] == 1
        assert row["expected"] == 4
        assert row["actual"] == 0

    def test_all_cells_different(self):
        expected = [[1, 2], [3, 4]]
        actual = [[5, 6], [7, 8]]
        diff = grid_diff(expected, actual)
        assert diff.height == 4

    def test_columns(self):
        expected = [[0]]
        actual = [[1]]
        diff = grid_diff(expected, actual)
        assert set(diff.columns) == {"row", "col", "expected", "actual"}


# ---------------------------------------------------------------------------
# wrong_cell_summary
# ---------------------------------------------------------------------------

class TestWrongCellSummary:
    """Tests for wrong_cell_summary helper."""

    def test_identical(self):
        grid = [[1, 2], [3, 4]]
        s = wrong_cell_summary(grid, grid)
        assert s["total_cells"] == 4
        assert s["wrong_cells"] == 0
        assert s["similarity"] == 1.0
        assert s["wrong_positions"] == []

    def test_one_wrong(self):
        expected = [[1, 2, 3], [4, 5, 6]]
        actual = [[1, 2, 3], [4, 0, 6]]
        s = wrong_cell_summary(expected, actual)
        assert s["total_cells"] == 6
        assert s["wrong_cells"] == 1
        assert abs(s["similarity"] - (5 / 6)) < 1e-9
        assert s["wrong_positions"] == [(1, 1, 5, 0)]

    def test_all_wrong(self):
        expected = [[1, 1], [1, 1]]
        actual = [[0, 0], [0, 0]]
        s = wrong_cell_summary(expected, actual)
        assert s["wrong_cells"] == 4
        assert s["similarity"] == 0.0


# ---------------------------------------------------------------------------
# ArcAnalytics — Candidates
# ---------------------------------------------------------------------------

class TestAnalyticsCandidates:
    """Tests for candidate tracking."""

    def test_empty(self):
        a = ArcAnalytics()
        assert a.candidates.is_empty()
        assert a.best_candidate("x") is None

    def test_add_and_retrieve(self):
        a = ArcAnalytics()
        a.add_candidate("t1", hyp_id=0, sample_id=0, similarity=0.8)
        a.add_candidate("t1", hyp_id=0, sample_id=1, similarity=0.95)
        assert a.candidates.height == 2

    def test_best_candidate(self):
        a = ArcAnalytics()
        a.add_candidate("t1", hyp_id=0, sample_id=0, similarity=0.8)
        a.add_candidate("t1", hyp_id=0, sample_id=1, similarity=0.95)
        a.add_candidate("t1", hyp_id=0, sample_id=2, similarity=0.7, error="crash")
        best = a.best_candidate("t1")
        assert best is not None
        assert best["similarity"] == 0.95

    def test_best_candidate_wrong_task(self):
        a = ArcAnalytics()
        a.add_candidate("t1", hyp_id=0, sample_id=0, similarity=0.8)
        assert a.best_candidate("t2") is None

    def test_top_candidates(self):
        a = ArcAnalytics()
        for i in range(10):
            a.add_candidate("t1", hyp_id=0, sample_id=i, similarity=i * 0.1)
        top = a.top_candidates("t1", n=3)
        assert top.height == 3
        assert top["similarity"][0] == pytest.approx(0.9)

    def test_all_errors_returns_none(self):
        a = ArcAnalytics()
        a.add_candidate("t1", hyp_id=0, sample_id=0, similarity=0.0, error="fail")
        assert a.best_candidate("t1") is None


# ---------------------------------------------------------------------------
# ArcAnalytics — Mutations
# ---------------------------------------------------------------------------

class TestAnalyticsMutations:
    """Tests for mutation tracking."""

    def test_empty(self):
        a = ArcAnalytics()
        assert a.mutations.is_empty()

    def test_add_and_stats(self):
        a = ArcAnalytics()
        a.add_mutation("t1", parent_id=0, generation=0, mutation_type="constant",
                       target="color=3→5", similarity=0.96, delta=0.01)
        a.add_mutation("t1", parent_id=0, generation=0, mutation_type="constant",
                       target="color=3→7", similarity=0.93, delta=-0.02)
        a.add_mutation("t1", parent_id=0, generation=0, mutation_type="operator",
                       target=">→>=", similarity=0.98, delta=0.03)

        stats = a.mutation_stats("t1")
        assert stats.height == 2  # 2 mutation types
        # operator should be first (best_sim = 0.98)
        assert stats["mutation_type"][0] == "operator"

    def test_stats_empty_task(self):
        a = ArcAnalytics()
        a.add_mutation("t1", 0, 0, "constant", "x", 0.9, 0.0)
        stats = a.mutation_stats("t2")
        assert stats.is_empty()


# ---------------------------------------------------------------------------
# ArcAnalytics — Iterations
# ---------------------------------------------------------------------------

class TestAnalyticsIterations:
    """Tests for iteration tracking."""

    def test_empty(self):
        a = ArcAnalytics()
        assert a.iterations.is_empty()

    def test_improvement_curve(self):
        a = ArcAnalytics()
        a.add_iteration("t1", 0, hyp_id=0, similarity=0.5, delta=0.0)
        a.add_iteration("t1", 1, hyp_id=0, similarity=0.7, delta=0.2)
        a.add_iteration("t1", 2, hyp_id=0, similarity=0.75, delta=0.05)

        curve = a.improvement_curve("t1")
        assert curve.height == 3
        assert curve["similarity"].to_list() == [0.5, 0.7, 0.75]


# ---------------------------------------------------------------------------
# ArcAnalytics — Eval analytics
# ---------------------------------------------------------------------------

class TestEvalAnalytics:
    """Tests for static eval analysis methods."""

    def _write_jsonl(self, tmpdir: str, data: list[dict]) -> str:
        path = str(Path(tmpdir) / "eval.jsonl")
        with open(path, "w") as f:
            for entry in data:
                f.write(json.dumps(entry) + "\n")
        return path

    def test_load_eval(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._write_jsonl(tmpdir, [
                {"task_id": "a", "similarity": 0.9, "time_seconds": 10, "iterations": 5, "complexity": "medium"},
                {"task_id": "b", "similarity": 0.5, "time_seconds": 20, "iterations": 10, "complexity": "high"},
            ])
            lf = ArcAnalytics.load_eval(path)
            assert isinstance(lf, pl.LazyFrame)
            df = lf.collect()
            assert df.height == 2

    def test_eval_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._write_jsonl(tmpdir, [
                {"task_id": "a", "similarity": 0.95, "time_seconds": 10, "iterations": 5, "complexity": "medium"},
                {"task_id": "b", "similarity": 0.50, "time_seconds": 20, "iterations": 10, "complexity": "high"},
                {"task_id": "c", "similarity": 0.92, "time_seconds": 15, "iterations": 8, "complexity": "medium"},
            ])
            lf = ArcAnalytics.load_eval(path)
            summary = ArcAnalytics.eval_summary(lf)
            assert summary.height == 2  # medium + high
            medium = summary.filter(pl.col("complexity") == "medium")
            assert medium["task_count"][0] == 2
            assert medium["near_misses_90"][0] == 2

    def test_compare_evals(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path_a = self._write_jsonl(tmpdir, [
                {"task_id": "a", "similarity": 0.5, "time_seconds": 10},
                {"task_id": "b", "similarity": 0.7, "time_seconds": 20},
            ])
            path_b = str(Path(tmpdir) / "eval_b.jsonl")
            with open(path_b, "w") as f:
                f.write(json.dumps({"task_id": "a", "similarity": 0.9, "time_seconds": 8}) + "\n")
                f.write(json.dumps({"task_id": "b", "similarity": 0.6, "time_seconds": 25}) + "\n")

            comp = ArcAnalytics.compare_evals(path_a, path_b, "old", "new")
            assert comp.height == 2
            # Task "a" improved most (+0.4)
            assert comp["task_id"][0] == "a"
            assert comp["sim_delta"][0] == pytest.approx(0.4)


# ---------------------------------------------------------------------------
# ArcAnalytics — Export
# ---------------------------------------------------------------------------

class TestExport:
    """Tests for export methods."""

    def test_export_candidates_parquet(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a = ArcAnalytics()
            a.add_candidate("t1", 0, 0, similarity=0.9)
            path = Path(tmpdir) / "cands.parquet"
            a.export_candidates(path)
            assert path.exists()
            loaded = pl.read_parquet(str(path))
            assert loaded.height == 1

    def test_export_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a = ArcAnalytics()
            a.add_candidate("t1", 0, 0, similarity=0.9)
            a.add_mutation("t1", 0, 0, "constant", "x", 0.95, 0.05)
            path = Path(tmpdir) / "report.md"
            a.export_report(path)
            assert path.exists()
            text = path.read_text()
            assert "Candidates" in text
            assert "Mutations" in text
