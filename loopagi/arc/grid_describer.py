"""Object-centric grid description for ARC-AGI perception.

Converts raw integer grids into human-readable, object-centric
descriptions that dramatically improve LLM perception accuracy.
Research shows this can double LLM performance on ARC tasks.

Uses ``grid_objects.py`` for connected-component detection and
produces structured text suitable for perceiver/synthesizer prompts.

Usage:
    from loopagi.arc.grid_describer import describe_grid, describe_pair
    desc = describe_grid([[0,0,1],[0,1,0],[1,0,0]])
    print(desc.text)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from loopagi.arc.grid_objects import (
    GridObject,
    find_objects,
    object_contains,
    object_distance,
    objects_adjacent,
    objects_aligned_horizontal,
    objects_aligned_vertical,
)
from loopagi.arc.grid_ops import (
    Color,
    Grid,
    background_color,
    grid_shape,
    unique_colors,
)

logger = logging.getLogger(__name__)

# ARC color names (standard 10-color palette)
COLOR_NAMES: dict[int, str] = {
    0: "black",
    1: "blue",
    2: "red",
    3: "green",
    4: "yellow",
    5: "grey",
    6: "magenta",
    7: "orange",
    8: "cyan",
    9: "maroon",
}


def color_name(c: int) -> str:
    """Return human-readable color name."""
    return COLOR_NAMES.get(c, f"color_{c}")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ObjectInfo:
    """Summarised info about a detected grid object."""

    object_id: int
    color: int
    color_name: str
    cell_count: int
    bbox: tuple[int, int, int, int]
    bbox_shape: tuple[int, int]
    center: tuple[float, float]
    shape_name: str
    is_rectangular: bool


@dataclass
class GridDescription:
    """Object-centric description of a single grid."""

    rows: int
    cols: int
    bg_color: int
    bg_name: str
    num_colors: int
    colors_used: list[int]
    objects: list[ObjectInfo]
    spatial_relations: list[str]
    text: str


# ---------------------------------------------------------------------------
# Shape classification
# ---------------------------------------------------------------------------


def _classify_shape(obj: GridObject) -> str:
    """Classify an object's shape into a human-readable category."""
    h, w = obj.bbox_shape
    size = obj.size

    if size == 1:
        return "dot"
    if h == 1 and w > 1:
        return "horizontal line"
    if w == 1 and h > 1:
        return "vertical line"
    if obj.is_rectangular:
        if h == w:
            return "square"
        return "rectangle"
    if h == 1 or w == 1:
        return "line"

    # Check if it's L-shaped: fills ~75% of bbox
    bbox_area = h * w
    fill_ratio = size / bbox_area if bbox_area else 0

    if 0.4 <= fill_ratio <= 0.6:
        return "L-shape"
    if fill_ratio < 0.4:
        return "sparse"
    if fill_ratio > 0.8:
        return "near-rectangle"
    return "irregular"


# ---------------------------------------------------------------------------
# Spatial relationships
# ---------------------------------------------------------------------------


def _describe_relations(objects: list[GridObject]) -> list[str]:
    """Describe spatial relationships between objects."""
    relations: list[str] = []
    n = len(objects)
    if n < 2 or n > 15:
        return relations

    for i in range(n):
        for j in range(i + 1, n):
            a, b = objects[i], objects[j]
            ca, cb = a.center, b.center

            if objects_adjacent(a, b):
                relations.append(
                    f"Object {a.obj_id} is adjacent to Object {b.obj_id}"
                )
            if object_contains(a, b):
                relations.append(
                    f"Object {a.obj_id} contains Object {b.obj_id}"
                )
            elif object_contains(b, a):
                relations.append(
                    f"Object {b.obj_id} contains Object {a.obj_id}"
                )
            if objects_aligned_horizontal(a, b):
                relations.append(
                    f"Object {a.obj_id} and Object {b.obj_id} are horizontally aligned"
                )
            if objects_aligned_vertical(a, b):
                relations.append(
                    f"Object {a.obj_id} and Object {b.obj_id} are vertically aligned"
                )

    return relations[:20]  # Cap to avoid prompt bloat


# ---------------------------------------------------------------------------
# Core description
# ---------------------------------------------------------------------------


