"""ARC-AGI Grid Objects: Object detection and manipulation.

Implements Chollet's "objectness" core knowledge prior:
- Connected component detection (4-connected and 8-connected)
- Object extraction, bounding boxes, properties
- Object relationships (adjacency, containment, alignment)

Objects are contiguous regions of non-background color in the grid.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

from loopagi.arc.grid_ops import (
    BBox,
    Color,
    Grid,
    background_color,
    crop,
    grid_shape,
    make_grid,
)

Position: TypeAlias = tuple[int, int]


@dataclass
class GridObject:
    """A detected object (connected component) in an ARC grid."""

    obj_id: int
    color: Color
    pixels: list[Position] = field(default_factory=list)

    @property
    def size(self) -> int:
        """Number of pixels in the object."""
        return len(self.pixels)

    @property
    def bbox(self) -> BBox:
        """Bounding box: (row_min, col_min, row_max, col_max)."""
        if not self.pixels:
            return (0, 0, 0, 0)
        rows = [p[0] for p in self.pixels]
        cols = [p[1] for p in self.pixels]
        return (min(rows), min(cols), max(rows), max(cols))

    @property
    def bbox_shape(self) -> tuple[int, int]:
        """Height and width of bounding box."""
        r_min, c_min, r_max, c_max = self.bbox
        return (r_max - r_min + 1, c_max - c_min + 1)

    @property
    def center(self) -> tuple[float, float]:
        """Center of mass (row, col) as floats."""
        if not self.pixels:
            return (0.0, 0.0)
        avg_r = sum(p[0] for p in self.pixels) / len(self.pixels)
        avg_c = sum(p[1] for p in self.pixels) / len(self.pixels)
        return (avg_r, avg_c)

    @property
    def is_rectangular(self) -> bool:
        """Check if the object fills its entire bounding box."""
        h, w = self.bbox_shape
        return self.size == h * w

    @property
    def pixel_set(self) -> set[Position]:
        """Pixels as a set for fast membership tests."""
        return set(self.pixels)

    def to_grid(self, bg: Color = 0) -> Grid:
        """Extract object as a minimal grid (cropped to bounding box)."""
        r_min, c_min, r_max, c_max = self.bbox
        h, w = r_max - r_min + 1, c_max - c_min + 1
        result = make_grid(h, w, bg)
        for r, c in self.pixels:
            result[r - r_min][c - c_min] = self.color
        return result

    def summary(self) -> str:
        """Brief summary string."""
        h, w = self.bbox_shape
        return (
            f"Object {self.obj_id}: color={self.color}, "
            f"size={self.size}, bbox={h}x{w}, "
            f"rect={self.is_rectangular}"
        )


# --- Connected Component Detection ---


def _flood_fill_component(
    grid: Grid,
    start_r: int,
    start_c: int,
    visited: set[Position],
    target_color: Color,
    connectivity: int = 4,
) -> list[Position]:
    """Flood-fill to find all pixels of a connected component."""
    rows, cols = grid_shape(grid)
    pixels: list[Position] = []
    stack = [(start_r, start_c)]

    if connectivity == 8:
        neighbors = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                     (0, 1), (1, -1), (1, 0), (1, 1)]
    else:
        neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while stack:
        r, c = stack.pop()
        if (r, c) in visited:
            continue
        if r < 0 or r >= rows or c < 0 or c >= cols:
            continue
        if grid[r][c] != target_color:
            continue
        visited.add((r, c))
        pixels.append((r, c))
        for dr, dc in neighbors:
            stack.append((r + dr, c + dc))

    return pixels


def find_objects(
    grid: Grid,
    bg: Color | None = None,
    connectivity: int = 4,
    min_size: int = 1,
) -> list[GridObject]:
    """Find all connected components (objects) in the grid.

    Args:
        grid: The input grid.
        bg: Background color to exclude. Auto-detected if None.
        connectivity: 4 or 8 for neighbor connectivity.
        min_size: Minimum pixels to count as an object.

    Returns:
        List of GridObject instances, sorted by size (largest first).
    """
    rows, cols = grid_shape(grid)
    if bg is None:
        bg = background_color(grid)

    visited: set[Position] = set()
    objects: list[GridObject] = []
    obj_id = 0

    for r in range(rows):
        for c in range(cols):
            if (r, c) in visited or grid[r][c] == bg:
                visited.add((r, c))
                continue
            color = grid[r][c]
            pixels = _flood_fill_component(
                grid, r, c, visited, color, connectivity
            )
            if len(pixels) >= min_size:
                objects.append(GridObject(
                    obj_id=obj_id, color=color, pixels=sorted(pixels)
                ))
                obj_id += 1

    objects.sort(key=lambda o: o.size, reverse=True)
    return objects


def find_objects_multicolor(
    grid: Grid,
    bg: Color | None = None,
    connectivity: int = 4,
) -> list[GridObject]:
    """Find objects treating any non-background pixel as part of an object.

    Unlike find_objects which groups by same color, this groups all
    non-background connected pixels regardless of color.

    Args:
        grid: The input grid.
        bg: Background color. Auto-detected if None.
        connectivity: 4 or 8 connectivity.

    Returns:
        List of multi-color GridObject instances. Color is set to -1.
    """
    rows, cols = grid_shape(grid)
    if bg is None:
        bg = background_color(grid)

    visited: set[Position] = set()
    objects: list[GridObject] = []
    obj_id = 0

    if connectivity == 8:
        neighbors = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                     (0, 1), (1, -1), (1, 0), (1, 1)]
    else:
        neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for r in range(rows):
        for c in range(cols):
            if (r, c) in visited or grid[r][c] == bg:
                visited.add((r, c))
                continue
            # BFS for any non-bg connected pixels
            pixels: list[Position] = []
            stack = [(r, c)]
            while stack:
                cr, cc = stack.pop()
                if (cr, cc) in visited:
                    continue
                if cr < 0 or cr >= rows or cc < 0 or cc >= cols:
                    continue
                if grid[cr][cc] == bg:
                    visited.add((cr, cc))
                    continue
                visited.add((cr, cc))
                pixels.append((cr, cc))
                for dr, dc in neighbors:
                    stack.append((cr + dr, cc + dc))

            if pixels:
                objects.append(GridObject(
                    obj_id=obj_id, color=-1, pixels=sorted(pixels)
                ))
                obj_id += 1

    objects.sort(key=lambda o: o.size, reverse=True)
    return objects


# --- Object Relationships ---


def objects_adjacent(a: GridObject, b: GridObject, connectivity: int = 4) -> bool:
    """Check if two objects are adjacent (share a neighbor pixel)."""
    if connectivity == 8:
        deltas = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                  (0, 1), (1, -1), (1, 0), (1, 1)]
    else:
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    b_pixels = b.pixel_set
    for r, c in a.pixels:
        for dr, dc in deltas:
            if (r + dr, c + dc) in b_pixels:
                return True
    return False


def object_contains(outer: GridObject, inner: GridObject) -> bool:
    """Check if inner object's bounding box is fully inside outer's."""
    o = outer.bbox
    i = inner.bbox
    return (o[0] <= i[0] and o[1] <= i[1] and
            o[2] >= i[2] and o[3] >= i[3])


def objects_aligned_horizontal(a: GridObject, b: GridObject) -> bool:
    """Check if two objects share the same row range."""
    return a.bbox[0] == b.bbox[0] and a.bbox[2] == b.bbox[2]


def objects_aligned_vertical(a: GridObject, b: GridObject) -> bool:
    """Check if two objects share the same column range."""
    return a.bbox[1] == b.bbox[1] and a.bbox[3] == b.bbox[3]


def object_distance(a: GridObject, b: GridObject) -> float:
    """Manhattan distance between object centers."""
    ca, cb = a.center, b.center
    return abs(ca[0] - cb[0]) + abs(ca[1] - cb[1])


# --- Object Extraction ---


def extract_object_grid(grid: Grid, obj: GridObject, bg: Color = 0) -> Grid:
    """Extract an object from the grid, cropped to its bounding box."""
    r_min, c_min, r_max, c_max = obj.bbox
    h, w = r_max - r_min + 1, c_max - c_min + 1
    result = make_grid(h, w, bg)
    for r, c in obj.pixels:
        result[r - r_min][c - c_min] = grid[r][c]
    return result


def place_object(
    grid: Grid,
    obj_grid: Grid,
    r: int,
    c: int,
    transparent: Color = 0,
) -> Grid:
    """Place an object grid onto a base grid at position (r, c)."""
    from loopagi.arc.grid_ops import deep_copy
    result = deep_copy(grid)
    rows, cols = grid_shape(result)
    o_rows, o_cols = grid_shape(obj_grid)
    for or_ in range(o_rows):
        for oc in range(o_cols):
            nr, nc = r + or_, c + oc
            if 0 <= nr < rows and 0 <= nc < cols:
                if obj_grid[or_][oc] != transparent:
                    result[nr][nc] = obj_grid[or_][oc]
    return result


def remove_object(grid: Grid, obj: GridObject, fill: Color = 0) -> Grid:
    """Remove an object from the grid, replacing its pixels with fill."""
    from loopagi.arc.grid_ops import deep_copy
    result = deep_copy(grid)
    for r, c in obj.pixels:
        result[r][c] = fill
    return result
