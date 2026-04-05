"""
Chapter 4: Your First Agent

The agent is not the model. The agent is the model plus its role,
its tools, its constraints, and its relationships.

This script creates a single specialist agent powered by Ollama
and demonstrates the fundamental pattern: role + model = agent.

Prerequisites:
    ollama pull llama3.2
"""

from __future__ import annotations

from loopagi.core.agent import Agent


def demo_single_agent() -> None:
    """Create and interact with a single specialist agent."""
    print("Chapter 4: Your First Agent")
    print("=" * 50)

    # Create a coding specialist
    coder = Agent(
        name="coder",
        role=(
            "You are a Python coding specialist. Write clean, well-documented "
            "Python code. Always use type hints and docstrings. Follow PEP 8. "
            "Output code in fenced code blocks."
        ),
        model="llama3.2",
    )
    print(f"\nCreated: {coder}")
    print(f"  Name: {coder.name}")
    print(f"  Role: {coder.role[:60]}...")
    print()

    # Ask the agent a coding question
    tasks = [
        "Write a Python function that checks if a string is a palindrome.",
        "Now add error handling for non-string inputs.",
    ]

    for task in tasks:
        print(f"[user] {task}")
        print()
        response = coder.invoke(task)
        print(f"[{coder.name}]")
        print(response)
        print()
        print("-" * 50)
        print()


def demo_agent_identity() -> None:
    """
    Demonstrate that the same model with different roles
    produces different agents with different behaviors.
    """
    print("\nAgent Identity: Same Model, Different Roles")
    print("=" * 50)

    # Two agents with the same model but different roles
    optimist = Agent(
        name="optimist",
        role=(
            "You are relentlessly positive. Find the upside in everything."
            " Keep responses to 2-3 sentences."
        ),
        model="llama3.2",
    )
    critic = Agent(
        name="critic",
        role=(
            "You are a thoughtful critic. Find potential issues and risks."
            " Keep responses to 2-3 sentences."
        ),
        model="llama3.2",
    )

    question = "We're building AGI on consumer hardware using 13 specialized agents."

    print(f"\nQuestion: {question}\n")

    for agent in [optimist, critic]:
        response = agent.invoke(question)
        print(f"[{agent.name}] {response}")
        print()

    print("The agent is not the model. The role transforms the behavior.")


if __name__ == "__main__":
    demo_single_agent()
    demo_agent_identity()