def describe_grid(grid: Grid) -> GridDescription:
    """Parse a grid into an object-centric description.

    Returns a GridDescription with detected objects, their properties,
    spatial relationships, and a formatted text block for LLM prompts.
    """
    rows, cols = grid_shape(grid)
    bg = background_color(grid)
    colors = unique_colors(grid)
    non_bg_colors = [c for c in sorted(colors) if c != bg]
    objects = find_objects(grid, bg=bg)

    obj_infos: list[ObjectInfo] = []
    for obj in objects:
        shape = _classify_shape(obj)
        obj_infos.append(ObjectInfo(
            object_id=obj.obj_id,
            color=obj.color,
            color_name=color_name(obj.color),
            cell_count=obj.size,
            bbox=obj.bbox,
            bbox_shape=obj.bbox_shape,
            center=obj.center,
            shape_name=shape,
            is_rectangular=obj.is_rectangular,
        ))

    relations = _describe_relations(objects)

    text = _format_description(rows, cols, bg, non_bg_colors, obj_infos, relations)

    return GridDescription(
        rows=rows,
        cols=cols,
        bg_color=bg,
        bg_name=color_name(bg),
        num_colors=len(colors),
        colors_used=sorted(colors),
        objects=obj_infos,
        spatial_relations=relations,
        text=text,
    )


def _format_description(
    rows: int,
    cols: int,
    bg: int,
    non_bg_colors: list[int],
    objects: list[ObjectInfo],
    relations: list[str],
) -> str:
    """Format a structured text description for LLM prompts."""
    lines: list[str] = []
    lines.append(
        f"Grid: {rows}x{cols}, background={color_name(bg)} ({bg}), "
        f"{len(non_bg_colors)} foreground color(s)"
    )

    if objects:
        lines.append(f"Objects ({len(objects)}):")
        for o in objects[:15]:  # Cap to avoid huge prompts
            lines.append(
                f"  - Obj {o.object_id}: {o.shape_name}, "
                f"color={o.color_name} ({o.color}), "
                f"size={o.cell_count}, "
                f"bbox={o.bbox_shape[0]}x{o.bbox_shape[1]} "
                f"at ({o.bbox[0]},{o.bbox[1]})"
            )
    else:
        lines.append("Objects: none (uniform grid)")

    if relations:
        lines.append("Relations:")
        for r in relations[:10]:
            lines.append(f"  - {r}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pair-level description (input → output transform)
# ---------------------------------------------------------------------------


def describe_transform(
    input_desc: GridDescription,
    output_desc: GridDescription,
) -> str:
    """Describe how a grid changes from input to output.

    Identifies: size changes, color changes, object count changes,
    new/removed objects.
    """
    lines: list[str] = []

    # Shape change
    if (input_desc.rows, input_desc.cols) != (output_desc.rows, output_desc.cols):
        lines.append(
            f"Size: {input_desc.rows}x{input_desc.cols} → "
            f"{output_desc.rows}x{output_desc.cols}"
        )
    else:
        lines.append(f"Size: unchanged ({input_desc.rows}x{input_desc.cols})")

    # Color changes
    in_colors = set(input_desc.colors_used)
    out_colors = set(output_desc.colors_used)
    new_colors = out_colors - in_colors
    removed_colors = in_colors - out_colors
    if new_colors:
        lines.append(f"New colors: {[color_name(c) for c in sorted(new_colors)]}")
    if removed_colors:
        lines.append(f"Removed colors: {[color_name(c) for c in sorted(removed_colors)]}")

    # Object count
    n_in = len(input_desc.objects)
    n_out = len(output_desc.objects)
    if n_in != n_out:
        lines.append(f"Objects: {n_in} → {n_out}")
    else:
        lines.append(f"Objects: {n_in} (same count)")

    # Color mapping (if same object count)
    if n_in == n_out and n_in > 0:
        color_map: list[str] = []
        for i_obj, o_obj in zip(input_desc.objects, output_desc.objects):
            if i_obj.color != o_obj.color:
                color_map.append(
                    f"{color_name(i_obj.color)}→{color_name(o_obj.color)}"
                )
        if color_map:
            lines.append(f"Color changes: {', '.join(color_map)}")

    return "\n".join(lines)


def describe_pair(
    inp: Grid,
    out: Grid,
    pair_idx: int = 0,
) -> str:
    """Describe a single training pair with object analysis."""
    in_desc = describe_grid(inp)
    out_desc = describe_grid(out)
    transform = describe_transform(in_desc, out_desc)

    return (
        f"--- Pair {pair_idx + 1} ---\n"
        f"Input:\n{in_desc.text}\n"
        f"Output:\n{out_desc.text}\n"
        f"Transform:\n{transform}"
    )


def format_object_prompt(
    train_pairs: list[tuple[Grid, Grid]],
) -> str:
    """Generate a full object-aware description for all training pairs.

    Suitable for prepending to perceiver or synthesizer prompts.
    """
    parts: list[str] = []
    parts.append("=== Object-Centric Analysis ===")

    for i, (inp, out) in enumerate(train_pairs):
        parts.append(describe_pair(inp, out, i))

    parts.append("=== End Analysis ===")
    return "\n\n".join(parts)
