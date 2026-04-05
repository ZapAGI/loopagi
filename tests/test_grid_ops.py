"""Tests for loopagi.arc.grid_ops module."""

from __future__ import annotations

import pytest

from loopagi.arc.grid_ops import (
    apply_mask,
    background_color,
    color_positions,
    count_by_color,
    crop,
    deep_copy,
    diff_mask,
    extract_subgrid,
    flood_fill,
    grid_shape,
    grids_equal,
    is_rotationally_symmetric,
    is_symmetric_diagonal,
    is_symmetric_horizontal,
    is_symmetric_vertical,
    make_grid,
    mask_by_color,
    most_common_color,
    overlay,
    pad,
    recolor,
    reflect_anti_diagonal,
    reflect_diagonal,
    reflect_horizontal,
    reflect_vertical,
    replace_color,
    rotate_180,
    rotate_ccw,
    rotate_cw,
    scale_up,
    swap_colors,
    symmetry_report,
    tile,
    translate,
    unique_colors,
)


# --- Grid Construction ---


class TestGridConstruction:
    def test_make_grid(self) -> None:
        g = make_grid(2, 3, fill=5)
        assert g == [[5, 5, 5], [5, 5, 5]]

    def test_make_grid_default_fill(self) -> None:
        g = make_grid(1, 1)
        assert g == [[0]]

    def test_grid_shape(self) -> None:
        assert grid_shape([[1, 2], [3, 4]]) == (2, 2)

    def test_grid_shape_empty(self) -> None:
        assert grid_shape([]) == (0, 0)

    def test_deep_copy_independence(self) -> None:
        g = [[1, 2], [3, 4]]
        c = deep_copy(g)
        c[0][0] = 9
        assert g[0][0] == 1


# --- Geometric Transforms ---


class TestRotation:
    def test_rotate_cw(self) -> None:
        g = [[1, 2], [3, 4]]
        assert rotate_cw(g) == [[3, 1], [4, 2]]

    def test_rotate_ccw(self) -> None:
        g = [[1, 2], [3, 4]]
        assert rotate_ccw(g) == [[2, 4], [1, 3]]

    def test_rotate_180(self) -> None:
        g = [[1, 2], [3, 4]]
        assert rotate_180(g) == [[4, 3], [2, 1]]

    def test_rotate_cw_4_times_identity(self) -> None:
        g = [[1, 2, 3], [4, 5, 6]]
        result = g
        for _ in range(4):
            result = rotate_cw(result)
        assert result == g

    def test_rotate_empty(self) -> None:
        assert rotate_cw([]) == []
        assert rotate_ccw([]) == []
        assert rotate_180([]) == []

    def test_rotate_1x1(self) -> None:
        assert rotate_cw([[5]]) == [[5]]

    def test_rotate_non_square(self) -> None:
        g = [[1, 2, 3]]  # 1x3
        r = rotate_cw(g)
        assert grid_shape(r) == (3, 1)
        assert r == [[1], [2], [3]]


class TestReflection:
    def test_reflect_horizontal(self) -> None:
        g = [[1, 2], [3, 4]]
        assert reflect_horizontal(g) == [[3, 4], [1, 2]]

    def test_reflect_vertical(self) -> None:
        g = [[1, 2], [3, 4]]
        assert reflect_vertical(g) == [[2, 1], [4, 3]]

    def test_reflect_diagonal(self) -> None:
        g = [[1, 2], [3, 4]]
        assert reflect_diagonal(g) == [[1, 3], [2, 4]]

    def test_reflect_anti_diagonal(self) -> None:
        g = [[1, 2], [3, 4]]
        assert reflect_anti_diagonal(g) == [[4, 2], [3, 1]]

    def test_double_reflect_identity(self) -> None:
        g = [[1, 2, 3], [4, 5, 6]]
        assert reflect_horizontal(reflect_horizontal(g)) == g
        assert reflect_vertical(reflect_vertical(g)) == g

    def test_reflect_empty(self) -> None:
        assert reflect_diagonal([]) == []
        assert reflect_anti_diagonal([]) == []


