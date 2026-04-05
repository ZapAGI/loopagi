"""ARC-AGI Grid DSL: Core grid transformation primitives.

Implements Chollet's core knowledge priors as composable operations:
- Geometry and topology: rotate, reflect, translate, scale, crop, pad, tile
- Color operations: recolor, flood_fill, swap_colors
- Pattern operations: overlay, mask, symmetry detection
- Counting and arithmetic: count_by_color, dimensions, unique_colors

All operations work on Grid (list[list[int]]) and return new grids.
No mutation of input grids.
"""

from __future__ import annotations

import copy
from collections import Counter
from typing import TypeAlias

Grid: TypeAlias = list[list[int]]
Color: TypeAlias = int
BBox: TypeAlias = tuple[int, int, int, int]  # (row_min, col_min, row_max, col_max)


# --- Grid Construction ---


def make_grid(rows: int, cols: int, fill: Color = 0) -> Grid:
    """Create a new grid filled with a single color."""
    return [[fill] * cols for _ in range(rows)]


def grid_shape(grid: Grid) -> tuple[int, int]:
    """Return (rows, cols) of a grid."""
    if not grid:
        return (0, 0)
    return (len(grid), len(grid[0]))


def deep_copy(grid: Grid) -> Grid:
    """Return a deep copy of a grid."""
    return copy.deepcopy(grid)


# --- Geometric Transforms ---


def rotate_cw(grid: Grid) -> Grid:
    """Rotate grid 90 degrees clockwise."""
    if not grid:
        return []
    rows, cols = grid_shape(grid)
    return [[grid[rows - 1 - r][c] for r in range(rows)] for c in range(cols)]


def rotate_ccw(grid: Grid) -> Grid:
    """Rotate grid 90 degrees counter-clockwise."""
    if not grid:
        return []
    rows, cols = grid_shape(grid)
    return [[grid[r][c] for r in range(rows)] for c in range(cols - 1, -1, -1)]


def rotate_180(grid: Grid) -> Grid:
    """Rotate grid 180 degrees."""
    if not grid:
        return []
    return [row[::-1] for row in reversed(grid)]


def reflect_horizontal(grid: Grid) -> Grid:
    """Reflect grid along the horizontal axis (flip top-bottom)."""
    return list(reversed(grid))


def reflect_vertical(grid: Grid) -> Grid:
    """Reflect grid along the vertical axis (flip left-right)."""
    return [row[::-1] for row in grid]


def reflect_diagonal(grid: Grid) -> Grid:
    """Reflect grid along the main diagonal (transpose)."""
    if not grid:
        return []
    rows, cols = grid_shape(grid)
    return [[grid[r][c] for r in range(rows)] for c in range(cols)]


def reflect_anti_diagonal(grid: Grid) -> Grid:
    """Reflect grid along the anti-diagonal."""
    if not grid:
        return []
    rows, cols = grid_shape(grid)
    return [[grid[rows - 1 - c][cols - 1 - r] for c in range(cols)]
            for r in range(rows)]


def translate(grid: Grid, dr: int, dc: int, fill: Color = 0) -> Grid:
    """Translate grid by (dr, dc), filling empty space with fill color."""
    rows, cols = grid_shape(grid)
    result = make_grid(rows, cols, fill)
    for r in range(rows):
        for c in range(cols):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                result[nr][nc] = grid[r][c]
    return result


def scale_up(grid: Grid, factor: int) -> Grid:
    """Scale grid up by an integer factor (each cell becomes factor x factor)."""
    if factor < 1:
        raise ValueError(f"Scale factor must be >= 1, got {factor}")
    rows, cols = grid_shape(grid)
    result: Grid = []
    for r in range(rows):
        for _ in range(factor):
            result.append([])
            for c in range(cols):
                result[-1].extend([grid[r][c]] * factor)
    return result


def crop(grid: Grid, bbox: BBox) -> Grid:
    """Crop grid to bounding box (row_min, col_min, row_max, col_max) inclusive."""
    r_min, c_min, r_max, c_max = bbox
    return [row[c_min:c_max + 1] for row in grid[r_min:r_max + 1]]


