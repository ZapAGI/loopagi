"""
Chapter 5: Hierarchical Routing Demo

Master agent routes tasks to specialist Workers.
Two-phase routing: fast keyword matching, then LLM fallback.

Hierarchy is not authority. It is the architecture of
efficient coordination.

Prerequisites:
    ollama pull llama3.2
"""

from __future__ import annotations

from loopagi.core.agent import Agent
from loopagi.core.router import ROUTING_PATTERNS, Router


def demo_keyword_routing() -> None:
    """Demonstrate fast keyword-based routing (no LLM call)."""
    print("Chapter 5: Hierarchical Routing")
    print("=" * 60)
    print("\nPhase 1: Keyword Routing (O(1), no LLM call)")
    print("-" * 50)

    # Show the routing patterns
    print("\nRouting patterns:")
    for agent, keywords in ROUTING_PATTERNS.items():
        print(f"  {agent}: {', '.join(keywords[:5])}...")

    # Create agents
    coder = Agent("coder", "You write Python code.", model="llama3.2")
    researcher = Agent("researcher", "You research topics.", model="llama3.2")
    planner = Agent("planner", "You create implementation plans.", model="llama3.2")

    router = Router(agents=[coder, researcher, planner])

    # Test routing decisions
    tasks = [
        "Write a function to sort a list",
        "What is the Kardashev scale?",
        "Design the architecture for a web app",
        "Fix the bug in the authentication module",
        "Explain how neural networks work",
    ]

    print("\nRouting decisions:")
    for task in tasks:
        decision = router.route(task)
        print(f"  '{task[:45]}...'")
        print(f"    -> [{decision.agent_name}] ({decision.method}, conf={decision.confidence:.2f})")
        print()


def demo_coordination_cost() -> None:
    """Show why hierarchy beats flat: O(n²) vs O(n) communication."""
    print("\nCoordination Cost: Flat vs Hierarchical")
    print("-" * 50)

    for n in [5, 10, 13, 25, 50, 100]:
        flat_cost = n * (n - 1) // 2  # O(n²) peer-to-peer
        hier_cost = n + (n // 5)       # O(n) hub-and-spoke with team leads
        ratio = flat_cost / hier_cost if hier_cost > 0 else 0

        print(
            f"  {n:3d} agents: flat={flat_cost:5d} messages,"
            f" hierarchical={hier_cost:3d} messages ({ratio:.1f}x cheaper)"
        )

    print("\n  At 13 agents: flat requires 78 connections, hierarchy requires ~16.")
    print("  This is why nature, corporations, and AGI all converge on hierarchy.")


def demo_full_routing() -> None:
    """Demonstrate full routing with LLM execution."""
    print("\nFull Routing with Agent Execution")
    print("-" * 50)

    coder = Agent(
        "coder",
        "You are a Python coder. Write concise code. Keep responses under 5 lines.",
        model="llama3.2",
    )
    researcher = Agent(
        "researcher",
        "You explain concepts concisely. Keep responses under 3 sentences.",
        model="llama3.2",
    )

    router = Router(agents=[coder, researcher])

    task = "Write a one-line Python function to check if a number is prime"
    print(f"\nTask: {task}")
    decision = router.route(task)
    print(f"Routed to: [{decision.agent_name}] via {decision.method}")

    response = router.execute(task)
    print(f"\n[{decision.agent_name}] {response}")


if __name__ == "__main__":
    demo_keyword_routing()
    demo_coordination_cost()
    demo_full_routing()