class TestTranslate:
    def test_translate_right(self) -> None:
        g = [[1, 0], [0, 0]]
        assert translate(g, 0, 1) == [[0, 1], [0, 0]]

    def test_translate_down(self) -> None:
        g = [[1, 0], [0, 0]]
        assert translate(g, 1, 0) == [[0, 0], [1, 0]]

    def test_translate_out_of_bounds(self) -> None:
        g = [[1, 2], [3, 4]]
        r = translate(g, 2, 0)
        assert r == [[0, 0], [0, 0]]

    def test_translate_with_fill(self) -> None:
        g = [[1]]
        r = translate(g, 0, 0, fill=9)
        assert r == [[1]]


class TestScaleCropPadTile:
    def test_scale_up_2x(self) -> None:
        g = [[1, 2], [3, 4]]
        expected = [[1, 1, 2, 2], [1, 1, 2, 2], [3, 3, 4, 4], [3, 3, 4, 4]]
        assert scale_up(g, 2) == expected

    def test_scale_up_1x(self) -> None:
        g = [[1, 2]]
        assert scale_up(g, 1) == g

    def test_scale_up_invalid(self) -> None:
        with pytest.raises(ValueError):
            scale_up([[1]], 0)

    def test_crop(self) -> None:
        g = [[0, 0, 0], [0, 1, 2], [0, 3, 4]]
        assert crop(g, (1, 1, 2, 2)) == [[1, 2], [3, 4]]

    def test_pad(self) -> None:
        g = [[1]]
        r = pad(g, top=1, bottom=1, left=1, right=1, fill=0)
        assert r == [[0, 0, 0], [0, 1, 0], [0, 0, 0]]

    def test_tile(self) -> None:
        g = [[1, 2]]
        r = tile(g, 2, 2)
        assert r == [[1, 2, 1, 2], [1, 2, 1, 2]]

    def test_tile_single(self) -> None:
        g = [[5]]
        assert tile(g, 3, 3) == [[5, 5, 5], [5, 5, 5], [5, 5, 5]]


# --- Color Operations ---


class TestColorOps:
    def test_recolor(self) -> None:
        g = [[0, 1], [2, 3]]
        assert recolor(g, {1: 9, 2: 8}) == [[0, 9], [8, 3]]

    def test_swap_colors(self) -> None:
        g = [[1, 2], [2, 1]]
        assert swap_colors(g, 1, 2) == [[2, 1], [1, 2]]

    def test_replace_color(self) -> None:
        g = [[0, 1, 0], [1, 0, 1]]
        assert replace_color(g, 0, 5) == [[5, 1, 5], [1, 5, 1]]

    def test_flood_fill(self) -> None:
        g = [[0, 0, 1], [0, 0, 1], [1, 1, 1]]
        r = flood_fill(g, 0, 0, 5)
        assert r == [[5, 5, 1], [5, 5, 1], [1, 1, 1]]

    def test_flood_fill_same_color(self) -> None:
        g = [[1, 1], [1, 1]]
        assert flood_fill(g, 0, 0, 1) == g

    def test_flood_fill_out_of_bounds(self) -> None:
        g = [[1]]
        assert flood_fill(g, -1, 0, 5) == [[1]]

    def test_flood_fill_no_mutation(self) -> None:
        g = [[0, 1], [1, 0]]
        r = flood_fill(g, 0, 0, 9)
        assert g == [[0, 1], [1, 0]]


# --- Pattern Operations ---


class TestPatternOps:
    def test_overlay(self) -> None:
        base = [[1, 1], [1, 1]]
        top = [[0, 2], [3, 0]]
        assert overlay(base, top, transparent=0) == [[1, 2], [3, 1]]

    def test_mask_by_color(self) -> None:
        g = [[0, 1, 0], [1, 1, 0]]
        assert mask_by_color(g, 1) == [[0, 1, 0], [1, 1, 0]]

    def test_apply_mask(self) -> None:
        g = [[5, 6], [7, 8]]
        m = [[1, 0], [0, 1]]
        assert apply_mask(g, m) == [[5, 0], [0, 8]]

    def test_extract_subgrid(self) -> None:
        g = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        assert extract_subgrid(g, 1, 1, 2, 2) == [[5, 6], [8, 9]]


