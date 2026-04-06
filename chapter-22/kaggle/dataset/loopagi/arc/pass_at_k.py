"""Pass-at-K diversified candidate generation for ARC transduction.

Instead of relying on a single D4 voting attempt, this module generates
K candidate outputs using multiple strategies (temperature sweep, prompt
variants, traversal encodings) and votes across all of them. This directly
addresses the LLM non-determinism that causes D4 voting to be unreliable.

Based on findings from ARC Prize 2025:
- NVARC uses K=128 candidates
- Berman uses 40 attempts per task
- Pang uses 10 per task (most efficient)

We target K=24-32 candidates per test input using 4 strategy families.

Usage:
    from loopagi.arc.pass_at_k import multi_strategy_vote
    result = multi_strategy_vote(bridge, train_pairs, test_input)
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.llm_bridge import LLMBridge

logger = logging.getLogger(__name__)

# Type aliases
Grid = list[list[int]]
TrainPair = tuple[Grid, Grid]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class CandidateInfo:
    """Metadata about a single candidate prediction."""

    grid: Grid
    strategy: str
    temperature: float = 0.0
    filtered: bool = False


@dataclass
class MultiVoteResult:
    """Result of multi-strategy voting."""

    grid: Grid | None
    agreement: float
    n_candidates: int
    n_valid: int
    strategy_breakdown: dict = field(default_factory=dict)
    method: str = "multi_strategy_vote"


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


def _generate_d4_candidates(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
    test_input: Grid,
    temperature: float = 0.0,
) -> list[CandidateInfo]:
    """Generate candidates using D4 symmetry augmentations."""
    from loopagi.arc.augmentation_voter import _get_augmentations
    from loopagi.arc.transducer import transduce

    augmentations = _get_augmentations()
    candidates: list[CandidateInfo] = []

    for aug in augmentations:
        aug_pairs: list[TrainPair] = [
            (aug.forward(inp), aug.forward(out)) for inp, out in train_pairs
        ]
        aug_test = aug.forward(test_input)
        result = transduce(bridge, aug_pairs, aug_test, temperature=temperature)
        if result.predicted_grid is not None:
            reversed_grid = aug.reverse(result.predicted_grid)
            candidates.append(CandidateInfo(
                grid=reversed_grid,
                strategy=f"d4_{aug.name}",
                temperature=temperature,
            ))

    return candidates


def _generate_temperature_candidates(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
    test_input: Grid,
    temperatures: tuple[float, ...] = (0.1, 0.2, 0.3, 0.5, 0.7),
) -> list[CandidateInfo]:
    """Generate candidates at varied temperatures (identity augmentation only)."""
    from loopagi.arc.transducer import transduce

    candidates: list[CandidateInfo] = []
    for temp in temperatures:
        result = transduce(bridge, train_pairs, test_input, temperature=temp)
        if result.predicted_grid is not None:
            candidates.append(CandidateInfo(
                grid=result.predicted_grid,
                strategy=f"temp_{temp}",
                temperature=temp,
            ))
    return candidates


def _generate_d4_temp_candidates(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
    test_input: Grid,
    temperature: float = 0.3,
) -> list[CandidateInfo]:
    """Generate D4 candidates at a non-zero temperature for diversity."""
    return _generate_d4_candidates(bridge, train_pairs, test_input, temperature=temperature)


# ---------------------------------------------------------------------------
# Voting
# ---------------------------------------------------------------------------


def _majority_vote(grids: list[Grid]) -> Grid | None:
    """Cell-wise majority vote across multiple grids.

    Filters to grids matching the most common shape, then votes per cell.
    """
    if not grids:
        return None

    shape_counts: Counter = Counter()
    for g in grids:
        r = len(g)
        c = len(g[0]) if r > 0 else 0
        shape_counts[(r, c)] += 1

    target_shape = shape_counts.most_common(1)[0][0]
    matching = [
        g for g in grids
        if (len(g), len(g[0]) if g else 0) == target_shape
    ]
    if not matching:
        return None

    rows, cols = target_shape
    result: Grid = []
    for r in range(rows):
        row: list[int] = []
        for c in range(cols):
            votes = Counter(g[r][c] for g in matching)
            row.append(votes.most_common(1)[0][0])
        result.append(row)
    return result


def _compute_agreement(grids: list[Grid]) -> float:
    """Fraction of cells where all grids agree."""
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

    agree = sum(
        1 for r in range(rows) for c in range(cols)
        if len({g[r][c] for g in matching}) == 1
    )
    return agree / total


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------


def multi_strategy_vote(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
    test_input: Grid,
    enable_temp_sweep: bool = True,
    enable_d4_retry: bool = True,
    d4_retry_temp: float = 0.3,
    temp_schedule: tuple[float, ...] = (0.1, 0.2, 0.3, 0.5),
) -> MultiVoteResult:
    """Generate candidates via multiple strategies and vote.

    Strategy 1: D4 at temp=0.0 (8 candidates) — standard
    Strategy 2: Temperature sweep at identity (4-5 candidates)
    Strategy 3: D4 at temp=0.3 (8 candidates) — diversity retry

    Total: ~20-21 candidates per test input.

    Args:
        bridge: LLM bridge for inference.
        train_pairs: Training (input, output) pairs.
        test_input: The test input grid to predict.
        enable_temp_sweep: Include temperature-varied candidates.
        enable_d4_retry: Include D4 at non-zero temperature.
        d4_retry_temp: Temperature for D4 retry.
        temp_schedule: Temperatures for sweep strategy.

    Returns:
        MultiVoteResult with voted grid and agreement score.
    """
    from loopagi.arc.symbolic_filter import extract_priors, score_candidate

    _MIN_SCORE = 0.3
    priors = extract_priors(train_pairs)
    all_candidates: list[CandidateInfo] = []
    strategy_counts: dict[str, int] = {}

    # Strategy 1: Standard D4 at temp=0.0
    d4_cands = _generate_d4_candidates(bridge, train_pairs, test_input, temperature=0.0)
    all_candidates.extend(d4_cands)
    strategy_counts["d4_t0"] = len(d4_cands)

    # Early exit: if D4 produces no candidates, transduction isn't viable
    if len(d4_cands) < 2:
        logger.info("Pass-at-K: D4 produced only %d candidates, skipping extra strategies",
                     len(d4_cands))
        return MultiVoteResult(
            grid=None, agreement=0.0,
            n_candidates=len(d4_cands), n_valid=0,
            strategy_breakdown=strategy_counts,
        )

    # Strategy 2: Temperature sweep (identity augmentation)
    if enable_temp_sweep:
        temp_cands = _generate_temperature_candidates(
            bridge, train_pairs, test_input, temperatures=temp_schedule,
        )
        all_candidates.extend(temp_cands)
        strategy_counts["temp_sweep"] = len(temp_cands)

    # Strategy 3: D4 retry at non-zero temperature
    if enable_d4_retry:
        d4_retry_cands = _generate_d4_temp_candidates(
            bridge, train_pairs, test_input, temperature=d4_retry_temp,
        )
        all_candidates.extend(d4_retry_cands)
        strategy_counts["d4_retry"] = len(d4_retry_cands)

    # Apply symbolic scoring to all candidates (soft filter)
    valid_grids: list[Grid] = []
    for cand in all_candidates:
        sym_score = score_candidate(cand.grid, test_input, priors)
        if sym_score >= _MIN_SCORE:
            valid_grids.append(cand.grid)
        else:
            cand.filtered = True

    n_filtered = len(all_candidates) - len(valid_grids)
    strategy_counts["filtered"] = n_filtered

    logger.info(
        "Pass-at-K: %d candidates (%d valid, %d filtered) from strategies: %s",
        len(all_candidates), len(valid_grids), n_filtered,
        {k: v for k, v in strategy_counts.items() if k != "filtered"},
    )

    if not valid_grids:
        return MultiVoteResult(
            grid=None, agreement=0.0,
            n_candidates=len(all_candidates), n_valid=0,
            strategy_breakdown=strategy_counts,
        )

    voted_grid = _majority_vote(valid_grids)
    agreement = _compute_agreement(valid_grids)

    logger.info(
        "Pass-at-K: voted grid from %d valid candidates, agreement=%.1f%%",
        len(valid_grids), agreement * 100,
    )

    return MultiVoteResult(
        grid=voted_grid,
        agreement=agreement,
        n_candidates=len(all_candidates),
        n_valid=len(valid_grids),
        strategy_breakdown=strategy_counts,
    )


def try_multi_strategy_transduction(
    task: object,
    bridge: LLMBridge,
    min_agreement: float = 0.70,
) -> dict | None:
    """Try multi-strategy voting on all test inputs.

    This is the pipeline-compatible wrapper. Uses a lower agreement
    threshold (0.70) than standard D4 voting (0.80) because we have
    more candidates providing stronger consensus.

    Args:
        task: ARC task with .train and .test attributes.
        bridge: LLM bridge for inference.
        min_agreement: Minimum agreement fraction to accept.

    Returns:
        Solve dict compatible with solve_improved.py, or None.
    """
    if bridge.is_mock:
        return None

    train_pairs: list[TrainPair] = [(p.input, p.output) for p in task.train]
    predictions: list[Grid] = []

    for test in task.test:
        vr = multi_strategy_vote(bridge, train_pairs, test.input)
        if vr.grid is None or vr.agreement < min_agreement:
            logger.info(
                "[%s] Multi-strategy vote: agreement %.1f%% < %.1f%%, skipping",
                task.task_id, (vr.agreement if vr.grid else 0) * 100,
                min_agreement * 100,
            )
            return None
        predictions.append(vr.grid)

    if not predictions:
        return None

    logger.info("[%s] Multi-strategy transduction succeeded", task.task_id)

    from loopagi.arc.solver import SolveResult
    result = SolveResult(task_id=task.task_id)
    result.solved = True
    result.best_similarity = 1.0
    result.predictions = predictions
    result.total_seconds = 0.0

    return {
        "result": result,
        "bridge_stats": bridge.stats(),
        "complexity": "multi_strategy_transduction",
    }
