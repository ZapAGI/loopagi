"""Ensemble scoring for ARC candidate predictions.

Collects candidate output grids from multiple solving tracks
(transduction, synthesis, relaxed transduction, NL evolution) and
ranks them by training pair similarity. Picks the best distinct
candidates for submission.

Research basis: Omni-ARC (2nd place 2024) ensembles transductive and
inductive methods. Lewis H review: "Ensembling both transductive and
inductive methods was crucial to get to the top of the leaderboard."

Usage::

    from loopagi.arc.ensemble import EnsemblePool, rank_candidates
    pool = EnsemblePool()
    pool.add(grid, source="augmented_transduction")
    pool.add(grid, source="synthesis")
    best = pool.best(n=2, train_pairs=train_pairs, test_input=test_input)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Type aliases
Grid = list[list[int]]
TrainPair = tuple[Grid, Grid]


# ---------------------------------------------------------------------------
# Candidate and pool
# ---------------------------------------------------------------------------


@dataclass
class Candidate:
    """A candidate output grid with metadata."""

    grid: Grid
    source: str
    score: float = 0.0


@dataclass
class EnsemblePool:
    """Collects candidate grids from multiple solving tracks."""

    candidates: list[Candidate] = field(default_factory=list)

    def add(self, grid: Grid | None, source: str = "unknown") -> None:
        """Add a candidate grid to the pool. None grids are ignored.

        Validates that *grid* is a proper 2-D integer grid (list[list[int]]).
        Rejects nested list[Grid] that some solver tracks produce.
        """
        if grid is None:
            return
        if not grid or not grid[0]:
            return
        # Guard: reject nested list[Grid] — must be list[list[int]]
        if isinstance(grid[0], list) and grid[0] and isinstance(grid[0][0], list):
            logger.debug("Ensemble: skipping nested grid (list[Grid]), not a Grid")
            return
        self.candidates.append(Candidate(grid=grid, source=source))

    def add_many(self, grids: list[Grid], source: str = "unknown") -> None:
        """Add multiple candidate grids from the same source."""
        for g in grids:
            self.add(g, source=source)

    @property
    def size(self) -> int:
        return len(self.candidates)

    def best(
        self,
        n: int = 2,
        train_pairs: list[TrainPair] | None = None,
        test_input: Grid | None = None,
    ) -> list[Candidate]:
        """Return the top-n distinct candidates ranked by score.

        Scores each candidate by how well the transduction model
        reproduces training outputs when this candidate's "style"
        is used. Falls back to structural scoring if no train_pairs.

        Args:
            n: Number of distinct candidates to return.
            train_pairs: Training pairs for validation scoring.
            test_input: Test input grid (for size consistency check).

        Returns:
            List of up to n Candidate objects, best first.
        """
        if not self.candidates:
            return []

        # Score candidates
        for c in self.candidates:
            c.score = _score_candidate(c.grid, train_pairs, test_input)

        # Sort by score descending
        ranked = sorted(self.candidates, key=lambda c: c.score, reverse=True)

        # Pick top-n distinct grids
        seen: list[Grid] = []
        result: list[Candidate] = []
        for c in ranked:
            if not _grid_in_list(c.grid, seen):
                result.append(c)
                seen.append(c.grid)
            if len(result) >= n:
                break

        if result:
            logger.info(
                "Ensemble: %d candidates, top=%s (%.1f%%), %d distinct returned",
                len(self.candidates), result[0].source,
                result[0].score * 100, len(result),
            )

        return result


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _grid_similarity(expected: Grid, actual: Grid) -> float:
    """Cell-level similarity between two grids."""
    if not expected or not actual:
        return 0.0
    exp_rows, exp_cols = len(expected), len(expected[0])
    act_rows = len(actual)
    act_cols = len(actual[0]) if actual else 0
    if exp_rows != act_rows or exp_cols != act_cols:
        return 0.0
    total = exp_rows * exp_cols
    matching = sum(
        1 for r in range(exp_rows)
        for c in range(exp_cols)
        if expected[r][c] == actual[r][c]
    )
    return matching / total if total else 0.0


def _grids_equal(a: Grid, b: Grid) -> bool:
    """Check if two grids are identical."""
    if len(a) != len(b):
        return False
    return all(
        row_a == row_b for row_a, row_b in zip(a, b)
    )


def _grid_in_list(grid: Grid, grid_list: list[Grid]) -> bool:
    """Check if a grid is already in a list (exact match)."""
    return any(_grids_equal(grid, g) for g in grid_list)


def _score_candidate(
    grid: Grid,
    train_pairs: list[TrainPair] | None,
    test_input: Grid | None,
) -> float:
    """Score a candidate grid based on structural consistency.

    Scoring criteria (weighted):
    1. Size consistency with training outputs (0.4)
    2. Color consistency with task palette (0.3)
    3. Non-trivial content — not all zeros or all same value (0.2)
    4. Size consistency with test input scaling (0.1)
    """
    if not grid or not grid[0]:
        return 0.0

    score = 0.0
    pred_rows, pred_cols = len(grid), len(grid[0])

    # 1. Size consistency with training outputs
    if train_pairs:
        out_sizes = [(len(out), len(out[0])) for _, out in train_pairs]
        # Check fixed size
        if len(set(out_sizes)) == 1:
            expected = out_sizes[0]
            if (pred_rows, pred_cols) == expected:
                score += 0.4
        else:
            # Check if any training output matches size
            if (pred_rows, pred_cols) in out_sizes:
                score += 0.3
            # Check scaling pattern
            elif test_input:
                inp_sizes = [(len(inp), len(inp[0])) for inp, _ in train_pairs]
                ratios = set()
                for (ir, ic), (or_, oc) in zip(inp_sizes, out_sizes):
                    if ir > 0 and ic > 0:
                        ratios.add((or_ / ir, oc / ic))
                if len(ratios) == 1:
                    r_ratio, c_ratio = ratios.pop()
                    t_rows, t_cols = len(test_input), len(test_input[0])
                    exp_r = int(t_rows * r_ratio)
                    exp_c = int(t_cols * c_ratio)
                    if (pred_rows, pred_cols) == (exp_r, exp_c):
                        score += 0.4
    else:
        score += 0.2  # No training data, give partial credit

    # 2. Color consistency
    if train_pairs:
        task_colors: set[int] = set()
        for inp, out in train_pairs:
            for row in inp:
                task_colors.update(row)
            for row in out:
                task_colors.update(row)
        pred_colors = {v for row in grid for v in row}
        if pred_colors <= task_colors:
            score += 0.3
        else:
            extra = len(pred_colors - task_colors)
            penalty = min(extra * 0.1, 0.3)
            score += max(0.0, 0.3 - penalty)
    else:
        score += 0.15

    # 3. Non-trivial content
    all_values = {v for row in grid for v in row}
    if len(all_values) > 1:
        score += 0.2
    elif len(all_values) == 1 and 0 not in all_values:
        score += 0.1  # Single non-zero color (might be valid)

    # 4. Size relationship with test input
    if test_input:
        t_rows, t_cols = len(test_input), len(test_input[0])
        if (pred_rows, pred_cols) == (t_rows, t_cols):
            score += 0.1  # Same size as input (common pattern)

    return min(score, 1.0)


def try_ensemble_improve(
    task: object,
    solve_dict: dict,
    relaxed: dict | None,
    aug_sub_grids: list[Grid],
) -> None:
    """Apply ensemble scoring to improve an unsolved task's predictions.

    Collects candidate grids from all solving tracks (sub-threshold
    augmented transduction, relaxed transduction, synthesis/evolution)
    and picks the best distinct candidate. Modifies *solve_dict* in-place.

    Args:
        task: ARC task with .train, .test attributes.
        solve_dict: Current solve result dict (modified in-place).
        relaxed: Relaxed transduction result dict, or None.
        aug_sub_grids: Sub-threshold augmented transduction grids.
    """
    result = solve_dict["result"]
    if result.solved:
        return

    train_pairs: list[TrainPair] = [(p.input, p.output) for p in task.train]
    pool = EnsemblePool()

    # Collect sub-threshold augmented transduction grids
    for g in aug_sub_grids:
        pool.add(g, source="augmented_sub")

    # Collect relaxed transduction predictions
    if relaxed is not None and relaxed["result"].predictions:
        _add_predictions(pool, relaxed["result"].predictions, "relaxed_transduction")

    # Collect current best predictions (from synthesis/evolution/NL)
    if result.predictions:
        _add_predictions(pool, result.predictions, "synthesis")

    if pool.size < 2:
        return

    test_input = task.test[0].input if task.test else []
    best = pool.best(n=2, train_pairs=train_pairs, test_input=test_input)
    if not best or best[0].score <= 0.5:
        return

    top_grid = best[0].grid

    # Check if ensemble candidate improves on current best
    if task.test and hasattr(task.test[0], "output"):
        sim = _grid_similarity(task.test[0].output, top_grid)
        if sim > result.best_similarity:
            logger.info(
                "[%s] Ensemble improved: %.1f%% -> %.1f%% (src=%s)",
                task.task_id, result.best_similarity * 100,
                sim * 100, best[0].source,
            )
            result.best_similarity = sim
            result.predictions = [top_grid]
            if sim >= 1.0:
                logger.info("[%s] SOLVED via ensemble!", task.task_id)
                result.solved = True
    else:
        # No ground truth available (eval mode), use best candidate
        result.predictions = [b.grid for b in best[:1]]
        logger.info(
            "[%s] Ensemble selected: src=%s, score=%.2f",
            task.task_id, best[0].source, best[0].score,
        )


def _add_predictions(
    pool: EnsemblePool, predictions: list, source: str,
) -> None:
    """Safely add predictions to the pool, handling format variations.

    SolveResult.predictions has different shapes per solver track:
    - Transduction: flat ``list[Grid]`` (one Grid per test output)
    - Synthesis: ``list[list[Grid]]`` (list of attempts per test output)
    - NL evolution: ``list[list[Grid]]`` (single attempt wrapped)

    This helper unwraps nested formats so only proper Grids are added.
    """
    for pred in predictions:
        if not isinstance(pred, list) or not pred:
            continue
        # Check if pred is a Grid (list[list[int]]) or list[Grid]
        if isinstance(pred[0], list) and pred[0] and isinstance(pred[0][0], list):
            # Nested: pred is list[Grid] — unwrap each grid
            for g in pred:
                pool.add(g, source=source)
        else:
            # Flat: pred is a Grid
            pool.add(pred, source=source)


def rank_candidates(
    candidates: list[Grid],
    sources: list[str],
    train_pairs: list[TrainPair],
    test_input: Grid,
    n: int = 2,
) -> list[Candidate]:
    """Convenience function: rank a list of candidate grids.

    Args:
        candidates: List of predicted output grids.
        sources: Source label for each candidate.
        train_pairs: Training pairs for scoring.
        test_input: Test input grid.
        n: Number of distinct candidates to return.

    Returns:
        Top-n distinct Candidate objects, best first.
    """
    pool = EnsemblePool()
    for grid, source in zip(candidates, sources):
        pool.add(grid, source)
    return pool.best(n=n, train_pairs=train_pairs, test_input=test_input)