def pad(grid: Grid, top: int = 0, bottom: int = 0,
        left: int = 0, right: int = 0, fill: Color = 0) -> Grid:
    """Pad grid with fill color on specified sides."""
    rows, cols = grid_shape(grid)
    new_cols = left + cols + right
    result: Grid = []
    for _ in range(top):
        result.append([fill] * new_cols)
    for r in range(rows):
        result.append([fill] * left + grid[r] + [fill] * right)
    for _ in range(bottom):
        result.append([fill] * new_cols)
    return result


def tile(pattern: Grid, tile_rows: int, tile_cols: int) -> Grid:
    """Tile a pattern into a larger grid."""
    p_rows, p_cols = grid_shape(pattern)
    result: Grid = []
    for tr in range(tile_rows):
        for pr in range(p_rows):
            row: list[int] = []
            for _ in range(tile_cols):
                row.extend(pattern[pr])
            result.append(row)
    return result


# --- Color Operations ---


def recolor(grid: Grid, mapping: dict[Color, Color]) -> Grid:
    """Apply a color mapping to the grid."""
    return [[mapping.get(v, v) for v in row] for row in grid]


def swap_colors(grid: Grid, c1: Color, c2: Color) -> Grid:
    """Swap two colors in the grid."""
    return recolor(grid, {c1: c2, c2: c1})


def flood_fill(grid: Grid, r: int, c: int, new_color: Color) -> Grid:
    """Flood-fill from (r, c) with new_color (4-connected)."""
    result = deep_copy(grid)
    rows, cols = grid_shape(result)
    if r < 0 or r >= rows or c < 0 or c >= cols:
        return result
    old_color = result[r][c]
    if old_color == new_color:
        return result
    stack = [(r, c)]
    while stack:
        cr, cc = stack.pop()
        if cr < 0 or cr >= rows or cc < 0 or cc >= cols:
            continue
        if result[cr][cc] != old_color:
            continue
        result[cr][cc] = new_color
        stack.extend([(cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)])
    return result


def replace_color(grid: Grid, old: Color, new: Color) -> Grid:
    """Replace all occurrences of old color with new color."""
    return recolor(grid, {old: new})


# --- Pattern Operations ---


def overlay(base: Grid, top: Grid, transparent: Color = 0) -> Grid:
    """Overlay top grid onto base grid. Transparent color in top shows base through."""
    b_rows, b_cols = grid_shape(base)
    t_rows, t_cols = grid_shape(top)
    result = deep_copy(base)
    for r in range(min(b_rows, t_rows)):
        for c in range(min(b_cols, t_cols)):
            if top[r][c] != transparent:
                result[r][c] = top[r][c]
    return result


def mask_by_color(grid: Grid, color: Color) -> Grid:
    """Create a binary mask: 1 where grid has color, 0 elsewhere."""
    return [[1 if v == color else 0 for v in row] for row in grid]


def apply_mask(grid: Grid, mask: Grid, fill: Color = 0) -> Grid:
    """Keep grid values where mask is non-zero, fill elsewhere."""
    rows, cols = grid_shape(grid)
    result = make_grid(rows, cols, fill)
    for r in range(rows):
        for c in range(cols):
            if r < len(mask) and c < len(mask[r]) and mask[r][c] != 0:
                result[r][c] = grid[r][c]
    return result


def extract_subgrid(grid: Grid, r: int, c: int, h: int, w: int) -> Grid:
    """Extract a subgrid of size h x w starting at (r, c)."""
    return [row[c:c + w] for row in grid[r:r + h]]


# --- Analysis and Counting ---


def unique_colors(grid: Grid) -> set[Color]:
    """Return the set of unique colors in the grid."""
    colors: set[Color] = set()
    for row in grid:
        colors.update(row)
    return colors


def count_by_color(grid: Grid) -> dict[Color, int]:
    """Count occurrences of each color."""
    counter: Counter[Color] = Counter()
    for row in grid:
        counter.update(row)
    return dict(counter)


def most_common_color(grid: Grid, exclude: set[Color] | None = None) -> Color:
    """Return the most common color, optionally excluding some."""
    counts = count_by_color(grid)
    if exclude:
        counts = {k: v for k, v in counts.items() if k not in exclude}
    if not counts:
        return 0
    return max(counts, key=lambda k: counts[k])


