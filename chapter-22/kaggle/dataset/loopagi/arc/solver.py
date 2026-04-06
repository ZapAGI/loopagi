"""ARC-AGI Multi-Agent Solver.

Orchestrates the 5 specialist agents in a refinement loop:
Perceive -> Hypothesize -> Synthesize -> Verify -> Refine

This is the core of the book's thesis: intelligence emerges from
orchestrated specialists, not from a single monolithic model.
"""

from __future__ import annotations

import logging
import signal
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loopagi.arc.hypothesizer import Hypothesis, HypothesisSet, hypothesize
from loopagi.arc.perceiver import PerceptionReport, perceive_task
from loopagi.arc.refiner import RefinementPlan, refine
from loopagi.arc.synthesizer import (
    SynthesizedProgram,
    synthesize_from_hypothesis,
    synthesize_identity,
)
from loopagi.arc.verifier import VerificationResult, verify_program

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import ArcTask, Grid

logger = logging.getLogger(__name__)


@dataclass
class SolveIteration:
    """Record of one iteration of the refinement loop."""

    iteration: int
    hypothesis: Hypothesis
    program: SynthesizedProgram
    verification: VerificationResult
    refinement: RefinementPlan | None = None
    elapsed_seconds: float = 0.0


@dataclass
class SolveResult:
    """Complete result of attempting to solve an ARC task."""

    task_id: str
    solved: bool = False
    predictions: list[list[Grid]] = field(default_factory=list)
    iterations: list[SolveIteration] = field(default_factory=list)
    best_program: SynthesizedProgram | None = None
    best_similarity: float = 0.0
    total_seconds: float = 0.0

    @property
    def num_iterations(self) -> int:
        # _num_iterations_final is set by solve_task_with_llm when it
        # clears iterations to free memory during long eval runs.
        return getattr(self, "_num_iterations_final", len(self.iterations))

    def summary(self) -> str:
        status = "SOLVED" if self.solved else "UNSOLVED"
        lines = [
            f"Task {self.task_id}: {status}",
            f"  Iterations: {self.num_iterations}",
            f"  Best similarity: {self.best_similarity:.1%}",
            f"  Time: {self.total_seconds:.1f}s",
        ]
        if self.best_program:
            lines.append(f"  Best hypothesis: {self.best_program.hypothesis[:80]}")
        return "\n".join(lines)


def _extract_train_pairs(task: ArcTask) -> list[tuple[Grid, Grid]]:
    """Extract (input, output) tuples from training pairs."""
    return [(p.input, p.output) for p in task.train]


# Timeout (seconds) for executing LLM-generated code on test inputs.
_TEST_EXEC_TIMEOUT = 30


def _apply_program_to_tests(
    program: SynthesizedProgram,
    task: ArcTask,
    max_attempts: int = 2,
) -> list[list[Grid]]:
    """Apply a verified program to test inputs.

    Uses SIGALRM to prevent infinite loops in LLM-generated code.
    """
    def _alarm_handler(signum: int, frame: object) -> None:
        raise TimeoutError("transform() timed out")

    namespace: dict = {}
    try:
        exec(program.source_code, namespace)
    except Exception:
        return []

    transform_fn = namespace.get("transform")
    if not callable(transform_fn):
        return []

    predictions: list[list[Grid]] = []
    for test in task.test:
        attempts: list[Grid] = []
        old_handler = signal.getsignal(signal.SIGALRM)
        try:
            signal.signal(signal.SIGALRM, _alarm_handler)
            signal.alarm(_TEST_EXEC_TIMEOUT)
            result = transform_fn(test.input)
            if isinstance(result, list) and result and isinstance(result[0], list):
                attempts.append(result)
        except Exception:
            pass
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
        # Pad to max_attempts with copies
        while len(attempts) < max_attempts and attempts:
            attempts.append(attempts[0])
        if not attempts:
            attempts = [test.input]  # Fallback to identity
        predictions.append(attempts[:max_attempts])

    return predictions


