"""ARC-AGI Few-Shot Context Builder.

Retrieves similar tasks from the similarity index and formats
their perception reports as context for hypothesis and synthesis prompts.

This bridges the task_similarity engine with the LLM prompt pipeline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loopagi.arc.perceiver import (
    PerceptionReport,
    format_report_summary,
    grid_to_compact,
    perceive_task,
)
from loopagi.arc.task_similarity import (
    SimilarTask,
    TaskIndex,
    find_similar_tasks,
)

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import ArcDataset, ArcTask

logger = logging.getLogger(__name__)


@dataclass
class FewShotExample:
    """A single few-shot example from a similar task."""

    task_id: str
    similarity: float
    perception_summary: str
    consistent_patterns: list[str]
    sample_pair: str = ""


@dataclass
class FewShotContext:
    """Collection of few-shot examples for prompt injection."""

    examples: list[FewShotExample] = field(default_factory=list)

    @property
    def num_examples(self) -> int:
        return len(self.examples)

    def format_for_hypothesis(self) -> str:
        """Format examples as context for the hypothesis prompt."""
        if not self.examples:
            return ""

        lines: list[str] = [
            "",
            "Similar tasks found (use as hints, not as answers):",
        ]
        for ex in self.examples:
            lines.append(f"  Task {ex.task_id} ({ex.similarity:.0%} similar):")
            if ex.consistent_patterns:
                patterns = ", ".join(ex.consistent_patterns[:4])
                lines.append(f"    Patterns: {patterns}")
            if ex.sample_pair:
                lines.append(f"    Sample:\n{ex.sample_pair}")
        return "\n".join(lines)

    def format_for_synthesis(self) -> str:
        """Format examples as context for the synthesis prompt."""
        if not self.examples:
            return ""

        lines: list[str] = [
            "",
            "Hints from similar tasks:",
        ]
        for ex in self.examples:
            if ex.consistent_patterns:
                patterns = ", ".join(ex.consistent_patterns[:3])
                lines.append(
                    f"  Similar task ({ex.similarity:.0%}): {patterns}"
                )
            if ex.sample_pair:
                lines.append(ex.sample_pair)
        return "\n".join(lines)


def build_few_shot_context(
    task: ArcTask,
    index: TaskIndex,
    dataset: ArcDataset | None = None,
    k: int = 3,
    include_grids: bool = True,
) -> FewShotContext:
    """Retrieve similar tasks and build few-shot context.

    Args:
        task: The query task to find similar tasks for.
        index: Pre-built task similarity index.
        dataset: Optional dataset to load full task data for grid examples.
        k: Number of similar tasks to retrieve.
        include_grids: If True and dataset is provided, include sample grids.

    Returns:
        FewShotContext with formatted examples.
    """
    similar = find_similar_tasks(task, index, k=k)
    context = FewShotContext()

    for sim in similar:
        example = FewShotExample(
            task_id=sim.task_id,
            similarity=sim.similarity,
            perception_summary="",
            consistent_patterns=[],
        )

        # If we have the dataset, load the full task and perceive it
        if dataset is not None:
            try:
                similar_task = dataset.get_task(sim.task_id)
                report = perceive_task(similar_task)
                example.perception_summary = format_report_summary(report)
                example.consistent_patterns = report.consistent_patterns

                # Include a compact sample pair
                if include_grids and similar_task.train:
                    pair = similar_task.train[0]
                    sample = (
                        f"      In: {grid_to_compact(pair.input)}\n"
                        f"      Out: {grid_to_compact(pair.output)}"
                    )
                    example.sample_pair = sample

            except (KeyError, IndexError):
                logger.warning(
                    "Could not load similar task %s from dataset",
                    sim.task_id,
                )
                continue
        else:
            # Without dataset, use feature-derived patterns
            f = sim.features
            if f.shape_changes:
                example.consistent_patterns.append("output_different_shape")
            else:
                example.consistent_patterns.append("output_same_shape_as_input")
            if f.colors_added > 0:
                example.consistent_patterns.append("adds_colors")
            if f.colors_removed > 0:
                example.consistent_patterns.append("removes_colors")
            if f.gains_symmetry:
                example.consistent_patterns.append("gains_symmetry")

        context.examples.append(example)

    logger.info(
        "Built few-shot context for %s: %d examples",
        task.task_id,
        context.num_examples,
    )
    return context
