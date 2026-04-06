"""Augmentation-based voting for ARC transduction.

Generates D4 symmetry augmentations of a task (4 rotations × 2 reflections),
runs transduction on each, reverses the augmentations, and majority-votes
on the output grid. LLMs reason better about horizontal patterns than
vertical ones, so augmentations expose different aspects of the task.

Usage:
    from loopagi.arc.augmentation_voter import vote_transduction
    result = vote_transduction(bridge, train_pairs, test_input)
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loopagi.arc.grid_ops import (
    reflect_horizontal,
    reflect_vertical,
    rotate_180,
    rotate_ccw,
    rotate_cw,
)

if TYPE_CHECKING:
    from loopagi.arc.llm_bridge import LLMBridge

logger = logging.getLogger(__name__)

# Type aliases
Grid = list[list[int]]
TrainPair = tuple[Grid, Grid]


# ---------------------------------------------------------------------------
# Augmentation definitions (D4 symmetry group)
# ---------------------------------------------------------------------------

@dataclass
class Augmentation:
    """A reversible grid augmentation."""

    name: str
    forward: callable  # Grid -> Grid
    reverse: callable  # Grid -> Grid


def _identity(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def _get_augmentations() -> list[Augmentation]:
    """Return the 8 D4 symmetry augmentations."""
    return [
        Augmentation("identity", _identity, _identity),
        Augmentation("rot90", rotate_cw, rotate_ccw),
        Augmentation("rot180", rotate_180, rotate_180),
        Augmentation("rot270", rotate_ccw, rotate_cw),
        Augmentation("flip_h", reflect_horizontal, reflect_horizontal),
        Augmentation("flip_v", reflect_vertical, reflect_vertical),
        Augmentation("rot90+flip_h",
                      lambda g: reflect_horizontal(rotate_cw(g)),
                      lambda g: rotate_ccw(reflect_horizontal(g))),
        Augmentation("rot90+flip_v",
                      lambda g: reflect_vertical(rotate_cw(g)),
                      lambda g: rotate_ccw(reflect_vertical(g))),
    ]


# ---------------------------------------------------------------------------
# Voting result
# ---------------------------------------------------------------------------

@dataclass
class VoteResult:
    """Result of augmentation-based voting."""

    grid: Grid | None
    agreement: float
    n_valid: int
    n_total: int
    method: str = "augmentation_vote"
    per_augmentation: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core voting
# ---------------------------------------------------------------------------


def _majority_vote_grid(grids: list[Grid]) -> Grid | None:
    """Cell-wise majority vote across multiple grids.

    All grids must have the same shape. Returns None if no grids provided
    or shapes are inconsistent.
    """
    if not grids:
        return None

    rows = len(grids[0])
    cols = len(grids[0][0]) if rows else 0

    # Filter to grids matching the most common shape
    shape_counts: Counter = Counter()
    for g in grids:
        shape_counts[(len(g), len(g[0]) if g else 0)] += 1
    target_shape = shape_counts.most_common(1)[0][0]
    matching = [g for g in grids if (len(g), len(g[0]) if g else 0) == target_shape]

    if not matching:
        return None

    rows, cols = target_shape
    result: Grid = []
    total_cells = rows * cols
    agreeing_cells = 0

    for r in range(rows):
        row: list[int] = []
        for c in range(cols):
            votes = Counter(g[r][c] for g in matching)
            winner = votes.most_common(1)[0][0]
            winner_count = votes.most_common(1)[0][1]
            if winner_count == len(matching):
                agreeing_cells += 1
            row.append(winner)
        result.append(row)

    return result


def _compute_agreement(grids: list[Grid]) -> float:
    """Compute the fraction of cells where all grids agree."""
    if len(grids) < 2:
        return 1.0

    rows = len(grids[0])
    cols = len(grids[0][0]) if rows else 0
    matching = [g for g in grids if len(g) == rows and (len(g[0]) if g else 0) == cols]

    if len(matching) < 2:
        return 0.0

    total = rows * cols
    if total == 0:
        return 1.0

    agree = 0
    for r in range(rows):
        for c in range(cols):
            values = {g[r][c] for g in matching}
            if len(values) == 1:
                agree += 1
    return agree / total


def pure_d4_vote(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
    test_input: Grid,
    temperature: float = 0.0,
) -> VoteResult:
    """Run clean 8-candidate D4 voting WITHOUT symbolic filtering.

    This restores V3-style voting purity. No traversals, no color perms,
    no symbolic filter — just the 8 D4 symmetry augmentations voted
    cell-wise. This avoids vote dilution from expanded candidate pools
    and over-rejection from the symbolic filter.
    """
    from loopagi.arc.transducer import transduce

    augmentations = _get_augmentations()
    candidate_grids: list[Grid] = []
    per_aug: list[dict] = []

    for i, aug in enumerate(augmentations):
        aug_pairs: list[TrainPair] = [
            (aug.forward(inp), aug.forward(out)) for inp, out in train_pairs
        ]
        aug_test = aug.forward(test_input)
        trans_result = transduce(bridge, aug_pairs, aug_test, temperature=temperature)

        if trans_result.predicted_grid is not None:
            reversed_grid = aug.reverse(trans_result.predicted_grid)
            candidate_grids.append(reversed_grid)
            per_aug.append({"name": aug.name, "valid": True})
        else:
            per_aug.append({"name": aug.name, "valid": False})
            # Early exit: if first 2 augmentations both fail, skip rest
            if i == 1 and len(candidate_grids) == 0:
                logger.info("Pure D4 vote: first 2 failed, skipping rest")
                break

    if not candidate_grids:
        return VoteResult(
            grid=None, agreement=0.0,
            n_valid=0, n_total=len(augmentations),
            method="pure_d4_vote",
            per_augmentation=per_aug,
        )

    voted_grid = _majority_vote_grid(candidate_grids)
    agreement = _compute_agreement(candidate_grids)

    logger.info(
        "Pure D4 vote: %d/%d valid, agreement=%.1f%%",
        len(candidate_grids), len(augmentations), agreement * 100,
    )

    return VoteResult(
        grid=voted_grid,
        agreement=agreement,
        n_valid=len(candidate_grids),
        n_total=len(augmentations),
        method="pure_d4_vote",
        per_augmentation=per_aug,
    )


def vote_transduction(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
    test_input: Grid,
    max_augmentations: int = 8,
    enable_traversals: bool = False,
    enable_color_perms: bool = False,
    n_color_perms: int = 5,
    temperature: float = 0.0,
) -> VoteResult:
    """Run transduction on augmented versions of the task and vote.

    Combines D4 symmetry augmentations, grid traversal representations,
    and color permutations to build a diverse candidate pool, then
    majority-votes cell-wise.

    Args:
        bridge: LLM bridge for inference.
        train_pairs: Training (input, output) pairs.
        test_input: The test input grid to predict.
        max_augmentations: Maximum D4 augmentations to try (1-8).
        enable_traversals: Also run non-row traversal encodings (Phase HH).
        enable_color_perms: Also run color permutation variants (Phase KK).
        n_color_perms: Number of color permutations to generate.
        temperature: LLM temperature for transduction calls.

    Returns:
        VoteResult with the majority-voted grid and agreement score.
    """
    from loopagi.arc.symbolic_filter import extract_priors, score_candidate
    from loopagi.arc.transducer import transduce

    _MIN_SCORE = 0.3  # Minimum symbolic score to participate in vote
    augmentations = _get_augmentations()[:max_augmentations]
    priors = extract_priors(train_pairs)
    candidate_grids: list[Grid] = []
    per_aug: list[dict] = []
    d4_failed_early = False

    for i, aug in enumerate(augmentations):
        aug_pairs: list[TrainPair] = [
            (aug.forward(inp), aug.forward(out)) for inp, out in train_pairs
        ]
        aug_test = aug.forward(test_input)
        trans_result = transduce(bridge, aug_pairs, aug_test, temperature=temperature)

        if trans_result.predicted_grid is not None:
            reversed_grid = aug.reverse(trans_result.predicted_grid)
            # Soft symbolic scoring: penalize but don't eliminate single violations
            sym_score = score_candidate(reversed_grid, test_input, priors)
            if sym_score >= _MIN_SCORE:
                candidate_grids.append(reversed_grid)
                per_aug.append({"name": aug.name, "valid": True, "score": sym_score})
            else:
                per_aug.append({"name": aug.name, "valid": False, "filtered": True,
                                "score": sym_score})
        else:
            per_aug.append({"name": aug.name, "valid": False})
            # Early exit: if first 2 augmentations both fail, skip rest
            if i == 1 and len(candidate_grids) == 0:
                logger.info("Augmentation voter: first 2 failed, skipping rest")
                d4_failed_early = True
                break

    # --- Phase HH: Grid traversal candidates ---
    if enable_traversals and not d4_failed_early:
        from loopagi.arc.grid_traversal import multi_traversal_transduce

        # Use non-row traversals (row is already covered by D4 identity)
        trav_result = multi_traversal_transduce(
            bridge, train_pairs, test_input,
            methods=("column", "snake", "diagonal"),
        )
        for info in trav_result.per_traversal:
            per_aug.append({"name": f"trav_{info['method']}", "valid": info["valid"]})

        # Add valid traversal candidates through symbolic scoring
        if trav_result.grid is not None:
            t_score = score_candidate(trav_result.grid, test_input, priors)
            if t_score >= _MIN_SCORE:
                candidate_grids.append(trav_result.grid)
                logger.info(
                    "Traversal voter added candidate (agreement=%.1f%%, score=%.2f)",
                    trav_result.agreement * 100, t_score,
                )

    # --- Phase KK: Color permutation candidates ---
    n_color_added = 0
    if enable_color_perms and not d4_failed_early:
        from loopagi.arc.color_augmentor import color_augmented_transduce

        color_candidates = color_augmented_transduce(
            bridge, train_pairs, test_input,
            n_permutations=n_color_perms,
        )
        for j, cg in enumerate(color_candidates):
            c_score = score_candidate(cg, test_input, priors)
            if c_score >= _MIN_SCORE:
                candidate_grids.append(cg)
                per_aug.append({"name": f"color_perm_{j}", "valid": True, "score": c_score})
                n_color_added += 1
            else:
                per_aug.append({"name": f"color_perm_{j}", "valid": False,
                                "filtered": True, "score": c_score})

        if n_color_added:
            logger.info("Color permutations added %d candidates", n_color_added)

    n_trav = 3 if enable_traversals and not d4_failed_early else 0
    n_cperm = n_color_perms if enable_color_perms and not d4_failed_early else 0
    total_sources = len(augmentations) + n_trav + n_cperm

    if not candidate_grids:
        logger.info("Augmentation voter: no valid predictions from %d sources", total_sources)
        return VoteResult(
            grid=None, agreement=0.0,
            n_valid=0, n_total=total_sources,
            per_augmentation=per_aug,
        )

    voted_grid = _majority_vote_grid(candidate_grids)
    agreement = _compute_agreement(candidate_grids)

    logger.info(
        "Augmentation voter: %d/%d valid, agreement=%.1f%%",
        len(candidate_grids), total_sources, agreement * 100,
    )

    return VoteResult(
        grid=voted_grid,
        agreement=agreement,
        n_valid=len(candidate_grids),
        n_total=total_sources,
        per_augmentation=per_aug,
    )


def try_augmented_transduction(
    task: object,
    bridge: LLMBridge,
    min_agreement: float = 0.80,
) -> dict | None:
    """Try augmentation-based voting on all test inputs.

    Uses a two-phase approach:
    1. Pure D4 vote (8 candidates, no filter) — restores V3 voting purity
    2. If pure D4 fails, fall through to filtered expanded pool

    Returns a solve dict compatible with solve_improved.py pipeline,
    or None if voting fails or agreement is too low.
    """
    if bridge.is_mock:
        return None

    train_pairs: list[TrainPair] = [(p.input, p.output) for p in task.train]

    # --- Phase 1: Pure D4 vote (no filter, no extras) ---
    predictions: list[Grid] = []
    for test in task.test:
        vr = pure_d4_vote(bridge, train_pairs, test.input)
        if vr.grid is None or vr.agreement < min_agreement:
            predictions = []  # Reset — need ALL test inputs to pass
            break
        predictions.append(vr.grid)

    if predictions:
        logger.info("[%s] Augmented transduction succeeded (pure D4)", task.task_id)
        from loopagi.arc.solver import SolveResult
        result = SolveResult(task_id=task.task_id)
        result.solved = True
        result.best_similarity = 1.0
        result.predictions = predictions
        result.total_seconds = 0.0
        return {
            "result": result,
            "bridge_stats": bridge.stats(),
            "complexity": "augmented_transduction",
        }

    # --- Phase 2: Filtered expanded pool (D4 + symbolic filter) ---
    predictions = []
    for test in task.test:
        vr = vote_transduction(bridge, train_pairs, test.input)
        if vr.grid is None or vr.agreement < min_agreement:
            logger.info(
                "[%s] Augmented transduction: agreement %.1f%% < %.1f%%, skipping",
                task.task_id, (vr.agreement if vr.grid else 0) * 100,
                min_agreement * 100,
            )
            return None
        predictions.append(vr.grid)

    if not predictions:
        return None

    logger.info("[%s] Augmented transduction succeeded (filtered)", task.task_id)

    from loopagi.arc.solver import SolveResult
    result = SolveResult(task_id=task.task_id)
    result.solved = True
    result.best_similarity = 1.0
    result.predictions = predictions
    result.total_seconds = 0.0

    return {
        "result": result,
        "bridge_stats": bridge.stats(),
        "complexity": "augmented_transduction",
    }