def solve_task(
    task: ArcTask,
    max_hypotheses: int = 5,
    max_iterations: int = 10,
    max_attempts: int = 2,
    llm_callback: object | None = None,
) -> SolveResult:
    """Solve an ARC task using the multi-agent refinement loop.

    Args:
        task: The ARC task to solve.
        max_hypotheses: Number of hypotheses to generate per perception.
        max_iterations: Max refinement iterations per hypothesis.
        max_attempts: Number of prediction attempts per test input.
        llm_callback: Optional callable(prompt: str) -> str for LLM calls.

    Returns:
        SolveResult with predictions and iteration history.
    """
    start_time = time.monotonic()
    result = SolveResult(task_id=task.task_id)
    train_pairs = _extract_train_pairs(task)

    # Phase 1: Perceive
    logger.info("Perceiving task %s...", task.task_id)
    report = perceive_task(task)

    # Phase 2: Hypothesize
    logger.info("Generating hypotheses...")
    hyp_set = hypothesize(report, max_hypotheses=max_hypotheses)

    if not hyp_set.hypotheses:
        logger.warning("No hypotheses generated for task %s", task.task_id)
        result.total_seconds = time.monotonic() - start_time
        return result

    best_program: SynthesizedProgram | None = None
    best_sim = 0.0

    # Try each hypothesis with refinement
    for hypothesis in hyp_set.ranked():
        current_hyp = hypothesis

        for iteration in range(max_iterations):
            iter_start = time.monotonic()

            # Phase 3: Synthesize
            program = synthesize_from_hypothesis(current_hyp)

            # Phase 4: Verify
            verification = verify_program(program, train_pairs)

            # Track best result
            if verification.avg_similarity > best_sim:
                best_sim = verification.avg_similarity
                best_program = program

            iter_record = SolveIteration(
                iteration=iteration,
                hypothesis=current_hyp,
                program=program,
                verification=verification,
                elapsed_seconds=time.monotonic() - iter_start,
            )

            # Check if solved
            if verification.all_pass:
                logger.info(
                    "SOLVED task %s on iteration %d with: %s",
                    task.task_id, iteration, current_hyp.rule[:80],
                )
                result.solved = True
                result.best_program = program
                result.best_similarity = 1.0
                result.predictions = _apply_program_to_tests(
                    program, task, max_attempts
                )
                result.iterations.append(iter_record)
                result.total_seconds = time.monotonic() - start_time
                return result

            # Phase 5: Refine
            plan = refine(
                task.task_id, verification, current_hyp,
                iteration, max_iterations,
            )
            iter_record.refinement = plan
            result.iterations.append(iter_record)

            if plan.should_abandon:
                logger.info("Abandoning hypothesis: %s", plan.abandon_reason)
                break

            # Apply refinement: use the new hypothesis if available
            refined_hyp = None
            for action in plan.actions:
                if action.new_hypothesis is not None:
                    refined_hyp = action.new_hypothesis
                    break

            if refined_hyp:
                current_hyp = refined_hyp
            else:
                break  # No refinement possible, try next hypothesis

    # No hypothesis solved the task; return best attempt
    result.best_program = best_program
    result.best_similarity = best_sim

    if best_program:
        result.predictions = _apply_program_to_tests(
            best_program, task, max_attempts
        )

    result.total_seconds = time.monotonic() - start_time
    logger.info(
        "Task %s unsolved after %d iterations (best sim: %.1f%%)",
        task.task_id, result.num_iterations, best_sim * 100,
    )
    return result


class MultiAgentArcSolver:
    """ArcSolver implementation using the multi-agent refinement loop.

    Compatible with the ArcSolver Protocol from arc_runner.py.
    """

    def __init__(
        self,
        max_hypotheses: int = 5,
        max_iterations: int = 10,
        llm_callback: object | None = None,
    ) -> None:
        self._max_hypotheses = max_hypotheses
        self._max_iterations = max_iterations
        self._llm_callback = llm_callback

    @property
    def name(self) -> str:
        return "multi_agent"

    def solve(
        self, task: ArcTask, max_attempts: int = 2
    ) -> list[list[Grid]]:
        """Solve an ARC task, returning predictions for test inputs."""
        result = solve_task(
            task,
            max_hypotheses=self._max_hypotheses,
            max_iterations=self._max_iterations,
            max_attempts=max_attempts,
            llm_callback=self._llm_callback,
        )
        if result.predictions:
            return result.predictions
        # Fallback: return test inputs unchanged
        return [[t.input] * max_attempts for t in task.test]
