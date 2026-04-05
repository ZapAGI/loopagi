"""Tests for loopagi.arc.grid_describer — object-centric grid descriptions."""

from __future__ import annotations

import pytest

from loopagi.arc.grid_describer import (
    GridDescription,
    ObjectInfo,
    _classify_shape,
    color_name,
    describe_grid,
    describe_pair,
    describe_transform,
    format_object_prompt,
)
from loopagi.arc.grid_objects import GridObject


# ---------------------------------------------------------------------------
# color_name
# ---------------------------------------------------------------------------

class TestColorName:
    """Tests for color name lookup."""

    def test_known_colors(self):
        assert color_name(0) == "black"
        assert color_name(1) == "blue"
        assert color_name(2) == "red"
        assert color_name(9) == "maroon"

    def test_unknown_color(self):
        assert color_name(42) == "color_42"


# ---------------------------------------------------------------------------
# _classify_shape
# ---------------------------------------------------------------------------

class TestClassifyShape:
    """Tests for shape classification."""

    def test_dot(self):
        obj = GridObject(obj_id=0, color=1, pixels=[(0, 0)])
        assert _classify_shape(obj) == "dot"

    def test_horizontal_line(self):
        obj = GridObject(obj_id=0, color=1, pixels=[(0, 0), (0, 1), (0, 2)])
        assert _classify_shape(obj) == "horizontal line"

    def test_vertical_line(self):
        obj = GridObject(obj_id=0, color=1, pixels=[(0, 0), (1, 0), (2, 0)])
        assert _classify_shape(obj) == "vertical line"

    def test_square(self):
        pixels = [(r, c) for r in range(3) for c in range(3)]
        obj = GridObject(obj_id=0, color=1, pixels=pixels)
        assert _classify_shape(obj) == "square"

    def test_rectangle(self):
        pixels = [(r, c) for r in range(2) for c in range(4)]
        obj = GridObject(obj_id=0, color=1, pixels=pixels)
        assert _classify_shape(obj) == "rectangle"

    def test_l_shape(self):
        # L-shape: 3x3 bbox, 5 pixels (55% fill ratio)
        pixels = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]
        obj = GridObject(obj_id=0, color=1, pixels=pixels)
        shape = _classify_shape(obj)
        assert shape in ("L-shape", "irregular")


# ---------------------------------------------------------------------------
# describe_grid
# ---------------------------------------------------------------------------

class TestDescribeGrid:
    """Tests for grid description generation."""

    def test_uniform_grid(self):
        grid = [[0, 0], [0, 0]]
        desc = describe_grid(grid)
        assert isinstance(desc, GridDescription)
        assert desc.rows == 2
        assert desc.cols == 2
        assert desc.bg_color == 0
        assert len(desc.objects) == 0
        assert "uniform" in desc.text.lower() or "none" in desc.text.lower()

    def test_single_object(self):
        grid = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
        desc = describe_grid(grid)
        assert desc.num_colors == 2
        assert len(desc.objects) == 1
        assert desc.objects[0].color == 1
        assert desc.objects[0].shape_name == "dot"

    def test_two_objects(self):
        grid = [[1, 0, 2], [0, 0, 0], [0, 0, 0]]
        desc = describe_grid(grid)
        assert len(desc.objects) == 2

    def test_text_contains_grid_size(self):
        grid = [[0, 1], [2, 0], [0, 3]]
        desc = describe_grid(grid)
        assert "3x2" in desc.text

    def test_text_contains_object_info(self):
        grid = [[0, 0, 0], [0, 1, 1], [0, 1, 1]]
        desc = describe_grid(grid)
        assert "square" in desc.text or "rectangle" in desc.text
        assert "blue" in desc.text  # color 1 = blue

    def test_colors_used(self):
        grid = [[0, 1], [2, 3]]
        desc = describe_grid(grid)
        assert set(desc.colors_used) == {0, 1, 2, 3}

    def test_bg_name(self):
        grid = [[0, 0], [0, 1]]
        desc = describe_grid(grid)
        assert desc.bg_name == "black"


# ---------------------------------------------------------------------------
# describe_transform
# ---------------------------------------------------------------------------

class TestDescribeTransform:
    """Tests for transform description."""

    def test_size_unchanged(self):
        in_desc = describe_grid([[0, 1], [0, 0]])
        out_desc = describe_grid([[0, 2], [0, 0]])
        text = describe_transform(in_desc, out_desc)
        assert "unchanged" in text

    def test_size_changed(self):
        in_desc = describe_grid([[0, 1]])
        out_desc = describe_grid([[0, 1], [0, 0]])
        text = describe_transform(in_desc, out_desc)
        assert "1x2" in text
        assert "2x2" in text

    def test_new_colors(self):
        in_desc = describe_grid([[0, 1], [0, 0]])
        out_desc = describe_grid([[0, 1], [0, 3]])
        text = describe_transform(in_desc, out_desc)
        assert "New colors" in text

    def test_removed_colors(self):
        in_desc = describe_grid([[0, 1], [0, 2]])
        out_desc = describe_grid([[0, 0], [0, 2]])
        text = describe_transform(in_desc, out_desc)
        assert "Removed colors" in text

    def test_object_count_change(self):
        in_desc = describe_grid([[1, 0, 2]])
        out_desc = describe_grid([[1, 0, 0]])
        text = describe_transform(in_desc, out_desc)
        assert "→" in text or "same count" in text


# ---------------------------------------------------------------------------
# describe_pair
# ---------------------------------------------------------------------------

class TestDescribePair:
    """Tests for pair description."""

    def test_contains_sections(self):
        inp = [[0, 1], [0, 0]]
        out = [[0, 2], [0, 0]]
        text = describe_pair(inp, out, 0)
        assert "Pair 1" in text
        assert "Input:" in text
        assert "Output:" in text
        assert "Transform:" in text

    def test_pair_index(self):
        text = describe_pair([[0]], [[1]], 2)
        assert "Pair 3" in text


# ---------------------------------------------------------------------------
# format_object_prompt
# ---------------------------------------------------------------------------

class TestFormatObjectPrompt:
    """Tests for full object-aware prompt generation."""

    def test_single_pair(self):
        pairs = [([[0, 1], [0, 0]], [[0, 2], [0, 0]])]
        prompt = format_object_prompt(pairs)
        assert "Object-Centric Analysis" in prompt
        assert "End Analysis" in prompt
        assert "Pair 1" in prompt

    def test_multiple_pairs(self):
        pairs = [
            ([[0]], [[1]]),
            ([[2]], [[3]]),
        ]
        prompt = format_object_prompt(pairs)
        assert "Pair 1" in prompt
        assert "Pair 2" in prompt

    def test_includes_objects(self):
        pairs = [([[0, 0, 0], [0, 1, 0], [0, 0, 0]], [[0, 0, 0], [0, 2, 0], [0, 0, 0]])]
        prompt = format_object_prompt(pairs)
        assert "blue" in prompt or "Obj" in prompt


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge case tests."""

    def test_single_cell_grid(self):
        desc = describe_grid([[5]])
        assert desc.rows == 1
        assert desc.cols == 1

    def test_large_grid_no_crash(self):
        grid = [[0] * 30 for _ in range(30)]
        grid[15][15] = 1
        desc = describe_grid(grid)
        assert desc.rows == 30
        assert len(desc.objects) == 1

    def test_all_same_color(self):
        grid = [[3, 3], [3, 3]]
        desc = describe_grid(grid)
        assert desc.bg_color == 3
        assert len(desc.objects) == 0
