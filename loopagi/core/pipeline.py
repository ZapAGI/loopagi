"""
Chapter 7: The Quality Pipeline

Plan, Code, Test, Review: the assembly line of thought.
Quality is not a checkpoint. It is a conversation between agents.

Usage:
    from loopagi.core.pipeline import QualityPipeline

    pipeline = QualityPipeline()
    result = pipeline.run("Create a Python function that validates email addresses")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

from loopagi.core.agent import Agent

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    """Stages of the quality pipeline."""

    PLAN = "plan"
    CODE = "code"
    TEST = "test"
    REVIEW = "review"


@dataclass
class StageResult:
    """Output from a single pipeline stage."""

    stage: PipelineStage
    agent_name: str
    output: str
    passed: bool = True
    feedback: str = ""


@dataclass
class PipelineResult:
    """Complete output from the quality pipeline."""

    task: str
    stages: list[StageResult] = field(default_factory=list)
    final_code: str = ""
    iterations: int = 0
    success: bool = False

    @property
    def summary(self) -> str:
        stage_status = " -> ".join(
            f"{s.stage.value}:{'PASS' if s.passed else 'FAIL'}" for s in self.stages
        )
        return f"Pipeline [{stage_status}] iterations={self.iterations} success={self.success}"


class QualityPipeline:
    """
    Four-stage quality pipeline: Plan -> Code -> Test -> Review.

    Each agent's output feeds the next. The reviewer can send work
    back for revision, creating a feedback loop. This is the first
    loop of machine self-improvement: when the tester discovers an
    opportunity the coder missed.

    The question of standards: who decides what "good" looks like
    when the evaluator is also a machine?
    """

    def __init__(self, model: str = "llama3.2", max_iterations: int = 3) -> None:
        self.max_iterations = max_iterations

        self.planner = Agent(
            name="planner",
            role=(
                "You are a software architect. Given a task, create a clear, "
                "step-by-step implementation plan. Include: function signatures, "
                "data structures, edge cases to handle, and testing strategy. "
                "Output ONLY the plan, no code."
            ),
            model=model,
        )
        self.coder = Agent(
            name="coder",
            role=(
                "You are a Python coding specialist. Given a plan, write clean, "
                "well-documented Python code that implements it exactly. Use type "
                "hints, docstrings, and follow PEP 8. Output ONLY the Python code "
                "in a single code block."
            ),
            model=model,
        )
        self.tester = Agent(
            name="tester",
            role=(
                "You are a testing specialist. Given Python code, write comprehensive "
                "pytest tests that cover: happy path, edge cases, error conditions, "
                "and boundary values. Output ONLY the test code in a single code block."
            ),
            model=model,
        )
        self.reviewer = Agent(
            name="reviewer",
            role=(
                "You are a senior code reviewer. Given code and tests, evaluate: "
                "correctness, style, edge case coverage, performance, and security. "
                "If the code passes review, respond with 'APPROVED' on the first line "
                "followed by any positive notes. If it needs changes, respond with "
                "'REVISION NEEDED' on the first line followed by specific actionable feedback."
            ),
            model=model,
        )
        logger.info("QualityPipeline initialized (max_iterations=%d)", max_iterations)

    def run(self, task: str) -> PipelineResult:
        """
        Run the full quality pipeline for a task.

        Returns a PipelineResult with all stage outputs and the final code.
        """
        result = PipelineResult(task=task)

        for iteration in range(1, self.max_iterations + 1):
            result.iterations = iteration
            logger.info(
                "Pipeline iteration %d/%d for: %s",
                iteration, self.max_iterations, task[:60],
            )

            # Stage 1: Plan
            if iteration == 1:
                plan_output = self.planner.invoke(
                    f"Create an implementation plan for:\n{task}"
                )
                result.stages.append(StageResult(
                    stage=PipelineStage.PLAN,
                    agent_name=self.planner.name,
                    output=plan_output,
                ))
            else:
                # On revision, include reviewer feedback in the plan
                last_review = result.stages[-1]
                plan_output = self.planner.invoke(
                    f"Revise the plan based on reviewer feedback:\n\n"
                    f"Original task: {task}\n\n"
                    f"Feedback: {last_review.feedback}"
                )
                result.stages.append(StageResult(
                    stage=PipelineStage.PLAN,
                    agent_name=self.planner.name,
                    output=plan_output,
                ))

            # Stage 2: Code
            code_output = self.coder.invoke(
                f"Implement this plan:\n\n{plan_output}"
            )
            result.stages.append(StageResult(
                stage=PipelineStage.CODE,
                agent_name=self.coder.name,
                output=code_output,
            ))
            result.final_code = code_output

            # Stage 3: Test
            test_output = self.tester.invoke(
                f"Write tests for this code:\n\n{code_output}"
            )
            result.stages.append(StageResult(
                stage=PipelineStage.TEST,
                agent_name=self.tester.name,
                output=test_output,
            ))

            # Stage 4: Review
            review_output = self.reviewer.invoke(
                f"Review this code and tests:\n\nCode:\n{code_output}\n\nTests:\n{test_output}"
            )
            approved = review_output.strip().upper().startswith("APPROVED")
            result.stages.append(StageResult(
                stage=PipelineStage.REVIEW,
                agent_name=self.reviewer.name,
                output=review_output,
                passed=approved,
                feedback=review_output if not approved else "",
            ))

            if approved:
                result.success = True
                logger.info("Pipeline APPROVED on iteration %d", iteration)
                break
            else:
                logger.info("Pipeline REVISION NEEDED (iteration %d)", iteration)

        if not result.success:
            logger.warning(
                "Pipeline did not achieve APPROVED after %d iterations",
                self.max_iterations,
            )

        return result

    def __repr__(self) -> str:
        return f"QualityPipeline(max_iterations={self.max_iterations})"
