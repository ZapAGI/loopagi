"""Color permutation augmentation for ARC-AGI tasks.

Swaps colors in both input and output grids to create new training
examples that force the model to learn the *structure* of a transformation,
not specific color values. Used by NVARC, Omni-ARC, and other top solvers.

Example: if a task uses colors {1, 3, 5}, create variants with
{2, 4, 7}, {6, 8, 9}, etc. The transformation rule stays the same
but the model can't memorize specific color mappings.

Usage::

    from loopagi.arc.color_augmentor import (
        generate_color_permutations, apply_color_map,
    )
    perms = generate_color_permutations(train_pairs, n=5)
    for color_map, aug_pairs in perms:
        # aug_pairs has same structure, different colors
        ...
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.llm_bridge import LLMBridge

logger = logging.getLogger(__name__)

# Type aliases
Grid = list[list[int]]
TrainPair = tuple[Grid, Grid]

# ARC uses colors 0-9 (0 = black/background)
ARC_COLORS = list(range(10))
BACKGROUND_COLOR = 0


# ---------------------------------------------------------------------------
# Color extraction and mapping
# ---------------------------------------------------------------------------


def extract_task_colors(train_pairs: list[TrainPair]) -> set[int]:
    """Extract the set of unique colors used across all grids in a task."""
    colors: set[int] = set()
    for inp, out in train_pairs:
        for row in inp:
            colors.update(row)
        for row in out:
            colors.update(row)
    return colors


def _generate_color_map(
    task_colors: set[int],
    preserve_background: bool = True,
    rng: random.Random | None = None,
) -> dict[int, int]:
    """Generate a random color permutation map.

    Args:
        task_colors: Colors present in the task.
        preserve_background: If True, color 0 always maps to 0.
        rng: Random number generator for reproducibility.

    Returns:
        Dict mapping old color -> new color.
    """
    if rng is None:
        rng = random.Random()

    # Separate background from foreground colors
    fg_colors = sorted(c for c in task_colors if c != BACKGROUND_COLOR)
    available = [c for c in ARC_COLORS if c != BACKGROUND_COLOR]

    # Shuffle available colors and pick len(fg_colors) of them
    rng.shuffle(available)
    new_fg = available[: len(fg_colors)]

    color_map: dict[int, int] = {}
    if preserve_background and BACKGROUND_COLOR in task_colors:
        color_map[BACKGROUND_COLOR] = BACKGROUND_COLOR

    for old, new in zip(fg_colors, new_fg):
        color_map[old] = new

    return color_map


def apply_color_map(grid: Grid, color_map: dict[int, int]) -> Grid:
    """Apply a color mapping to a grid.

    Colors not in the map are left unchanged.
    """
    return [
        [color_map.get(cell, cell) for cell in row]
        for row in grid
    ]


def invert_color_map(color_map: dict[int, int]) -> dict[int, int]:
    """Invert a color map (new -> old)."""
    return {v: k for k, v in color_map.items()}


# ---------------------------------------------------------------------------
# Permutation generation
# ---------------------------------------------------------------------------


@dataclass
class ColorPermutation:
    """A color permutation with its forward and reverse mappings."""

    color_map: dict[int, int]
    reverse_map: dict[int, int]
    augmented_pairs: list[TrainPair]
    name: str = ""


def generate_color_permutations(
    train_pairs: list[TrainPair],
    n: int = 5,
    preserve_background: bool = True,
    seed: int | None = None,
) -> list[ColorPermutation]:
    """Generate n color-permuted variants of a task.

    Each permutation remaps all colors to random alternatives while
    preserving the transformation structure.

    Args:
        train_pairs: Original training (input, output) pairs.
        n: Number of permutations to generate.
        preserve_background: Keep color 0 mapped to 0.
        seed: Random seed for reproducibility.

    Returns:
        List of ColorPermutation objects with augmented pairs.
    """
    task_colors = extract_task_colors(train_pairs)
    fg_count = len(task_colors - {BACKGROUND_COLOR})

    # If task uses all 9 foreground colors, permutations are just
    # rearrangements; still useful but fewer unique options
    rng = random.Random(seed)
    seen_maps: set[tuple[tuple[int, int], ...]] = set()
    permutations: list[ColorPermutation] = []

    max_attempts = n * 5  # Avoid infinite loop on small color sets
    attempts = 0

    while len(permutations) < n and attempts < max_attempts:
        attempts += 1
        cmap = _generate_color_map(task_colors, preserve_background, rng)

        # Skip duplicates
        key = tuple(sorted(cmap.items()))
        if key in seen_maps:
            continue

        # Skip identity mapping
        if all(k == v for k, v in cmap.items()):
            continue

        seen_maps.add(key)

        aug_pairs: list[TrainPair] = [
            (apply_color_map(inp, cmap), apply_color_map(out, cmap))
            for inp, out in train_pairs
        ]

        permutations.append(ColorPermutation(
            color_map=cmap,
            reverse_map=invert_color_map(cmap),
            augmented_pairs=aug_pairs,
            name=f"color_perm_{len(permutations)}",
        ))

    logger.debug(
        "Generated %d color permutations from %d fg colors (%d attempts)",
        len(permutations), fg_count, attempts,
    )
    return permutations


# ---------------------------------------------------------------------------
# Color-augmented transduction voting
# ---------------------------------------------------------------------------


def color_augmented_transduce(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
    test_input: Grid,
    n_permutations: int = 5,
    seed: int | None = None,
) -> list[Grid]:
    """Run transduction on color-permuted variants and collect candidates.

    For each color permutation:
    1. Remap all grids to new colors
    2. Run transduction
    3. Reverse the color mapping on the prediction

    Returns a list of candidate grids (already un-permuted) that can
    be added to a voting pool.

    Args:
        bridge: LLM bridge for inference.
        train_pairs: Original training pairs.
        test_input: Original test input.
        n_permutations: Number of color permutations to try.
        seed: Random seed for reproducibility.

    Returns:
        List of valid candidate grids (reverse-mapped to original colors).
    """
    from loopagi.arc.transducer import transduce

    permutations = generate_color_permutations(
        train_pairs, n=n_permutations, seed=seed,
    )
    candidates: list[Grid] = []

    for perm in permutations:
        aug_test = apply_color_map(test_input, perm.color_map)
        result = transduce(bridge, perm.augmented_pairs, aug_test, temperature=0.0)

        if result.predicted_grid is not None:
            # Reverse color mapping to get prediction in original colors
            original_pred = apply_color_map(result.predicted_grid, perm.reverse_map)
            candidates.append(original_pred)
            logger.debug("Color perm %s: valid prediction", perm.name)
        else:
            logger.debug("Color perm %s: failed to parse", perm.name)

    logger.info(
        "Color augmentation: %d/%d valid candidates",
        len(candidates), len(permutations),
    )
    return candidates
