"""Symbolic filtering for ARC candidate outputs.

Rejects invalid candidate grids based on white-box priors extracted from
training pairs. NVARC's ablation shows filtering is worth +14 percentage
points — it eliminates garbage predictions before scoring.

Three filters:
1. Color consistency: output must only use colors present in the task
2. Grid size consistency: output must match the size pattern from training
3. Inclusion: if output ⊂ input in training, same must hold for test

Usage:
    from loopagi.arc.symbolic_filter import filter_candidate, extract_priors
    priors = extract_priors(train_pairs)
    is_valid = filter_candidate(predicted_grid, test_input, priors)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Type aliases
Grid = list[list[int]]
TrainPair = tuple[Grid, Grid]


# ---------------------------------------------------------------------------
# Priors extraction
# ---------------------------------------------------------------------------


@dataclass
class TaskPriors:
    """Symbolic priors extracted from training pairs."""

    all_colors: set[int] = field(default_factory=set)
    """Union of all colors appearing in any training grid."""

    output_fixed_size: tuple[int, int] | None = None
    """If all outputs share the same (rows, cols), store it."""

    output_scale: tuple[float, float] | None = None
    """If outputs scale uniformly from inputs, store (row_ratio, col_ratio)."""

    output_subset_of_input: bool = False
    """True if every output grid's cells are a subset of its input's cells."""

    input_subset_of_output: bool = False
    """True if every input grid's cells are a subset of its output's cells."""


def _grid_colors(grid: Grid) -> set[int]:
    """Extract the set of unique color values from a grid."""
    colors: set[int] = set()
    for row in grid:
        colors.update(row)
    return colors


def _grid_size(grid: Grid) -> tuple[int, int]:
    """Return (rows, cols) of a grid."""
    if not grid:
        return (0, 0)
    return (len(grid), len(grid[0]))


def _is_subset_grid(subset: Grid, superset: Grid) -> bool:
    """Check if every non-zero cell in subset appears in superset at same position."""
    if _grid_size(subset) != _grid_size(superset):
        return False
    for r in range(len(subset)):
        for c in range(len(subset[0])):
            if subset[r][c] != 0 and subset[r][c] != superset[r][c]:
                return False
    return True


def extract_priors(train_pairs: list[TrainPair]) -> TaskPriors:
    """Extract symbolic priors from training pairs.

    Args:
        train_pairs: List of (input_grid, output_grid) tuples.

    Returns:
        TaskPriors with all extracted constraints.
    """
    priors = TaskPriors()

    if not train_pairs:
        return priors

    # Color consistency: union of all colors in the task
    for inp, out in train_pairs:
        priors.all_colors.update(_grid_colors(inp))
        priors.all_colors.update(_grid_colors(out))

    # Grid size consistency
    output_sizes = [_grid_size(out) for _, out in train_pairs]
    if len(set(output_sizes)) == 1:
        priors.output_fixed_size = output_sizes[0]
    else:
        # Check for uniform scaling
        ratios: list[tuple[float, float]] = []
        for inp, out in train_pairs:
            inp_r, inp_c = _grid_size(inp)
            out_r, out_c = _grid_size(out)
            if inp_r > 0 and inp_c > 0:
                ratios.append((out_r / inp_r, out_c / inp_c))
        if ratios and len(set(ratios)) == 1:
            priors.output_scale = ratios[0]

    # Inclusion priors
    all_out_subset = all(
        _is_subset_grid(out, inp) for inp, out in train_pairs
        if _grid_size(inp) == _grid_size(out)
    )
    all_inp_subset = all(
        _is_subset_grid(inp, out) for inp, out in train_pairs
        if _grid_size(inp) == _grid_size(out)
    )
    # Only set if sizes match (inclusion doesn't apply when sizes differ)
    same_sizes = all(_grid_size(inp) == _grid_size(out) for inp, out in train_pairs)
    if same_sizes and train_pairs:
        priors.output_subset_of_input = all_out_subset
        priors.input_subset_of_output = all_inp_subset

    return priors


# ---------------------------------------------------------------------------
# Individual filters
# ---------------------------------------------------------------------------


def filter_by_colors(predicted: Grid, priors: TaskPriors) -> bool:
    """Check if predicted grid uses only colors present in the task.

    Returns True if valid, False if should be rejected.
    """
    if not priors.all_colors:
        return True
    pred_colors = _grid_colors(predicted)
    invalid = pred_colors - priors.all_colors
    if invalid:
        logger.debug("Color filter: predicted has colors %s not in task", invalid)
        return False
    return True


def filter_by_size(
    predicted: Grid,
    test_input: Grid,
    priors: TaskPriors,
) -> bool:
    """Check if predicted grid matches the size pattern from training.

    Returns True if valid, False if should be rejected.
    """
    pred_size = _grid_size(predicted)

    if priors.output_fixed_size is not None:
        if pred_size != priors.output_fixed_size:
            logger.debug("Size filter: predicted %s != expected %s",
                         pred_size, priors.output_fixed_size)
            return False

    if priors.output_scale is not None:
        inp_r, inp_c = _grid_size(test_input)
        expected_r = int(inp_r * priors.output_scale[0])
        expected_c = int(inp_c * priors.output_scale[1])
        if pred_size != (expected_r, expected_c):
            logger.debug("Size filter: predicted %s != scaled (%d,%d)",
                         pred_size, expected_r, expected_c)
            return False

    return True


def filter_by_inclusion(
    predicted: Grid,
    test_input: Grid,
    priors: TaskPriors,
) -> bool:
    """Check if predicted grid respects inclusion relationships.

    Returns True if valid, False if should be rejected.
    """
    if _grid_size(predicted) != _grid_size(test_input):
        return True  # Inclusion only applies when sizes match

    if priors.output_subset_of_input:
        if not _is_subset_grid(predicted, test_input):
            logger.debug("Inclusion filter: output not subset of input")
            return False

    if priors.input_subset_of_output:
        if not _is_subset_grid(test_input, predicted):
            logger.debug("Inclusion filter: input not subset of output")
            return False

    return True


# ---------------------------------------------------------------------------
# Combined filter
# ---------------------------------------------------------------------------


def filter_candidate(
    predicted: Grid,
    test_input: Grid,
    priors: TaskPriors,
) -> bool:
    """Apply all symbolic filters to a candidate output.

    Returns True if the candidate passes all filters (valid),
    False if it should be rejected.
    """
    if not predicted:
        return False

    if not filter_by_colors(predicted, priors):
        return False

    if not filter_by_size(predicted, test_input, priors):
        return False

    if not filter_by_inclusion(predicted, test_input, priors):
        return False

    return True


def score_candidate(
    predicted: Grid,
    test_input: Grid,
    priors: TaskPriors,
) -> float:
    """Score a candidate 0.0-1.0 based on structural priors.

    Unlike filter_candidate() which is binary, this returns a soft score.
    Candidates violating a single prior are penalized but not eliminated,
    preventing over-rejection in D4 voting pools.

    Returns:
        1.0 if all priors satisfied, reduced for each violation.
        0.0 if grid is empty or has critical violations.
    """
    if not predicted:
        return 0.0
    score = 1.0
    if not filter_by_colors(predicted, priors):
        score -= 0.3
    if not filter_by_size(predicted, test_input, priors):
        score -= 0.4
    if not filter_by_inclusion(predicted, test_input, priors):
        score -= 0.2
    return max(0.0, score)
