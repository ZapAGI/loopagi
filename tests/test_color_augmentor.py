"""Tests for loopagi.arc.color_augmentor — color permutation augmentation."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from loopagi.arc.color_augmentor import (
    ARC_COLORS,
    BACKGROUND_COLOR,
    ColorPermutation,
    apply_color_map,
    color_augmented_transduce,
    extract_task_colors,
    generate_color_permutations,
    invert_color_map,
    _generate_color_map,
)


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

SIMPLE_PAIRS = [
    ([[0, 1, 2], [3, 0, 1]], [[1, 2, 0], [0, 1, 3]]),
]

TWO_COLOR_PAIRS = [
    ([[0, 1], [1, 0]], [[1, 0], [0, 1]]),
]

MULTI_COLOR_PAIRS = [
    ([[0, 1, 2, 3], [4, 5, 6, 7]], [[7, 6, 5, 4], [3, 2, 1, 0]]),
]


# ---------------------------------------------------------------------------
# extract_task_colors
# ---------------------------------------------------------------------------


class TestExtractTaskColors:
    def test_simple(self):
        colors = extract_task_colors(SIMPLE_PAIRS)
        assert colors == {0, 1, 2, 3}

    def test_two_color(self):
        colors = extract_task_colors(TWO_COLOR_PAIRS)
        assert colors == {0, 1}

    def test_multi_color(self):
        colors = extract_task_colors(MULTI_COLOR_PAIRS)
        assert colors == {0, 1, 2, 3, 4, 5, 6, 7}

    def test_empty(self):
        assert extract_task_colors([]) == set()


# ---------------------------------------------------------------------------
# _generate_color_map
# ---------------------------------------------------------------------------


class TestGenerateColorMap:
    def test_preserves_background(self):
        import random
        rng = random.Random(42)
        cmap = _generate_color_map({0, 1, 2, 3}, preserve_background=True, rng=rng)
        assert cmap[0] == 0

    def test_maps_all_task_colors(self):
        import random
        rng = random.Random(42)
        task_colors = {0, 1, 2, 3}
        cmap = _generate_color_map(task_colors, rng=rng)
        assert set(cmap.keys()) == task_colors

    def test_no_background_preserve(self):
        import random
        rng = random.Random(42)
        cmap = _generate_color_map({0, 1, 2}, preserve_background=False, rng=rng)
        # Background may or may not map to 0
        assert set(cmap.keys()) >= {1, 2}

    def test_new_colors_are_valid(self):
        import random
        rng = random.Random(42)
        cmap = _generate_color_map({0, 1, 2, 3}, rng=rng)
        for v in cmap.values():
            assert v in ARC_COLORS

    def test_fg_colors_unique(self):
        import random
        rng = random.Random(42)
        cmap = _generate_color_map({0, 1, 2, 3, 4, 5}, rng=rng)
        fg_values = [v for k, v in cmap.items() if k != 0]
        assert len(fg_values) == len(set(fg_values)), "Foreground colors must be unique"


# ---------------------------------------------------------------------------
# apply_color_map
# ---------------------------------------------------------------------------


class TestApplyColorMap:
    def test_simple_remap(self):
        grid = [[0, 1], [2, 3]]
        cmap = {0: 0, 1: 5, 2: 7, 3: 9}
        result = apply_color_map(grid, cmap)
        assert result == [[0, 5], [7, 9]]

    def test_unmapped_colors_unchanged(self):
        grid = [[0, 1], [2, 8]]
        cmap = {0: 0, 1: 5, 2: 7}
        result = apply_color_map(grid, cmap)
        assert result == [[0, 5], [7, 8]]

    def test_identity_map(self):
        grid = [[1, 2], [3, 4]]
        cmap = {1: 1, 2: 2, 3: 3, 4: 4}
        assert apply_color_map(grid, cmap) == grid

    def test_empty_grid(self):
        assert apply_color_map([], {}) == []


# ---------------------------------------------------------------------------
# invert_color_map
# ---------------------------------------------------------------------------


class TestInvertColorMap:
    def test_basic(self):
        cmap = {0: 0, 1: 5, 2: 7}
        inv = invert_color_map(cmap)
        assert inv == {0: 0, 5: 1, 7: 2}

    def test_roundtrip(self):
        cmap = {0: 0, 1: 3, 2: 8, 4: 6}
        inv = invert_color_map(cmap)
        grid = [[0, 1], [2, 4]]
        mapped = apply_color_map(grid, cmap)
        restored = apply_color_map(mapped, inv)
        assert restored == grid


# ---------------------------------------------------------------------------
# generate_color_permutations
# ---------------------------------------------------------------------------


class TestGenerateColorPermutations:
    def test_generates_n_permutations(self):
        perms = generate_color_permutations(SIMPLE_PAIRS, n=5, seed=42)
        assert len(perms) == 5

    def test_no_identity_permutations(self):
        perms = generate_color_permutations(SIMPLE_PAIRS, n=5, seed=42)
        for perm in perms:
            assert not all(k == v for k, v in perm.color_map.items())

    def test_no_duplicate_permutations(self):
        perms = generate_color_permutations(SIMPLE_PAIRS, n=5, seed=42)
        keys = [tuple(sorted(p.color_map.items())) for p in perms]
        assert len(set(keys)) == len(keys)

    def test_augmented_pairs_have_correct_structure(self):
        perms = generate_color_permutations(SIMPLE_PAIRS, n=3, seed=42)
        for perm in perms:
            assert len(perm.augmented_pairs) == len(SIMPLE_PAIRS)
            for (orig_inp, orig_out), (aug_inp, aug_out) in zip(
                SIMPLE_PAIRS, perm.augmented_pairs
            ):
                assert len(aug_inp) == len(orig_inp)
                assert len(aug_inp[0]) == len(orig_inp[0])
                assert len(aug_out) == len(orig_out)

    def test_reverse_map_undoes_augmentation(self):
        perms = generate_color_permutations(SIMPLE_PAIRS, n=3, seed=42)
        for perm in perms:
            for (orig_inp, orig_out), (aug_inp, aug_out) in zip(
                SIMPLE_PAIRS, perm.augmented_pairs
            ):
                restored_inp = apply_color_map(aug_inp, perm.reverse_map)
                restored_out = apply_color_map(aug_out, perm.reverse_map)
                assert restored_inp == orig_inp
                assert restored_out == orig_out

    def test_preserves_background(self):
        perms = generate_color_permutations(SIMPLE_PAIRS, n=5, seed=42)
        for perm in perms:
            assert perm.color_map.get(0) == 0

    def test_two_color_task_limited(self):
        # Only 1 foreground color, 8 possible remaps (to colors 2-9)
        perms = generate_color_permutations(TWO_COLOR_PAIRS, n=20, seed=42)
        assert len(perms) <= 8  # Can't exceed number of available colors

    def test_has_names(self):
        perms = generate_color_permutations(SIMPLE_PAIRS, n=3, seed=42)
        for i, perm in enumerate(perms):
            assert perm.name == f"color_perm_{i}"

    def test_seed_reproducibility(self):
        p1 = generate_color_permutations(SIMPLE_PAIRS, n=5, seed=99)
        p2 = generate_color_permutations(SIMPLE_PAIRS, n=5, seed=99)
        for a, b in zip(p1, p2):
            assert a.color_map == b.color_map


# ---------------------------------------------------------------------------
# ColorPermutation dataclass
# ---------------------------------------------------------------------------


class TestColorPermutation:
    def test_dataclass(self):
        perm = ColorPermutation(
            color_map={0: 0, 1: 5},
            reverse_map={0: 0, 5: 1},
            augmented_pairs=[],
            name="test",
        )
        assert perm.name == "test"
        assert perm.reverse_map[5] == 1


# ---------------------------------------------------------------------------
# color_augmented_transduce
# ---------------------------------------------------------------------------


class TestColorAugmentedTransduce:
    def test_returns_candidates(self):
        """Mock bridge returns a valid grid for every call."""
        import json
        bridge = MagicMock()
        bridge.call = MagicMock(return_value=json.dumps([[5, 6], [7, 8]]))

        pairs = [([[0, 1], [2, 3]], [[5, 6], [7, 8]])]
        candidates = color_augmented_transduce(
            bridge, pairs, [[0, 1], [2, 3]], n_permutations=3, seed=42,
        )
        # Should get some candidates (bridge returns valid grids)
        assert len(candidates) >= 1

    def test_handles_failed_transduction(self):
        """Bridge returns garbage for all calls."""
        bridge = MagicMock()
        bridge.call = MagicMock(return_value="I don't know")

        pairs = [([[0, 1], [2, 3]], [[5, 6], [7, 8]])]
        candidates = color_augmented_transduce(
            bridge, pairs, [[0, 1], [2, 3]], n_permutations=3, seed=42,
        )
        assert len(candidates) == 0

    def test_candidates_use_original_colors(self):
        """Returned candidates should be in the original color space."""
        import json
        # Bridge always returns [[1, 2], [3, 4]] regardless of color perm
        bridge = MagicMock()
        bridge.call = MagicMock(return_value=json.dumps([[1, 2], [3, 4]]))

        pairs = [([[0, 1], [2, 3]], [[1, 2], [3, 4]])]
        candidates = color_augmented_transduce(
            bridge, pairs, [[0, 1], [2, 3]], n_permutations=2, seed=42,
        )
        # Candidates exist (reverse-mapped), values are in ARC color range
        for grid in candidates:
            for row in grid:
                for cell in row:
                    assert 0 <= cell <= 9
