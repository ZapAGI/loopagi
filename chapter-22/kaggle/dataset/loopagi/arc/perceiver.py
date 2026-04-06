"""ARC-AGI Perceiver Agent.

Analyzes training input/output grid pairs and produces a structured
perception report describing what changes between input and output.

The Perceiver is the first step in the refinement loop:
Perceive -> Hypothesize -> Synthesize -> Verify -> Refine
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loopagi.arc.arc_visualizer import grid_to_ascii
from loopagi.arc.grid_objects import find_objects
from loopagi.arc.grid_ops import (
    background_color,
    count_by_color,
    grid_shape,
    symmetry_report,
    unique_colors,
)

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import ArcTask, Grid

logger = logging.getLogger(__name__)


@dataclass
class GridAnalysis:
    """Structured analysis of a single grid."""

    shape: tuple[int, int]
    num_colors: int
    colors: set[int]
    color_counts: dict[int, int]
    background: int
    num_objects: int
    object_sizes: list[int]
    object_colors: list[int]
    symmetry: dict[str, bool]


@dataclass
class PairAnalysis:
    """Structured analysis of an input/output pair."""

    input_analysis: GridAnalysis
    output_analysis: GridAnalysis
    shape_changed: bool
    colors_added: set[int]
    colors_removed: set[int]
    size_ratio: tuple[float, float]


@dataclass
class PerceptionReport:
    """Full perception report for a task."""

    task_id: str
    num_pairs: int
    pair_analyses: list[PairAnalysis] = field(default_factory=list)
    llm_description: str = ""
    consistent_patterns: list[str] = field(default_factory=list)


def analyze_grid(grid: Grid) -> GridAnalysis:
    """Produce a structured analysis of a single grid."""
    shape = grid_shape(grid)
    colors = unique_colors(grid)
    bg = background_color(grid)
    objects = find_objects(grid, bg=bg)
    sym = symmetry_report(grid)

    return GridAnalysis(
        shape=shape,
        num_colors=len(colors),
        colors=colors,
        color_counts=count_by_color(grid),
        background=bg,
        num_objects=len(objects),
        object_sizes=[o.size for o in objects],
        object_colors=[o.color for o in objects],
        symmetry=sym,
    )


def analyze_pair(input_grid: Grid, output_grid: Grid) -> PairAnalysis:
    """Analyze the relationship between an input and output grid."""
    inp = analyze_grid(input_grid)
    out = analyze_grid(output_grid)

    inp_rows, inp_cols = inp.shape
    out_rows, out_cols = out.shape
    row_ratio = out_rows / inp_rows if inp_rows > 0 else 0.0
    col_ratio = out_cols / inp_cols if inp_cols > 0 else 0.0

    return PairAnalysis(
        input_analysis=inp,
        output_analysis=out,
        shape_changed=inp.shape != out.shape,
        colors_added=out.colors - inp.colors,
        colors_removed=inp.colors - out.colors,
        size_ratio=(row_ratio, col_ratio),
    )


def find_consistent_patterns(pairs: list[PairAnalysis]) -> list[str]:
    """Identify patterns that are consistent across all training pairs."""
    if not pairs:
        return []

    patterns: list[str] = []

    # Check shape consistency
    all_same_shape = all(not p.shape_changed for p in pairs)
    all_diff_shape = all(p.shape_changed for p in pairs)
    if all_same_shape:
        patterns.append("output_same_shape_as_input")
    elif all_diff_shape:
        ratios = [p.size_ratio for p in pairs]
        if len(set(ratios)) == 1:
            patterns.append(f"consistent_size_ratio_{ratios[0]}")
        else:
            patterns.append("output_different_shape")

    # Check color consistency
    all_same_colors = all(
        not p.colors_added and not p.colors_removed for p in pairs
    )
    if all_same_colors:
        patterns.append("same_color_palette")
    else:
        added = set.intersection(*(p.colors_added for p in pairs)) if pairs else set()
        removed = set.intersection(*(p.colors_removed for p in pairs)) if pairs else set()
        if added:
            patterns.append(f"always_adds_colors_{added}")
        if removed:
            patterns.append(f"always_removes_colors_{removed}")

    # Check object count changes
    obj_deltas = [
        p.output_analysis.num_objects - p.input_analysis.num_objects
        for p in pairs
    ]
    if len(set(obj_deltas)) == 1:
        delta = obj_deltas[0]
        if delta == 0:
            patterns.append("same_object_count")
        elif delta > 0:
            patterns.append(f"adds_{delta}_objects")
        else:
            patterns.append(f"removes_{abs(delta)}_objects")

    # Check background consistency
    if all(
        p.input_analysis.background == p.output_analysis.background
        for p in pairs
    ):
        patterns.append("same_background")

    # Check symmetry changes
    for sym_type in ("horizontal", "vertical", "diagonal", "rotational_180"):
        gained = all(
            not p.input_analysis.symmetry[sym_type]
            and p.output_analysis.symmetry[sym_type]
            for p in pairs
        )
        if gained:
            patterns.append(f"output_gains_{sym_type}_symmetry")

    return patterns


def grid_to_compact(grid: Grid) -> str:
    """Convert a grid to a compact string (no spaces, one row per line)."""
    return "\n".join("".join(str(v) for v in row) for row in grid)


def format_perception_prompt(task: ArcTask, max_pairs: int = 3) -> str:
    """Format task data into a compact prompt for the LLM perceiver.

    Uses compact grid format (no spaces) to minimize token count.
    Limits to max_pairs training pairs for large tasks.
    """
    pairs = task.train[:max_pairs]
    lines: list[str] = [
        f"ARC task: {task.num_train} pairs. Describe the transformation rule.",
        "What changes between input and output? Be concise.",
        "",
    ]

    for i, pair in enumerate(pairs):
        ir, ic = grid_shape(pair.input)
        or_, oc = grid_shape(pair.output)
        lines.append(f"Pair {i + 1}:")
        lines.append(f"In ({ir}x{ic}):")
        lines.append(grid_to_compact(pair.input))
        lines.append(f"Out ({or_}x{oc}):")
        lines.append(grid_to_compact(pair.output))
        lines.append("")

    lines.append("State the rule in ONE sentence.")
    return "\n".join(lines)


def perceive_task(task: ArcTask, llm_response: str = "") -> PerceptionReport:
    """Produce a full perception report for a task.

    Combines deterministic analysis with optional LLM description.

    Args:
        task: The ARC task to analyze.
        llm_response: Optional LLM-generated description of the transformation.

    Returns:
        PerceptionReport with structured analysis and patterns.
    """
    pair_analyses: list[PairAnalysis] = []
    for pair in task.train:
        pa = analyze_pair(pair.input, pair.output)
        pair_analyses.append(pa)

    consistent = find_consistent_patterns(pair_analyses)

    report = PerceptionReport(
        task_id=task.task_id,
        num_pairs=task.num_train,
        pair_analyses=pair_analyses,
        llm_description=llm_response,
        consistent_patterns=consistent,
    )

    logger.info(
        "Perceived task %s: %d pairs, %d patterns found",
        task.task_id,
        task.num_train,
        len(consistent),
    )
    return report


class TaskComplexity:
    """Task complexity level with associated iteration parameters."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    PARAMS: dict[str, dict[str, int]] = {
        "low": {"max_hypotheses": 3, "max_iterations": 3},
        "medium": {"max_hypotheses": 5, "max_iterations": 5},
        "high": {"max_hypotheses": 7, "max_iterations": 7},
    }


