"""Tests for loopagi.arc.symbolic_filter — symbolic candidate filtering."""

from __future__ import annotations

import pytest

from loopagi.arc.symbolic_filter import (
    TaskPriors,
    _grid_colors,
    _grid_size,
    _is_subset_grid,
    extract_priors,
    filter_by_colors,
    filter_by_inclusion,
    filter_by_size,
    filter_candidate,
)


# ---------------------------------------------------------------------------
# _grid_colors
# ---------------------------------------------------------------------------


class TestGridColors:
    def test_simple(self):
        assert _grid_colors([[1, 2], [3, 4]]) == {1, 2, 3, 4}

    def test_with_zeros(self):
        assert _grid_colors([[0, 1], [0, 0]]) == {0, 1}

    def test_empty(self):
        assert _grid_colors([]) == set()

    def test_single_color(self):
        assert _grid_colors([[5, 5], [5, 5]]) == {5}


# ---------------------------------------------------------------------------
# _grid_size
# ---------------------------------------------------------------------------


class TestGridSize:
    def test_normal(self):
        assert _grid_size([[1, 2], [3, 4]]) == (2, 2)

    def test_rectangular(self):
        assert _grid_size([[1, 2, 3]]) == (1, 3)

    def test_empty(self):
        assert _grid_size([]) == (0, 0)


# ---------------------------------------------------------------------------
# _is_subset_grid
# ---------------------------------------------------------------------------


class TestIsSubsetGrid:
    def test_identical(self):
        g = [[1, 2], [3, 4]]
        assert _is_subset_grid(g, g)

    def test_subset_with_zeros(self):
        subset = [[0, 2], [0, 0]]
        superset = [[1, 2], [3, 4]]
        assert _is_subset_grid(subset, superset)

    def test_not_subset(self):
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        assert not _is_subset_grid(a, b)

    def test_different_sizes(self):
        assert not _is_subset_grid([[1]], [[1, 2]])


# ---------------------------------------------------------------------------
# extract_priors
# ---------------------------------------------------------------------------


class TestExtractPriors:
    def test_color_union(self):
        pairs = [([[1, 2]], [[3, 4]]), ([[5]], [[6]])]
        priors = extract_priors(pairs)
        assert priors.all_colors == {1, 2, 3, 4, 5, 6}

    def test_fixed_output_size(self):
        pairs = [([[1]], [[1, 2]]), ([[3]], [[4, 5]])]
        priors = extract_priors(pairs)
        assert priors.output_fixed_size == (1, 2)

    def test_no_fixed_size(self):
        pairs = [([[1]], [[1, 2]]), ([[3]], [[4, 5], [6, 7]])]
        priors = extract_priors(pairs)
        assert priors.output_fixed_size is None

    def test_uniform_scale(self):
        pairs = [
            ([[1, 2]], [[1, 2, 3, 4]]),  # 1x2 -> 1x4 (2x width)
            ([[1]], [[1, 2]]),             # 1x1 -> 1x2 (2x width)
        ]
        priors = extract_priors(pairs)
        assert priors.output_scale == (1.0, 2.0)

    def test_output_subset_of_input(self):
        pairs = [
            ([[1, 2], [3, 4]], [[0, 2], [0, 4]]),  # removed col 0 values
        ]
        priors = extract_priors(pairs)
        assert priors.output_subset_of_input

    def test_empty_pairs(self):
        priors = extract_priors([])
        assert priors.all_colors == set()
        assert priors.output_fixed_size is None


# ---------------------------------------------------------------------------
# filter_by_colors
# ---------------------------------------------------------------------------


class TestFilterByColors:
    def test_valid_colors(self):
        priors = TaskPriors(all_colors={0, 1, 2, 3})
        assert filter_by_colors([[1, 2], [3, 0]], priors)

    def test_invalid_color(self):
        priors = TaskPriors(all_colors={0, 1, 2})
        assert not filter_by_colors([[1, 9]], priors)

    def test_empty_priors(self):
        priors = TaskPriors()
        assert filter_by_colors([[5, 6]], priors)


# ---------------------------------------------------------------------------
# filter_by_size
# ---------------------------------------------------------------------------


class TestFilterBySize:
    def test_fixed_size_match(self):
        priors = TaskPriors(output_fixed_size=(2, 3))
        assert filter_by_size([[1, 2, 3], [4, 5, 6]], [[0]], priors)

    def test_fixed_size_mismatch(self):
        priors = TaskPriors(output_fixed_size=(2, 3))
        assert not filter_by_size([[1, 2]], [[0]], priors)

    def test_scale_match(self):
        priors = TaskPriors(output_scale=(2.0, 2.0))
        inp = [[1, 2], [3, 4]]  # 2x2
        pred = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]  # 4x4
        assert filter_by_size(pred, inp, priors)

    def test_scale_mismatch(self):
        priors = TaskPriors(output_scale=(2.0, 2.0))
        inp = [[1, 2], [3, 4]]  # 2x2
        pred = [[1, 2, 3], [4, 5, 6]]  # 2x3 (wrong)
        assert not filter_by_size(pred, inp, priors)

    def test_no_size_constraint(self):
        priors = TaskPriors()
        assert filter_by_size([[1]], [[2]], priors)


# ---------------------------------------------------------------------------
# filter_by_inclusion
# ---------------------------------------------------------------------------


class TestFilterByInclusion:
    def test_output_subset_valid(self):
        priors = TaskPriors(output_subset_of_input=True)
        inp = [[1, 2], [3, 4]]
        pred = [[0, 2], [0, 4]]
        assert filter_by_inclusion(pred, inp, priors)

    def test_output_subset_invalid(self):
        priors = TaskPriors(output_subset_of_input=True)
        inp = [[1, 2], [3, 4]]
        pred = [[9, 2], [3, 4]]  # 9 not in input
        assert not filter_by_inclusion(pred, inp, priors)

    def test_different_sizes_skip(self):
        priors = TaskPriors(output_subset_of_input=True)
        assert filter_by_inclusion([[1, 2, 3]], [[1]], priors)

    def test_no_inclusion_constraint(self):
        priors = TaskPriors()
        assert filter_by_inclusion([[9]], [[1]], priors)


# ---------------------------------------------------------------------------
# filter_candidate (combined)
# ---------------------------------------------------------------------------


class TestFilterCandidate:
    def test_valid_candidate(self):
        priors = TaskPriors(all_colors={0, 1, 2}, output_fixed_size=(2, 2))
        assert filter_candidate([[1, 2], [0, 1]], [[0, 0], [0, 0]], priors)

    def test_empty_rejected(self):
        priors = TaskPriors()
        assert not filter_candidate([], [[1]], priors)

    def test_color_rejection(self):
        priors = TaskPriors(all_colors={0, 1})
        assert not filter_candidate([[9]], [[0]], priors)

    def test_size_rejection(self):
        priors = TaskPriors(output_fixed_size=(3, 3))
        assert not filter_candidate([[1]], [[0]], priors)

    def test_all_pass(self):
        priors = TaskPriors(all_colors={0, 1, 2, 3, 4})
        assert filter_candidate([[1, 2], [3, 4]], [[0, 0], [0, 0]], priors)
