"""
Chapter 6: Identity Experiment

When you create three copies of the same agent and give them
the same task, they produce different answers. Are they the
same entity? Different entities? Does it matter?

Parallel minds are not copies. They are perspectives.

Prerequisites:
    ollama pull llama3.2
"""

from __future__ import annotations

import hashlib

from loopagi.core.agent import Agent


def fingerprint(text: str) -> str:
    """Generate a short fingerprint of a text response."""
    return hashlib.md5(text.encode()).hexdigest()[:8]


def demo() -> None:
    """Three copies of the same agent answer the same question."""
    print("Chapter 6: The Identity Experiment")
    print("=" * 60)
    print()
    print("Three instances of the SAME agent (same role, same model)")
    print("answer the SAME question. Are the answers identical?")
    print()

    role = (
        "You are a Python coder. Write a function to check if a number "
        "is prime. Output ONLY the function, no explanation. Keep it under 10 lines."
    )

    agents = [
        Agent(name="coder:0", role=role, model="llama3.2"),
        Agent(name="coder:1", role=role, model="llama3.2"),
        Agent(name="coder:2", role=role, model="llama3.2"),
    ]

    question = "Write a function to check if a number is prime."

    print(f"Question: {question}")
    print(f"Agents: {[a.name for a in agents]}")
    print("-" * 60)

    responses = []
    for agent in agents:
        response = agent.invoke(question)
        responses.append(response)
        fp = fingerprint(response)
        print(f"\n[{agent.name}] (fingerprint: {fp})")
        # Show first 200 chars
        print(response[:200])
        if len(response) > 200:
            print(f"... ({len(response)} chars total)")

    # Compare responses
    print("\n" + "=" * 60)
    print("Analysis:")

    fingerprints = [fingerprint(r) for r in responses]
    unique = len(set(fingerprints))

    print(f"  Fingerprints: {fingerprints}")
    print(f"  Unique responses: {unique}/{len(responses)}")

    if unique == len(responses):
        print(f"\n  All {len(responses)} responses are DIFFERENT.")
        print("  Same role, same model, same question. Different answers.")
        print("  If identity requires uniqueness, each instance is unique.")
    elif unique == 1:
        print(f"\n  All {len(responses)} responses are IDENTICAL.")
        print("  The model is deterministic at temperature 0.")
    else:
        print(f"\n  {unique} unique responses out of {len(responses)}.")
        print("  Partial divergence: some identical, some different.")

    # Length comparison
    lengths = [len(r) for r in responses]
    print(f"\n  Response lengths: {lengths}")
    print(f"  Length variance: {max(lengths) - min(lengths)} chars")

    print()
    print("The philosophical question: if three instances of the same")
    print("agent produce three different implementations, which one")
    print("IS the agent? All of them. None of them. The agent is the")
    print("role, not any single execution of it.")


if __name__ == "__main__":
    demo()