def estimate_complexity(report: PerceptionReport) -> tuple[str, dict[str, int]]:
    """Estimate task complexity from perception data.

    Uses grid size, color count, object count, and shape changes
    to classify a task as low, medium, or high complexity.

    Args:
        report: The perception report for the task.

    Returns:
        Tuple of (complexity_level, iteration_params).
    """
    if not report.pair_analyses:
        return TaskComplexity.MEDIUM, TaskComplexity.PARAMS[TaskComplexity.MEDIUM]

    score = 0

    # Factor 1: Grid size (larger grids are harder)
    avg_cells = sum(
        pa.input_analysis.shape[0] * pa.input_analysis.shape[1]
        for pa in report.pair_analyses
    ) / len(report.pair_analyses)
    if avg_cells > 100:
        score += 3
    elif avg_cells > 25:
        score += 1

    # Factor 2: Color count (more colors = more complex)
    avg_colors = sum(
        pa.input_analysis.num_colors for pa in report.pair_analyses
    ) / len(report.pair_analyses)
    if avg_colors > 6:
        score += 2
    elif avg_colors > 3:
        score += 1

    # Factor 3: Object count (more objects = harder to reason about)
    avg_objects = sum(
        pa.input_analysis.num_objects for pa in report.pair_analyses
    ) / len(report.pair_analyses)
    if avg_objects > 8:
        score += 3
    elif avg_objects > 3:
        score += 1

    # Factor 4: Shape changes (output size differs from input)
    any_shape_change = any(pa.shape_changed for pa in report.pair_analyses)
    if any_shape_change:
        score += 2

    # Factor 5: Color palette changes
    any_color_change = any(
        pa.colors_added or pa.colors_removed for pa in report.pair_analyses
    )
    if any_color_change:
        score += 1

    # Factor 6: Few consistent patterns found = harder
    if len(report.consistent_patterns) <= 1:
        score += 2

    # Classify
    if score <= 3:
        level = TaskComplexity.LOW
    elif score <= 7:
        level = TaskComplexity.MEDIUM
    else:
        level = TaskComplexity.HIGH

    params = TaskComplexity.PARAMS[level]
    logger.info(
        "Task %s complexity: %s (score=%d, hyp=%d, iter=%d)",
        report.task_id, level, score,
        params["max_hypotheses"], params["max_iterations"],
    )
    return level, params


def format_report_summary(report: PerceptionReport) -> str:
    """Format a perception report as human-readable text."""
    lines: list[str] = [
        f"Task: {report.task_id} ({report.num_pairs} training pairs)",
        "",
    ]

    for i, pa in enumerate(report.pair_analyses):
        lines.append(f"Pair {i + 1}:")
        lines.append(f"  Input:  {pa.input_analysis.shape}, "
                     f"{pa.input_analysis.num_colors} colors, "
                     f"{pa.input_analysis.num_objects} objects")
        lines.append(f"  Output: {pa.output_analysis.shape}, "
                     f"{pa.output_analysis.num_colors} colors, "
                     f"{pa.output_analysis.num_objects} objects")
        if pa.shape_changed:
            lines.append(f"  Shape changed: ratio {pa.size_ratio}")
        if pa.colors_added:
            lines.append(f"  Colors added: {pa.colors_added}")
        if pa.colors_removed:
            lines.append(f"  Colors removed: {pa.colors_removed}")

    if report.consistent_patterns:
        lines.append("")
        lines.append("Consistent patterns:")
        for p in report.consistent_patterns:
            lines.append(f"  - {p}")

    if report.llm_description:
        lines.append("")
        lines.append(f"LLM description: {report.llm_description}")

    return "\n".join(lines)
