"""Tests for loopagi.arc.grid_objects module."""

from __future__ import annotations

import pytest

from loopagi.arc.grid_objects import (
    GridObject,
    extract_object_grid,
    find_objects,
    find_objects_multicolor,
    object_contains,
    object_distance,
    objects_adjacent,
    objects_aligned_horizontal,
    objects_aligned_vertical,
    place_object,
    remove_object,
)


# --- Fixtures ---


@pytest.fixture
def simple_grid() -> list[list[int]]:
    """Grid with two distinct objects on a black background.

    0 0 0 0 0
    0 1 1 0 0
    0 1 0 0 0
    0 0 0 2 2
    0 0 0 2 2
    """
    return [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 2, 2],
        [0, 0, 0, 2, 2],
    ]


@pytest.fixture
def multicolor_grid() -> list[list[int]]:
    """Grid with a multi-color connected object.

    0 0 0
    0 1 2
    0 3 0
    """
    return [
        [0, 0, 0],
        [0, 1, 2],
        [0, 3, 0],
    ]


# --- GridObject Tests ---


class TestGridObject:
    def test_basic_properties(self) -> None:
        obj = GridObject(obj_id=0, color=1, pixels=[(0, 0), (0, 1), (1, 0)])
        assert obj.size == 3
        assert obj.bbox == (0, 0, 1, 1)
        assert obj.bbox_shape == (2, 2)

    def test_is_rectangular(self) -> None:
        # 2x2 bounding box with 4 pixels = rectangular
        rect = GridObject(
            obj_id=0, color=1,
            pixels=[(0, 0), (0, 1), (1, 0), (1, 1)]
        )
        assert rect.is_rectangular is True

        # 2x2 bounding box with 3 pixels = not rectangular
        lshape = GridObject(
            obj_id=0, color=1,
            pixels=[(0, 0), (0, 1), (1, 0)]
        )
        assert lshape.is_rectangular is False

    def test_center(self) -> None:
        obj = GridObject(obj_id=0, color=1, pixels=[(0, 0), (0, 2)])
        cr, cc = obj.center
        assert cr == 0.0
        assert cc == 1.0

    def test_to_grid(self) -> None:
        obj = GridObject(
            obj_id=0, color=1,
            pixels=[(1, 1), (1, 2), (2, 1)]
        )
        g = obj.to_grid(bg=0)
        assert g == [[1, 1], [1, 0]]

    def test_pixel_set(self) -> None:
        obj = GridObject(obj_id=0, color=1, pixels=[(0, 0), (1, 1)])
        assert obj.pixel_set == {(0, 0), (1, 1)}

    def test_summary(self) -> None:
        obj = GridObject(obj_id=0, color=1, pixels=[(0, 0)])
        s = obj.summary()
        assert "color=1" in s
        assert "size=1" in s

    def test_empty_object(self) -> None:
        obj = GridObject(obj_id=0, color=0, pixels=[])
        assert obj.size == 0
        assert obj.bbox == (0, 0, 0, 0)
        assert obj.center == (0.0, 0.0)


# --- find_objects Tests ---


class TestFindObjects:
    def test_finds_two_objects(self, simple_grid: list[list[int]]) -> None:
        objs = find_objects(simple_grid, bg=0)
        assert len(objs) == 2

    def test_object_colors(self, simple_grid: list[list[int]]) -> None:
        objs = find_objects(simple_grid, bg=0)
        colors = {o.color for o in objs}
        assert colors == {1, 2}

    def test_object_sizes(self, simple_grid: list[list[int]]) -> None:
        objs = find_objects(simple_grid, bg=0)
        sizes = sorted([o.size for o in objs], reverse=True)
        assert sizes == [4, 3]  # 2x2 square = 4, L-shape = 3

    def test_auto_detect_background(self, simple_grid: list[list[int]]) -> None:
        objs = find_objects(simple_grid)  # bg auto-detected
        assert len(objs) == 2

    def test_min_size_filter(self, simple_grid: list[list[int]]) -> None:
        objs = find_objects(simple_grid, bg=0, min_size=4)
        assert len(objs) == 1
        assert objs[0].color == 2

    def test_8_connectivity(self) -> None:
        # Two pixels diagonal from each other
        g = [[1, 0], [0, 1]]
        objs_4 = find_objects(g, bg=0, connectivity=4)
        objs_8 = find_objects(g, bg=0, connectivity=8)
        assert len(objs_4) == 2  # Separate in 4-connected
        assert len(objs_8) == 1  # Connected in 8-connected

    def test_single_pixel_objects(self) -> None:
        g = [[0, 1, 0], [0, 0, 0], [0, 2, 0]]
        objs = find_objects(g, bg=0)
        assert len(objs) == 2
        assert all(o.size == 1 for o in objs)

    def test_empty_grid(self) -> None:
        g = [[0, 0], [0, 0]]
        objs = find_objects(g, bg=0)
        assert len(objs) == 0

    def test_full_grid(self) -> None:
        g = [[1, 1], [1, 1]]
        objs = find_objects(g, bg=0)
        assert len(objs) == 1
        assert objs[0].size == 4

    def test_sorted_by_size(self) -> None:
        g = [
            [0, 0, 0, 0],
            [0, 1, 0, 2],
            [0, 0, 0, 2],
            [0, 0, 0, 2],
        ]
        objs = find_objects(g, bg=0)
        assert objs[0].size >= objs[1].size


