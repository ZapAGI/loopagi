"""
Chapter 6: Agent Pool Demo

Three coders working simultaneously. Each a parallel instance.
The metaphysics of identity when you have three copies of the same agent.

Parallel minds are not copies. They are perspectives.

Prerequisites:
    ollama pull llama3.2
"""

from __future__ import annotations

from loopagi.core.pool import AgentPool


def demo_parallel_execution() -> None:
    """Execute multiple tasks in parallel across pool agents."""
    print("Chapter 6: Agent Pools - Parallel Execution")
    print("=" * 60)

    pool = AgentPool(
        name="coder",
        role=(
            "You are a Python coder. Write a single function that solves "
            "the given task. Output ONLY the function, no explanations. "
            "Keep it under 10 lines."
        ),
        size=3,
        model="llama3.2",
    )
    print(f"Created: {pool}")
    print()

    tasks = [
        "Write a function to reverse a string",
        "Write a function to find the maximum in a list",
        "Write a function to count vowels in a string",
    ]

    print("Executing 3 tasks across 3 agents in parallel...")
    results = pool.execute_parallel(tasks)

    for result in results:
        status = "OK" if result.success else f"FAIL: {result.error}"
        print(f"\n[{result.agent_name}] Task: {result.task[:50]}")
        print(f"Status: {status}")
        if result.success:
            print(result.response[:200])
        print("-" * 40)


def demo_consensus() -> None:
    """Ask all agents the same question, compare answers."""
    print("\n\nConsensus Pattern: Same Question, Multiple Perspectives")
    print("=" * 60)

    pool = AgentPool(
        name="advisor",
        role=(
            "You are a software architecture advisor. Give concise advice "
            "in 2-3 sentences. Each answer should reflect your unique perspective."
        ),
        size=3,
        model="llama3.2",
    )

    question = "Should we use microservices or a monolith for a new project?"
    print(f"\nQuestion: {question}\n")

    best = pool.execute_consensus(question)
    print("Selected response (longest/most detailed):")
    print(best[:300])
    print()
    print("Three minds, one question, three perspectives.")
    print("The best answer emerges from the collective.")


if __name__ == "__main__":
    demo_parallel_execution()
    demo_consensus()
