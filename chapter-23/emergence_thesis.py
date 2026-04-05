"""
Chapter 21: The Emergence Thesis

Can intelligence arise from parts that are not themselves intelligent?
If no single neuron thinks, no single worker builds a car, and no
single agent writes a complete application, then where does the
intelligence live?

Intelligence is not built. It emerges. And the conditions for
emergence are now within reach of any builder with consumer hardware.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class EmergenceExperiment:
    """Results from an emergence measurement experiment."""

    num_agents: int
    individual_scores: list[float]
    system_score: float
    phi_ratio: float
    phase: str


def measure_emergence_by_scale(
    agent_counts: list[int],
    interaction_strength: float = 0.3,
    seed: int = 42,
) -> list[EmergenceExperiment]:
    """
    Measure emergence as a function of system scale.

    As the number of interacting agents increases, there is a
    phase transition where emergent behavior appears.
    """
    random.seed(seed)
    results = []

    for n in agent_counts:
        individual = [random.gauss(0.5, 0.15) for _ in range(n)]
        sum_individual = sum(individual)

        interaction_bonus = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                synergy = individual[i] * individual[j] * interaction_strength
                interaction_bonus += synergy

        system_score = sum_individual + interaction_bonus
        phi = system_score / sum_individual if sum_individual > 0 else 1.0

        if phi < 1.1:
            phase = "sub-critical"
        elif phi < 1.5:
            phase = "critical"
        else:
            phase = "super-critical"

        results.append(EmergenceExperiment(
            num_agents=n,
            individual_scores=individual,
            system_score=system_score,
            phi_ratio=phi,
            phase=phase,
        ))

    return results


def demo() -> None:
    """Demonstrate the emergence thesis with scaling experiments."""
    print("Chapter 21: The Emergence Thesis")
    print("=" * 60)
    print()
    print("Hypothesis E1: Phi(S) > sum(Phi(s_i))")
    print("Emergence occurs when the system exceeds the sum of its parts.")
    print()

    agent_counts = [1, 2, 3, 5, 7, 10, 13, 15, 20, 25, 30]
    results = measure_emergence_by_scale(agent_counts)

    print(f"{'Agents':<8} {'Sum(parts)':<12} {'System':<12} {'Phi ratio':<12} {'Phase'}")
    print("-" * 56)

    for r in results:
        sum_parts = sum(r.individual_scores)
        print(
            f"{r.num_agents:<8} "
            f"{sum_parts:<12.2f} "
            f"{r.system_score:<12.2f} "
            f"{r.phi_ratio:<12.2f} "
            f"{r.phase}"
        )

    print()
    print("Phi Ratio Visualization:")
    print("-" * 50)
    for r in results:
        bar_len = int(r.phi_ratio * 15)
        bar = "X" * min(bar_len, 50)
        print(f"  {r.num_agents:3d} agents: {bar} {r.phi_ratio:.2f}")

    # Parallels
    print("\n\nThe Three Parallels:")
    print("-" * 50)
    parallels = [
        ("Neuroscience", "No single neuron is intelligent. 100 billion together: consciousness."),
        ("Economics", "No single worker builds a car. Millions together: an economy."),
        ("AGI", "No single agent writes an application. 13 together: emergent intelligence."),
    ]
    for domain, insight in parallels:
        print(f"\n  {domain}:")
        print(f"    {insight}")

    print()
    print("=" * 60)
    print("Intelligence is not built. It emerges.")
    print("And the conditions for emergence are now within reach")
    print("of any builder with consumer hardware.")


if __name__ == "__main__":
    demo()