# --- find_objects_multicolor Tests ---


class TestFindObjectsMulticolor:
    def test_groups_adjacent_colors(self, multicolor_grid: list[list[int]]) -> None:
        objs = find_objects_multicolor(multicolor_grid, bg=0, connectivity=4)
        # 1,2,3 are all connected via 4-connectivity:
        # (1,1)=1 adjacent to (1,2)=2 and (2,1)=3
        assert len(objs) == 1
        assert objs[0].size == 3

    def test_separate_groups(self) -> None:
        g = [[1, 0, 2], [0, 0, 0], [3, 0, 4]]
        objs = find_objects_multicolor(g, bg=0, connectivity=4)
        assert len(objs) == 4

    def test_8_connectivity_merges(self) -> None:
        g = [[1, 0], [0, 2]]
        objs_4 = find_objects_multicolor(g, bg=0, connectivity=4)
        objs_8 = find_objects_multicolor(g, bg=0, connectivity=8)
        assert len(objs_4) == 2
        assert len(objs_8) == 1


# --- Object Relationships ---


class TestObjectRelationships:
    def test_adjacent(self) -> None:
        a = GridObject(obj_id=0, color=1, pixels=[(0, 0)])
        b = GridObject(obj_id=1, color=2, pixels=[(0, 1)])
        assert objects_adjacent(a, b) is True

    def test_not_adjacent(self) -> None:
        a = GridObject(obj_id=0, color=1, pixels=[(0, 0)])
        b = GridObject(obj_id=1, color=2, pixels=[(2, 2)])
        assert objects_adjacent(a, b) is False

    def test_diagonal_adjacent_8(self) -> None:
        a = GridObject(obj_id=0, color=1, pixels=[(0, 0)])
        b = GridObject(obj_id=1, color=2, pixels=[(1, 1)])
        assert objects_adjacent(a, b, connectivity=4) is False
        assert objects_adjacent(a, b, connectivity=8) is True

    def test_contains(self) -> None:
        outer = GridObject(
            obj_id=0, color=1,
            pixels=[(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]
        )
        inner = GridObject(obj_id=1, color=2, pixels=[(1, 1)])
        assert object_contains(outer, inner) is True

    def test_not_contains(self) -> None:
        a = GridObject(obj_id=0, color=1, pixels=[(0, 0), (0, 1)])
        b = GridObject(obj_id=1, color=2, pixels=[(2, 2)])
        assert object_contains(a, b) is False

    def test_aligned_horizontal(self) -> None:
        a = GridObject(obj_id=0, color=1, pixels=[(1, 0), (1, 1)])
        b = GridObject(obj_id=1, color=2, pixels=[(1, 3), (1, 4)])
        assert objects_aligned_horizontal(a, b) is True

    def test_aligned_vertical(self) -> None:
        a = GridObject(obj_id=0, color=1, pixels=[(0, 1), (1, 1)])
        b = GridObject(obj_id=1, color=2, pixels=[(3, 1), (4, 1)])
        assert objects_aligned_vertical(a, b) is True

    def test_distance(self) -> None:
        a = GridObject(obj_id=0, color=1, pixels=[(0, 0)])
        b = GridObject(obj_id=1, color=2, pixels=[(3, 4)])
        assert object_distance(a, b) == 7.0


# --- Object Extraction ---


class TestObjectExtraction:
    def test_extract_object_grid(self, simple_grid: list[list[int]]) -> None:
        objs = find_objects(simple_grid, bg=0)
        # Find the L-shaped object (color=1)
        obj1 = [o for o in objs if o.color == 1][0]
        g = extract_object_grid(simple_grid, obj1, bg=0)
        assert g == [[1, 1], [1, 0]]

    def test_extract_square_object(self, simple_grid: list[list[int]]) -> None:
        objs = find_objects(simple_grid, bg=0)
        obj2 = [o for o in objs if o.color == 2][0]
        g = extract_object_grid(simple_grid, obj2, bg=0)
        assert g == [[2, 2], [2, 2]]

    def test_place_object(self) -> None:
        base = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        obj = [[1, 1], [1, 0]]
        result = place_object(base, obj, 0, 0, transparent=0)
        assert result == [[1, 1, 0], [1, 0, 0], [0, 0, 0]]

    def test_place_object_with_offset(self) -> None:
        base = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        obj = [[5]]
        result = place_object(base, obj, 1, 2)
        assert result[1][2] == 5

    def test_remove_object(self, simple_grid: list[list[int]]) -> None:
        objs = find_objects(simple_grid, bg=0)
        obj1 = [o for o in objs if o.color == 1][0]
        result = remove_object(simple_grid, obj1, fill=0)
        # All color-1 pixels should now be 0
        for r, c in obj1.pixels:
            assert result[r][c] == 0
        # Original unchanged
        assert simple_grid[1][1] == 1

    def test_place_and_remove_roundtrip(self) -> None:
        base = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        obj_grid = [[1, 1], [1, 0]]
        placed = place_object(base, obj_grid, 0, 0)
        objs = find_objects(placed, bg=0)
        removed = remove_object(placed, objs[0])
        assert removed == base
