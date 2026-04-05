"""
Chapter 4: Multiple Specialists Demo

Create multiple specialist agents and compare how the same
model with different roles produces fundamentally different responses.

The agent is not the model. The agent is the model plus its role,
its tools, its constraints, and its relationships.

Prerequisites:
    ollama pull llama3.2
"""

from __future__ import annotations

from loopagi.core.agent import Agent


def demo() -> None:
    """Create 5 specialists and ask each the same question."""
    print("Chapter 4: Multiple Specialists - Same Model, Different Minds")
    print("=" * 60)

    agents = [
        Agent(
            name="coder",
            role="You are a Python coder. Answer in 2-3 sentences focused on implementation.",
            model="llama3.2",
        ),
        Agent(
            name="tester",
            role="You are a QA tester. Answer in 2-3 sentences focused on what could go wrong.",
            model="llama3.2",
        ),
        Agent(
            name="architect",
            role="You are a software architect. Answer in 2-3 sentences focused on system design.",
            model="llama3.2",
        ),
        Agent(
            name="security",
            role=(
                "You are a security specialist. Answer in 2-3 sentences"
                " focused on vulnerabilities."
            ),
            model="llama3.2",
        ),
        Agent(
            name="teacher",
            role=(
                "You are a programming teacher. Answer in 2-3 sentences"
                " as if explaining to a beginner."
            ),
            model="llama3.2",
        ),
    ]

    question = "How should we handle user authentication in a web application?"

    print(f"\nQuestion: {question}\n")
    print("-" * 60)

    for agent in agents:
        print(f"\n[{agent.name}]")
        response = agent.invoke(question)
        # Trim to first 3 sentences for readability
        sentences = response.replace("\n", " ").split(". ")
        trimmed = ". ".join(sentences[:3])
        if not trimmed.endswith("."):
            trimmed += "."
        print(f"  {trimmed}")

    print("\n" + "-" * 60)
    print("\nSame model, same question, 5 different perspectives.")
    print("The role transforms the behavior. That is what makes an agent.")


if __name__ == "__main__":
    demo()
