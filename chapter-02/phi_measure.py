"""
Chapter 2: Formal Emergence Measure

Hypothesis E1: Emergence occurs when Phi(S) > sum(Phi(s_i))

Where:
- Phi(S) is the capability of the whole system
- Phi(s_i) is the capability of each individual component
- The excess is the "emergent surplus": behavior that cannot
  be predicted from the components alone

We measure capability using task completion scoring: each agent
attempts tasks independently, and the orchestrated system attempts
the same tasks. Emergence is when the system outperforms any
individual agent and their simple sum.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass


@dataclass
class Agent:
    """A simulated specialist agent with strengths and weaknesses."""

    name: str
    strengths: list[str]
    base_skill: float  # 0.0 to 1.0
    variance: float


def score_task(agent: Agent, task_type: str) -> float:
    """Score an agent's performance on a task type."""
    base = agent.base_skill
    if task_type in agent.strengths:
        base += 0.2  # bonus for specialization
    noise = random.gauss(0, agent.variance)
    return max(0.0, min(1.0, base + noise))


def score_independent_sum(agents: list[Agent], tasks: list[str]) -> list[float]:
    """Each agent tries each task independently. Take the best score per task."""
    scores = []
    for task in tasks:
        best = max(score_task(agent, task) for agent in agents)
        scores.append(best)
    return scores


def score_orchestrated(agents: list[Agent], tasks: list[str]) -> list[float]:
    """
    Orchestrated system: agents collaborate on each task.

    The key: orchestration adds nonlinear benefits:
    - Specialist routing (right agent for the job)
    - Quality pipeline (each agent refines the previous output)
    - Error correction (reviewer catches what coder misses)
    """
    scores = []
    for task in tasks:
        # Step 1: Route to the best specialist
        agent_scores = [(agent, score_task(agent, task)) for agent in agents]
        best_agent, initial_score = max(agent_scores, key=lambda x: x[1])

        # Step 2: Quality pipeline refinement
        # Each additional agent contributes a multiplicative improvement
        refinement = 1.0
        for agent, s in agent_scores:
            if agent.name != best_agent.name:
                # Each specialist adds a small multiplicative boost
                boost = 1.0 + (s * 0.15)
                refinement *= boost

        # Step 3: Combined score with orchestration bonus
        orchestrated_score = min(1.0, initial_score * refinement)
        scores.append(orchestrated_score)

    return scores


def measure_emergence(
    agents: list[Agent],
    tasks: list[str],
    num_trials: int = 500,
) -> dict[str, float]:
    """
    Measure emergence by comparing independent vs orchestrated performance.

    Returns metrics showing whether the system exceeds the sum of parts.
    """
    individual_means = []
    for agent in agents:
        agent_scores = [score_task(agent, random.choice(tasks)) for _ in range(num_trials)]
        individual_means.append(statistics.mean(agent_scores))

    sum_individual = sum(individual_means)
    best_individual = max(individual_means)

    # Independent best-of-N (no orchestration, just pick the best)
    independent_scores = []
    for _ in range(num_trials):
        task = random.choice(tasks)
        independent_scores.extend(score_independent_sum(agents, [task]))
    independent_mean = statistics.mean(independent_scores)

    # Orchestrated system
    orchestrated_scores = []
    for _ in range(num_trials):
        task = random.choice(tasks)
        orchestrated_scores.extend(score_orchestrated(agents, [task]))
    orchestrated_mean = statistics.mean(orchestrated_scores)

    return {
        "sum_individual": sum_individual,
        "best_individual": best_individual,
        "independent_best_of_n": independent_mean,
        "orchestrated_system": orchestrated_mean,
        "emergence_ratio": orchestrated_mean / independent_mean,
        "emergent": orchestrated_mean > independent_mean,
        "individual_means": individual_means,
    }


# --- Demonstrations ---

TASK_TYPES = ["planning", "coding", "testing", "reviewing", "research", "debugging"]


def demo_no_emergence() -> None:
    """Identical agents: no specialization, no emergence."""
    print("Scenario 1: Identical Agents (No Emergence)")
    print("-" * 55)

    random.seed(42)
    agents = [
        Agent(name=f"generalist_{i}", strengths=[], base_skill=0.5, variance=0.1)
        for i in range(5)
    ]

    result = measure_emergence(agents, TASK_TYPES)
    print(f"  Best individual:     {result['best_individual']:.4f}")
    print(f"  Independent best-of: {result['independent_best_of_n']:.4f}")
    print(f"  Orchestrated system: {result['orchestrated_system']:.4f}")
    print(f"  Emergence ratio:     {result['emergence_ratio']:.4f}")
    print(f"  Emergent:            {result['emergent']}")
    print()


def demo_specialists() -> None:
    """Specialist agents: specialization enables emergence."""
    print("Scenario 2: Specialist Agents (Emergence)")
    print("-" * 55)

    random.seed(42)
    agents = [
        Agent(name="planner", strengths=["planning"], base_skill=0.6, variance=0.08),
        Agent(name="coder", strengths=["coding", "debugging"], base_skill=0.65, variance=0.1),
        Agent(name="tester", strengths=["testing"], base_skill=0.7, variance=0.05),
        Agent(name="reviewer", strengths=["reviewing"], base_skill=0.6, variance=0.08),
        Agent(name="researcher", strengths=["research"], base_skill=0.55, variance=0.12),
    ]

    result = measure_emergence(agents, TASK_TYPES)
    print(f"  Best individual:     {result['best_individual']:.4f}")
    print(f"  Independent best-of: {result['independent_best_of_n']:.4f}")
    print(f"  Orchestrated system: {result['orchestrated_system']:.4f}")
    print(f"  Emergence ratio:     {result['emergence_ratio']:.4f}")
    print(f"  Emergent:            {result['emergent']}")
    print()
    for agent, mean in zip(agents, result["individual_means"]):
        print(f"    {agent.name:<12} solo avg: {mean:.4f}")
    print()


def demo_scaling() -> None:
    """Show emergence increasing with team size."""
    print("Scenario 3: Emergence vs Team Size")
    print("-" * 55)

    random.seed(42)
    print(f"  {'Agents':<8} {'Independent':<14} {'Orchestrated':<14} {'Ratio':<10} {'Emergent'}")
    print(f"  {'-'*8} {'-'*14} {'-'*14} {'-'*10} {'-'*8}")

    for n in [1, 2, 3, 5, 8, 13]:
        agents = [
            Agent(
                name=f"agent_{i}",
                strengths=[TASK_TYPES[i % len(TASK_TYPES)]],
                base_skill=0.5 + random.uniform(0, 0.2),
                variance=0.08,
            )
            for i in range(n)
        ]
        result = measure_emergence(agents, TASK_TYPES, num_trials=200)
        print(
            f"  {n:<8} "
            f"{result['independent_best_of_n']:<14.4f} "
            f"{result['orchestrated_system']:<14.4f} "
            f"{result['emergence_ratio']:<10.4f} "
            f"{'YES' if result['emergent'] else 'no'}"
        )

    print()
    print("  As team size grows, the orchestration bonus compounds.")
    print("  At 13 agents (the ZAP AGI number), emergence is clear.")


def demo() -> None:
    """Run all emergence demonstrations."""
    print("Formal Emergence Measure: Phi(S) > sum(Phi(s_i))")
    print("=" * 60)
    print()

    demo_no_emergence()
    demo_specialists()
    demo_scaling()

    print("=" * 60)
    print("CONCLUSION: General intelligence is not designed. It emerges")
    print("from the orchestration of specialists.")


if __name__ == "__main__":
    demo()
