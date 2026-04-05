"""
Chapter 7: Quality Pipeline Demo

Plan -> Code -> Test -> Review: the assembly line of thought.
Quality is not a checkpoint. It is a conversation between agents.

Prerequisites:
    ollama pull llama3.2
"""

from __future__ import annotations

from loopagi.core.pipeline import QualityPipeline


def demo() -> None:
    """Run the quality pipeline on a real coding task."""
    print("Chapter 7: The Quality Pipeline")
    print("=" * 60)
    print("Stages: Plan -> Code -> Test -> Review")
    print()

    pipeline = QualityPipeline(model="llama3.2", max_iterations=2)

    task = (
        "Create a Python class called Stack that implements a stack"
        " data structure with push, pop, peek, is_empty, and size methods."
    )

    print(f"Task: {task}")
    print()
    print("Running pipeline...")
    print("-" * 60)

    result = pipeline.run(task)

    print(f"\n{result.summary}")
    print(f"\nIterations: {result.iterations}")
    print(f"Success: {result.success}")

    # Show each stage
    for stage in result.stages:
        print(f"\n{'=' * 40}")
        print(f"Stage: {stage.stage.value.upper()} [{stage.agent_name}]")
        print(f"Passed: {stage.passed}")
        print(f"{'=' * 40}")
        # Show first 300 chars of output
        print(stage.output[:300])
        if len(stage.output) > 300:
            print(f"... ({len(stage.output)} chars total)")

    print(f"\n{'=' * 60}")
    print("The quality pipeline demonstrates that quality is not a")
    print("single evaluation. It is a conversation between specialists.")


if __name__ == "__main__":
    demo()
