"""
Chapter 5: Hierarchy Simulation

O(n^2) vs O(n) coordination cost comparison.
Why flat organizations reach a ceiling at scale,
in companies and in AI.

Hierarchy is not authority. It is the architecture
of efficient coordination.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class Message:
    """A coordination message between agents."""

    sender: str
    receiver: str
    content: str


def flat_coordination(n: int) -> tuple[int, list[Message]]:
    """
    Flat organization: every agent must communicate with every other.

    Communication cost: O(n^2) = n * (n-1) / 2 messages.
    """
    agents = [f"agent_{i}" for i in range(n)]
    messages = []
    for i, sender in enumerate(agents):
        for j, receiver in enumerate(agents):
            if i < j:
                messages.append(Message(sender, receiver, f"sync: {sender}<->{receiver}"))
    return len(messages), messages


def hierarchical_coordination(n: int, team_size: int = 4) -> tuple[int, list[Message]]:
    """
    Hierarchical organization: Master -> Team Leads -> Workers.

    Communication cost: O(n) = n (workers to leads) + k (leads to master).
    """
    agents = [f"worker_{i}" for i in range(n)]
    num_teams = max(1, (n + team_size - 1) // team_size)
    leads = [f"lead_{i}" for i in range(num_teams)]
    master = "master"

    messages = []

    # Workers report to their team lead
    for i, worker in enumerate(agents):
        lead = leads[i % num_teams]
        messages.append(Message(worker, lead, f"report: {worker}->{lead}"))

    # Team leads report to master
    for lead in leads:
        messages.append(Message(lead, master, f"summary: {lead}->{master}"))

    # Master sends decisions back to leads
    for lead in leads:
        messages.append(Message(master, lead, f"decision: {master}->{lead}"))

    return len(messages), messages


def simulate_task_completion(n: int, is_hierarchical: bool) -> float:
    """
    Simulate task completion time.

    Flat: every agent must wait for all-to-all sync before acting.
    Hierarchical: agents act after syncing with their team lead only.
    """
    random.seed(42)

    if is_hierarchical:
        # Parallel within teams, sequential across tiers
        team_size = 4
        num_teams = max(1, (n + team_size - 1) // team_size)
        # Time = max(team sync times) + lead sync + master decision
        team_times = [
            max(random.uniform(0.1, 0.5) for _ in range(min(team_size, n)))
            for _ in range(num_teams)
        ]
        lead_time = max(random.uniform(0.1, 0.3) for _ in range(num_teams))
        master_time = random.uniform(0.1, 0.2)
        return max(team_times) + lead_time + master_time
    else:
        # All-to-all sync: time grows with number of connections
        sync_time = sum(random.uniform(0.05, 0.15) for _ in range(n * (n - 1) // 2))
        return sync_time / n  # Parallelism helps somewhat


def demo() -> None:
    """Compare flat vs hierarchical coordination costs."""
    print("Chapter 5: Hierarchy Simulation")
    print("=" * 60)

    print(f"\n{'Agents':<8} {'Flat msgs':<12} {'Hier msgs':<12} {'Ratio':<10} {'Savings'}")
    print("-" * 55)

    for n in [3, 5, 8, 10, 13, 20, 30, 50, 100]:
        flat_count, _ = flat_coordination(n)
        hier_count, _ = hierarchical_coordination(n)
        ratio = flat_count / hier_count if hier_count > 0 else 0
        savings = (1 - hier_count / flat_count) * 100 if flat_count > 0 else 0
        print(f"  {n:<6} {flat_count:<12} {hier_count:<12} {ratio:<10.1f}x {savings:.0f}%")

    # Task completion simulation
    print("\n\nTask Completion Time Simulation:")
    print("-" * 55)
    print(f"{'Agents':<8} {'Flat time':<12} {'Hier time':<12} {'Speedup'}")
    print("-" * 40)

    for n in [5, 10, 13, 20, 50]:
        flat_time = simulate_task_completion(n, is_hierarchical=False)
        hier_time = simulate_task_completion(n, is_hierarchical=True)
        speedup = flat_time / hier_time if hier_time > 0 else 0
        print(f"  {n:<6} {flat_time:<12.3f}s {hier_time:<12.3f}s {speedup:.1f}x")

    # The ZAP AGI number
    print("\n\nAt 13 agents (the ZAP AGI architecture):")
    flat_13, _ = flat_coordination(13)
    hier_13, _ = hierarchical_coordination(13)
    print(f"  Flat:         {flat_13} messages (every agent talks to every other)")
    print(f"  Hierarchical: {hier_13} messages (workers -> leads -> master)")
    print(f"  Savings:      {(1 - hier_13/flat_13)*100:.0f}% fewer messages")
    print()
    print("This is why nature, corporations, and AGI all converge on hierarchy.")


if __name__ == "__main__":
    demo()