# --- Analysis ---


class TestAnalysis:
    def test_unique_colors(self) -> None:
        g = [[0, 1], [2, 0]]
        assert unique_colors(g) == {0, 1, 2}

    def test_count_by_color(self) -> None:
        g = [[0, 1, 1], [0, 0, 2]]
        counts = count_by_color(g)
        assert counts == {0: 3, 1: 2, 2: 1}

    def test_most_common_color(self) -> None:
        g = [[0, 0, 1], [0, 1, 1]]
        assert most_common_color(g) == 0

    def test_most_common_color_exclude(self) -> None:
        g = [[0, 0, 1], [0, 1, 1]]
        assert most_common_color(g, exclude={0}) == 1

    def test_background_color(self) -> None:
        g = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
        assert background_color(g) == 0

    def test_color_positions(self) -> None:
        g = [[0, 1], [1, 0]]
        assert color_positions(g, 1) == [(0, 1), (1, 0)]


# --- Symmetry ---


class TestSymmetry:
    def test_horizontal_symmetric(self) -> None:
        g = [[1, 2], [1, 2]]
        assert is_symmetric_horizontal(g) is True

    def test_horizontal_asymmetric(self) -> None:
        g = [[1, 2], [3, 4]]
        assert is_symmetric_horizontal(g) is False

    def test_vertical_symmetric(self) -> None:
        g = [[1, 1], [2, 2]]
        assert is_symmetric_vertical(g) is True

    def test_diagonal_symmetric(self) -> None:
        g = [[1, 2], [2, 1]]
        assert is_symmetric_diagonal(g) is True

    def test_diagonal_non_square(self) -> None:
        g = [[1, 2, 3]]
        assert is_symmetric_diagonal(g) is False

    def test_rotational_symmetric(self) -> None:
        g = [[1, 2], [2, 1]]
        assert is_rotationally_symmetric(g) is True

    def test_symmetry_report(self) -> None:
        g = [[1, 1], [1, 1]]
        report = symmetry_report(g)
        assert report["horizontal"] is True
        assert report["vertical"] is True


# --- Grid Comparison ---


class TestGridComparison:
    def test_grids_equal(self) -> None:
        assert grids_equal([[1, 2]], [[1, 2]]) is True

    def test_grids_not_equal(self) -> None:
        assert grids_equal([[1]], [[2]]) is False

    def test_grids_different_shape(self) -> None:
        assert grids_equal([[1]], [[1, 2]]) is False

    def test_diff_mask(self) -> None:
        a = [[1, 2], [3, 4]]
        b = [[1, 9], [3, 4]]
        assert diff_mask(a, b) == [[0, 1], [0, 0]]

    def test_diff_mask_different_sizes(self) -> None:
        a = [[1]]
        b = [[1, 2], [3, 4]]
        mask = diff_mask(a, b)
        assert grid_shape(mask) == (2, 2)


# ---------------------------------------------------------------------------
# Phase S: DSL reference
# ---------------------------------------------------------------------------


class TestDSLReference:
    """Tests for the DSL reference string."""

    def test_returns_string(self) -> None:
        from loopagi.arc.grid_ops import get_dsl_reference
        ref = get_dsl_reference()
        assert isinstance(ref, str)
        assert len(ref) > 100

    def test_contains_key_functions(self) -> None:
        from loopagi.arc.grid_ops import get_dsl_reference
        ref = get_dsl_reference()
        assert "rotate_cw" in ref
        assert "flood_fill" in ref
        assert "overlay" in ref
        assert "crop" in ref
        assert "scale_up" in ref
        assert "unique_colors" in ref

    def test_contains_categories(self) -> None:
        from loopagi.arc.grid_ops import get_dsl_reference
        ref = get_dsl_reference()
        assert "Rotation" in ref
        assert "Color" in ref
        assert "Symmetry" in ref
        assert "Comparison" in ref
