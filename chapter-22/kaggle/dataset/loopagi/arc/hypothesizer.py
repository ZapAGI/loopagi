"""ARC-AGI Hypothesizer Agent.

Takes a PerceptionReport and generates multiple candidate transformation
hypotheses as natural language rules, ranked by specificity and coverage.

The Hypothesizer is the second step in the refinement loop:
Perceive -> Hypothesize -> Synthesize -> Verify -> Refine
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from loopagi.arc.perceiver import PerceptionReport

logger = logging.getLogger(__name__)


@dataclass
class Hypothesis:
    """A single candidate transformation hypothesis."""

    rule: str
    confidence: float = 0.5
    source: str = "pattern_match"
    refinement_notes: str = ""

    def summary(self) -> str:
        return f"[{self.confidence:.0%}] {self.rule}"


@dataclass
class HypothesisSet:
    """A ranked set of hypotheses for a task."""

    task_id: str
    hypotheses: list[Hypothesis] = field(default_factory=list)

    @property
    def best(self) -> Hypothesis | None:
        if not self.hypotheses:
            return None
        return max(self.hypotheses, key=lambda h: h.confidence)

    def ranked(self) -> list[Hypothesis]:
        return sorted(self.hypotheses, key=lambda h: h.confidence, reverse=True)

    def summary(self) -> str:
        lines = [f"Hypotheses for {self.task_id} ({len(self.hypotheses)} candidates):"]
        for h in self.ranked():
            lines.append(f"  {h.summary()}")
        return "\n".join(lines)


def generate_pattern_hypotheses(report: PerceptionReport) -> list[Hypothesis]:
    """Generate hypotheses from deterministic pattern analysis."""
    hypotheses: list[Hypothesis] = []
    patterns = report.consistent_patterns

    # Shape-based hypotheses
    if "output_same_shape_as_input" in patterns:
        hypotheses.append(Hypothesis(
            rule="The output grid has the same dimensions as the input grid. "
                 "The transformation modifies cell values in place.",
            confidence=0.7,
            source="shape_analysis",
        ))

    for p in patterns:
        if p.startswith("consistent_size_ratio_"):
            ratio = p.replace("consistent_size_ratio_", "")
            hypotheses.append(Hypothesis(
                rule=f"The output grid is scaled by a factor of {ratio} "
                     f"relative to the input grid.",
                confidence=0.8,
                source="shape_analysis",
            ))

    # Color-based hypotheses
    if "same_color_palette" in patterns:
        hypotheses.append(Hypothesis(
            rule="The transformation preserves all colors. "
                 "No colors are added or removed.",
            confidence=0.6,
            source="color_analysis",
        ))

    for p in patterns:
        if p.startswith("always_adds_colors_"):
            colors = p.replace("always_adds_colors_", "")
            hypotheses.append(Hypothesis(
                rule=f"The transformation introduces new color(s): {colors}.",
                confidence=0.7,
                source="color_analysis",
            ))
        if p.startswith("always_removes_colors_"):
            colors = p.replace("always_removes_colors_", "")
            hypotheses.append(Hypothesis(
                rule=f"The transformation removes color(s): {colors}.",
                confidence=0.7,
                source="color_analysis",
            ))

    # Object-based hypotheses
    if "same_object_count" in patterns:
        hypotheses.append(Hypothesis(
            rule="The number of objects is preserved. "
                 "Objects may be moved, recolored, or transformed in place.",
            confidence=0.6,
            source="object_analysis",
        ))

    for p in patterns:
        if p.startswith("adds_") and p.endswith("_objects"):
            n = p.replace("adds_", "").replace("_objects", "")
            hypotheses.append(Hypothesis(
                rule=f"The transformation adds {n} new object(s) to the grid.",
                confidence=0.6,
                source="object_analysis",
            ))
        if p.startswith("removes_") and p.endswith("_objects"):
            n = p.replace("removes_", "").replace("_objects", "")
            hypotheses.append(Hypothesis(
                rule=f"The transformation removes {n} object(s) from the grid.",
                confidence=0.6,
                source="object_analysis",
            ))

    # Symmetry-based hypotheses
    for p in patterns:
        if p.startswith("output_gains_") and p.endswith("_symmetry"):
            sym = p.replace("output_gains_", "").replace("_symmetry", "")
            hypotheses.append(Hypothesis(
                rule=f"The transformation makes the grid {sym}ly symmetric.",
                confidence=0.8,
                source="symmetry_analysis",
            ))

    # Background hypotheses
    if "same_background" in patterns:
        hypotheses.append(Hypothesis(
            rule="The background color is preserved in the output.",
            confidence=0.5,
            source="background_analysis",
        ))

    return hypotheses


def format_hypothesis_prompt(
    report: PerceptionReport,
    similar_context: str = "",
) -> str:
    """Format a prompt asking an LLM to generate hypotheses.

    Uses the perception report's patterns and pair analyses as context.
    Optionally includes few-shot context from similar tasks.

    Args:
        report: The perception report for the task.
        similar_context: Optional formatted context from similar tasks.
    """
    from loopagi.arc.perceiver import format_report_summary

    lines: list[str] = [
        "Based on this ARC-AGI task analysis, generate 3-5 candidate "
        "transformation rules. Each rule should be a clear, testable "
        "statement describing how to convert any input grid to its output.",
        "",
        format_report_summary(report),
    ]

    if similar_context:
        lines.append(similar_context)

    lines.extend([
        "",
        "For each hypothesis, provide:",
        "1. A natural language rule (one sentence)",
        "2. A confidence score (0.0 to 1.0)",
        "3. What evidence supports this rule",
        "",
        "Format each hypothesis as:",
        "RULE: <description>",
        "CONFIDENCE: <0.0-1.0>",
        "EVIDENCE: <what supports this>",
    ])
    return "\n".join(lines)


def parse_llm_hypotheses(llm_response: str) -> list[Hypothesis]:
    """Parse LLM-generated hypotheses from a structured response."""
    hypotheses: list[Hypothesis] = []
    current_rule = ""
    current_confidence = 0.5

    for line in llm_response.split("\n"):
        line = line.strip()
        if line.upper().startswith("RULE:"):
            if current_rule:
                hypotheses.append(Hypothesis(
                    rule=current_rule,
                    confidence=current_confidence,
                    source="llm",
                ))
            current_rule = line[5:].strip()
            current_confidence = 0.5
        elif line.upper().startswith("CONFIDENCE:"):
            try:
                val = float(line[11:].strip())
                current_confidence = max(0.0, min(1.0, val))
            except ValueError:
                current_confidence = 0.5

    if current_rule:
        hypotheses.append(Hypothesis(
            rule=current_rule,
            confidence=current_confidence,
            source="llm",
        ))

    return hypotheses


def hypothesize(
    report: PerceptionReport,
    llm_response: str = "",
    max_hypotheses: int = 5,
) -> HypothesisSet:
    """Generate a ranked set of hypotheses for a task.

    Combines deterministic pattern hypotheses with optional LLM-generated ones.

    Args:
        report: The perception report from the Perceiver.
        llm_response: Optional LLM response with additional hypotheses.
        max_hypotheses: Maximum number of hypotheses to return.

    Returns:
        HypothesisSet with ranked candidates.
    """
    pattern_hyps = generate_pattern_hypotheses(report)
    llm_hyps = parse_llm_hypotheses(llm_response) if llm_response else []

    all_hyps = pattern_hyps + llm_hyps
    all_hyps.sort(key=lambda h: h.confidence, reverse=True)

    result = HypothesisSet(
        task_id=report.task_id,
        hypotheses=all_hyps[:max_hypotheses],
    )

    logger.info(
        "Generated %d hypotheses for task %s (from %d pattern + %d LLM)",
        len(result.hypotheses),
        report.task_id,
        len(pattern_hyps),
        len(llm_hyps),
    )
    return result
