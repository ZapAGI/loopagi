"""
Chapter 7: The Reviewer Feedback Loop

Demonstrates the feedback loop where the reviewer sends code
back for revision. This is the first loop of machine
self-improvement: when the evaluator develops standards.

This example uses simulated agents (no Ollama required) to
show the feedback mechanism clearly.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class CodeSubmission:
    """A piece of code submitted for review."""

    code: str
    quality_score: float  # 0.0 to 1.0
    issues: list[str] = field(default_factory=list)
    iteration: int = 0


QUALITY_CRITERIA = [
    ("type_hints", "Missing type hints on function parameters"),
    ("docstring", "Missing docstring"),
    ("error_handling", "No error handling for edge cases"),
    ("naming", "Variable names not descriptive"),
    ("testing", "No tests provided"),
    ("dry", "Duplicated logic that should be extracted"),
    ("complexity", "Function too long, should be decomposed"),
    ("security", "User input not validated"),
]


def simulate_coder(task: str, feedback: str = "", iteration: int = 0) -> CodeSubmission:
    """
    Simulate a coder agent producing code.

    With each iteration, the coder improves based on feedback.
    The improvement is probabilistic: each issue has a chance
    of being fixed based on how specific the feedback is.
    """
    random.seed(42 + iteration)

    # Base quality improves with iterations (learning from feedback)
    base_quality = min(0.4 + (iteration * 0.15), 0.95)

    issues = []
    for criterion, description in QUALITY_CRITERIA:
        # Each criterion has a chance of being an issue
        threshold = base_quality + (0.1 if criterion in feedback else 0)
        if random.random() > threshold:
            issues.append(description)

    quality = 1.0 - (len(issues) / len(QUALITY_CRITERIA))
    return CodeSubmission(
        code=f"# Implementation for: {task} (iteration {iteration})",
        quality_score=quality,
        issues=issues,
        iteration=iteration,
    )


def simulate_reviewer(submission: CodeSubmission) -> tuple[bool, str]:
    """
    Simulate a reviewer agent evaluating code.

    Returns (approved, feedback_text).
    The reviewer has a quality threshold of 0.75.
    """
    threshold = 0.75

    if submission.quality_score >= threshold:
        return True, (
            f"APPROVED (score: {submission.quality_score:.2f})."
            " Code meets quality standards."
        )

    feedback_lines = [f"REVISION NEEDED (score: {submission.quality_score:.2f})"]
    feedback_lines.append(f"Issues found ({len(submission.issues)}):")
    for issue in submission.issues:
        feedback_lines.append(f"  - {issue}")
    feedback_lines.append("Fix these issues and resubmit.")

    return False, "\n".join(feedback_lines)


def demo() -> None:
    """Demonstrate the quality pipeline feedback loop."""
    print("Chapter 7: The Reviewer Feedback Loop")
    print("=" * 60)

    task = "Implement a user authentication module"
    max_iterations = 5

    print(f"\nTask: {task}")
    print("Quality threshold: 0.75")
    print(f"Max iterations: {max_iterations}")
    print("-" * 60)

    feedback = ""
    for iteration in range(max_iterations):
        # Coder produces code
        submission = simulate_coder(task, feedback, iteration)
        print(f"\n  Iteration {iteration + 1}:")
        print(f"  [coder] Submitted (quality: {submission.quality_score:.2f})")
        if submission.issues:
            print(f"  Issues: {len(submission.issues)}")

        # Reviewer evaluates
        approved, feedback = simulate_reviewer(submission)

        if approved:
            print(f"  [reviewer] {feedback}")
            print(f"\n  APPROVED after {iteration + 1} iteration(s)!")
            break
        else:
            print(f"  [reviewer] REVISION NEEDED ({len(submission.issues)} issues)")
            for issue in submission.issues:
                print(f"    - {issue}")

    # Show improvement trajectory
    print("\n\nImprovement Trajectory:")
    print("-" * 40)
    print(f"  {'Iteration':<12} {'Quality':<10} {'Issues':<10} {'Status'}")
    print(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*10}")

    for i in range(iteration + 1):
        sub = simulate_coder(task, "", i)
        status = "APPROVED" if sub.quality_score >= 0.75 else "needs work"
        bar = "X" * int(sub.quality_score * 20)
        print(f"  {i + 1:<12} {sub.quality_score:<10.2f} {len(sub.issues):<10} {bar} {status}")

    print()
    print("The feedback loop is the first loop of machine self-improvement.")
    print("Quality is not a checkpoint. It is a conversation between agents.")


if __name__ == "__main__":
    demo()
