"""ARC-AGI Refiner Agent.

Analyzes verification failures and produces refined hypotheses
or code fixes to improve the next iteration of the refinement loop.

The Refiner is the fifth step in the refinement loop:
Perceive -> Hypothesize -> Synthesize -> Verify -> Refine
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from loopagi.arc.hypothesizer import Hypothesis
from loopagi.arc.verifier import VerificationResult, format_grid_diff

logger = logging.getLogger(__name__)


@dataclass
class RefinementAction:
    """A suggested action to improve the hypothesis or code."""

    action_type: str  # "refine_hypothesis", "fix_code", "try_different_approach"
    description: str
    new_hypothesis: Hypothesis | None = None
    code_fix: str = ""
    priority: float = 0.5

    def summary(self) -> str:
        return f"[{self.action_type}] {self.description}"


@dataclass
class RefinementPlan:
    """A plan of actions to refine the current approach."""

    task_id: str
    iteration: int
    actions: list[RefinementAction]
    should_abandon: bool = False
    abandon_reason: str = ""

    def summary(self) -> str:
        if self.should_abandon:
            return f"ABANDON: {self.abandon_reason}"
        lines = [f"Refinement plan (iteration {self.iteration}):"]
        for a in self.actions:
            lines.append(f"  - {a.summary()}")
        return "\n".join(lines)


def diagnose_failures(result: VerificationResult) -> list[str]:
    """Analyze verification failures and identify error patterns.

    Returns a list of diagnostic observations.
    """
    diagnostics: list[str] = []

    if result.compile_error:
        diagnostics.append(f"Code does not compile: {result.compile_error}")
        return diagnostics

    if not result.pair_results:
        diagnostics.append("No pair results available")
        return diagnostics

    # Check for shape mismatches
    shape_mismatches = [
        r for r in result.pair_results
        if not r.passed and not r.shape_correct
    ]
    if shape_mismatches:
        diagnostics.append(
            f"Shape mismatch in {len(shape_mismatches)} pair(s): "
            f"expected {shape_mismatches[0].expected_shape}, "
            f"got {shape_mismatches[0].actual_shape}"
        )

    # Check for runtime errors
    runtime_errors = [r for r in result.pair_results if r.error]
    if runtime_errors:
        unique_errors = set(r.error.split(":")[0] for r in runtime_errors)
        diagnostics.append(
            f"Runtime errors in {len(runtime_errors)} pair(s): "
            f"{', '.join(unique_errors)}"
        )

    # Check partial correctness
    partial = [r for r in result.pair_results if not r.passed and r.similarity > 0.5]
    if partial:
        avg_sim = sum(r.similarity for r in partial) / len(partial)
        diagnostics.append(
            f"{len(partial)} pair(s) are partially correct "
            f"(avg similarity: {avg_sim:.0%}): hypothesis is close but incomplete"
        )

    # Check if any pairs pass
    if result.num_passed > 0:
        diagnostics.append(
            f"{result.num_passed}/{result.num_total} pairs pass: "
            f"hypothesis works for some cases but not all"
        )

    # Zero similarity
    zero_sim = [r for r in result.pair_results if r.similarity == 0.0 and not r.error]
    if zero_sim:
        diagnostics.append(
            f"{len(zero_sim)} pair(s) have zero similarity: "
            f"hypothesis may be fundamentally wrong"
        )

    return diagnostics


def suggest_refinements(
    result: VerificationResult,
    hypothesis: Hypothesis,
    iteration: int,
) -> list[RefinementAction]:
    """Generate refinement actions based on verification results."""
    actions: list[RefinementAction] = []
    diagnostics = diagnose_failures(result)

    # Compile error: fix the code
    if result.compile_error:
        actions.append(RefinementAction(
            action_type="fix_code",
            description=f"Fix compile error: {result.compile_error}",
            priority=1.0,
        ))
        return actions

    # Runtime errors: fix the code
    runtime_errors = [r for r in result.pair_results if r.error]
    if runtime_errors:
        actions.append(RefinementAction(
            action_type="fix_code",
            description=f"Fix runtime error: {runtime_errors[0].error[:100]}",
            priority=0.9,
        ))

    # Shape mismatch: refine hypothesis about output dimensions
    shape_mismatches = [
        r for r in result.pair_results if not r.shape_correct
    ]
    if shape_mismatches:
        m = shape_mismatches[0]
        actions.append(RefinementAction(
            action_type="refine_hypothesis",
            description=(
                f"Output shape is wrong (expected {m.expected_shape}, "
                f"got {m.actual_shape}). Revise the size/dimension rule."
            ),
            new_hypothesis=Hypothesis(
                rule=(
                    f"{hypothesis.rule} "
                    f"[REFINED: output should be {m.expected_shape[0]}x{m.expected_shape[1]}]"
                ),
                confidence=hypothesis.confidence * 0.8,
                source="refiner",
                refinement_notes=f"Shape correction from iteration {iteration}",
            ),
            priority=0.8,
        ))

    # Partial correctness: the hypothesis is close
    if result.avg_similarity > 0.5 and not result.all_pass:
        failing = [r for r in result.pair_results if not r.passed]
        actions.append(RefinementAction(
            action_type="refine_hypothesis",
            description=(
                f"Hypothesis is partially correct ({result.avg_similarity:.0%} avg similarity). "
                f"Focus on the {len(failing)} failing pair(s)."
            ),
            new_hypothesis=Hypothesis(
                rule=(
                    f"{hypothesis.rule} "
                    f"[REFINED: check edge cases in {len(failing)} failing pairs]"
                ),
                confidence=hypothesis.confidence * 0.9,
                source="refiner",
                refinement_notes=f"Partial refinement from iteration {iteration}",
            ),
            priority=0.7,
        ))

    # Zero similarity: try a different approach
    if result.avg_similarity < 0.1:
        actions.append(RefinementAction(
            action_type="try_different_approach",
            description="Hypothesis produces completely wrong output. Try a different rule.",
            priority=0.6,
        ))

    return actions


def refine(
    task_id: str,
    result: VerificationResult,
    hypothesis: Hypothesis,
    iteration: int,
    max_iterations: int = 10,
) -> RefinementPlan:
    """Produce a refinement plan based on verification results.

    Args:
        task_id: The ARC task ID.
        result: Verification results from the current iteration.
        hypothesis: The hypothesis that was tested.
        iteration: Current iteration number.
        max_iterations: Maximum allowed iterations.

    Returns:
        RefinementPlan with suggested actions.
    """
    if result.all_pass:
        return RefinementPlan(
            task_id=task_id,
            iteration=iteration,
            actions=[],
        )

    if iteration >= max_iterations:
        return RefinementPlan(
            task_id=task_id,
            iteration=iteration,
            actions=[],
            should_abandon=True,
            abandon_reason=f"Max iterations ({max_iterations}) reached",
        )

    actions = suggest_refinements(result, hypothesis, iteration)

    plan = RefinementPlan(
        task_id=task_id,
        iteration=iteration,
        actions=sorted(actions, key=lambda a: a.priority, reverse=True),
    )

    logger.info(
        "Refinement plan for %s (iter %d): %d actions",
        task_id,
        iteration,
        len(actions),
    )
    return plan


def format_refinement_prompt(
    result: VerificationResult,
    hypothesis: Hypothesis,
    diagnostics: list[str],
) -> str:
    """Format a prompt for an LLM to refine a hypothesis.

    Provides the failure report, cell-level grid diffs, and
    diagnostics as context so the LLM can see exactly what is wrong.
    """
    lines: list[str] = [
        "The following ARC-AGI transformation hypothesis failed verification.",
        "Analyze the failures and suggest an improved hypothesis.",
        "",
        f"Current hypothesis: {hypothesis.rule}",
        "",
        result.failure_report(),
        "",
        "Diagnostics:",
    ]
    for d in diagnostics:
        lines.append(f"  - {d}")
    lines.extend([
        "",
        "Provide a revised hypothesis that fixes the failures.",
        "Focus on the wrong cells shown above (X marks).",
        "Format:",
        "RULE: <improved description>",
        "CONFIDENCE: <0.0-1.0>",
        "FIX: <what specifically needs to change>",
    ])
    return "\n".join(lines)