def background_color(grid: Grid) -> Color:
    """Heuristic: the most common color is likely the background."""
    return most_common_color(grid)


def color_positions(grid: Grid, color: Color) -> list[tuple[int, int]]:
    """Return all (row, col) positions of a given color."""
    positions: list[tuple[int, int]] = []
    rows, cols = grid_shape(grid)
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == color:
                positions.append((r, c))
    return positions


# --- Symmetry Detection ---


def is_symmetric_horizontal(grid: Grid) -> bool:
    """Check if grid has horizontal symmetry (top-bottom mirror)."""
    return grid == reflect_horizontal(grid)


def is_symmetric_vertical(grid: Grid) -> bool:
    """Check if grid has vertical symmetry (left-right mirror)."""
    return grid == reflect_vertical(grid)


def is_symmetric_diagonal(grid: Grid) -> bool:
    """Check if grid is symmetric along the main diagonal."""
    rows, cols = grid_shape(grid)
    if rows != cols:
        return False
    return grid == reflect_diagonal(grid)


def is_rotationally_symmetric(grid: Grid) -> bool:
    """Check if grid has 180-degree rotational symmetry."""
    return grid == rotate_180(grid)


def symmetry_report(grid: Grid) -> dict[str, bool]:
    """Return a dictionary of all symmetry types detected."""
    return {
        "horizontal": is_symmetric_horizontal(grid),
        "vertical": is_symmetric_vertical(grid),
        "diagonal": is_symmetric_diagonal(grid),
        "rotational_180": is_rotationally_symmetric(grid),
    }


# --- Grid Comparison ---


def grids_equal(a: Grid, b: Grid) -> bool:
    """Check if two grids are identical."""
    if grid_shape(a) != grid_shape(b):
        return False
    return all(ar == br for ar, br in zip(a, b))


def get_dsl_reference() -> str:
    """Return a compact reference of available grid operations.

    Used by the synthesis prompt to give the LLM access to existing
    grid primitives instead of reimplementing them from scratch.
    """
    return """\
Available grid functions (from loopagi.arc.grid_ops):
  Construction:  make_grid(rows, cols, fill=0), deep_copy(g)
  Shape:         grid_shape(g) -> (rows, cols)
  Rotation:      rotate_cw(g), rotate_ccw(g), rotate_180(g)
  Reflection:    reflect_horizontal(g), reflect_vertical(g),
                 reflect_diagonal(g), reflect_anti_diagonal(g)
  Transform:     translate(g, dr, dc, fill=0), scale_up(g, factor)
  Slicing:       crop(g, bbox), extract_subgrid(g, r, c, h, w)
  Padding:       pad(g, top=0, bottom=0, left=0, right=0, fill=0)
  Tiling:        tile(pattern, tile_rows, tile_cols)
  Color:         recolor(g, mapping), swap_colors(g, c1, c2),
                 replace_color(g, old, new), flood_fill(g, r, c, new)
  Compositing:   overlay(base, top, transparent=0)
  Masking:       mask_by_color(g, color), apply_mask(g, mask, fill=0)
  Analysis:      unique_colors(g), count_by_color(g),
                 most_common_color(g, exclude=None), background_color(g),
                 color_positions(g, color)
  Symmetry:      is_symmetric_horizontal(g), is_symmetric_vertical(g),
                 is_symmetric_diagonal(g), is_rotationally_symmetric(g),
                 symmetry_report(g)
  Comparison:    grids_equal(a, b), diff_mask(a, b)"""


def diff_mask(a: Grid, b: Grid) -> Grid:
    """Return a mask where 1 indicates cells that differ between a and b."""
    rows_a, cols_a = grid_shape(a)
    rows_b, cols_b = grid_shape(b)
    rows, cols = max(rows_a, rows_b), max(cols_a, cols_b)
    result = make_grid(rows, cols, 0)
    for r in range(rows):
        for c in range(cols):
            va = a[r][c] if r < rows_a and c < cols_a else -1
            vb = b[r][c] if r < rows_b and c < cols_b else -1
            if va != vb:
                result[r][c] = 1
    return result
