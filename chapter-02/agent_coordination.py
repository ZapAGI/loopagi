"""
Chapter 2: Multi-Agent Coordination Without Central Control

Demonstrates how agents can coordinate through simple message
passing without a central orchestrator. Each agent makes local
decisions based on its neighbors, yet globally coordinated
behavior emerges.

This is the multi-agent analog of the Boids flocking simulation:
coordination from local rules, not central planning.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class Task:
    """A task that needs to be completed by agents."""

    id: int
    difficulty: float  # 0.0 to 1.0
    task_type: str
    completed: bool = False
    assigned_to: str = ""


@dataclass
class CoordinatingAgent:
    """An agent that coordinates with neighbors without a central controller."""

    name: str
    specialty: str
    skill: float  # 0.0 to 1.0
    capacity: int = 3
    current_tasks: list[Task] = field(default_factory=list)
    completed_count: int = 0

    @property
    def available(self) -> bool:
        return len(self.current_tasks) < self.capacity

    @property
    def load(self) -> float:
        return len(self.current_tasks) / self.capacity if self.capacity > 0 else 1.0

    def can_handle(self, task: Task) -> float:
        """Score how well this agent can handle a task (0.0 to 1.0)."""
        base = self.skill
        if task.task_type == self.specialty:
            base += 0.3
        load_penalty = self.load * 0.2
        return max(0.0, min(1.0, base - load_penalty))

    def accept_task(self, task: Task) -> bool:
        """Accept a task if the agent has capacity."""
        if not self.available:
            return False
        task.assigned_to = self.name
        self.current_tasks.append(task)
        return True

    def work(self) -> list[Task]:
        """Process current tasks. Returns completed tasks."""
        completed = []
        remaining = []
        for task in self.current_tasks:
            success_chance = self.can_handle(task) + random.gauss(0, 0.1)
            if success_chance > task.difficulty:
                task.completed = True
                self.completed_count += 1
                completed.append(task)
            else:
                remaining.append(task)
        self.current_tasks = remaining
        return completed


class DecentralizedCoordinator:
    """
    Coordination without a central controller.

    Each agent communicates only with its neighbors. Tasks are
    distributed through a gossip-like protocol where agents
    pass tasks they cannot handle to better-suited neighbors.
    """

    def __init__(self, agents: list[CoordinatingAgent]) -> None:
        self.agents = {a.name: a for a in agents}
        self._build_neighbor_graph()
        self.task_log: list[dict] = []

    def _build_neighbor_graph(self) -> None:
        """Build a neighbor graph (each agent knows 2-3 neighbors)."""
        names = list(self.agents.keys())
        self.neighbors: dict[str, list[str]] = {}
        for i, name in enumerate(names):
            n = []
            if i > 0:
                n.append(names[i - 1])
            if i < len(names) - 1:
                n.append(names[i + 1])
            if len(names) > 3:
                n.append(names[(i + len(names) // 2) % len(names)])
            self.neighbors[name] = list(set(n) - {name})

    def distribute_task(self, task: Task) -> str:
        """Distribute a task using decentralized negotiation."""
        # Start with a random agent
        start = random.choice(list(self.agents.keys()))
        visited = set()
        return self._negotiate(task, start, visited)

    def _negotiate(self, task: Task, agent_name: str, visited: set) -> str:
        """Recursive negotiation: try self, then ask neighbors."""
        if agent_name in visited:
            return ""
        visited.add(agent_name)

        agent = self.agents[agent_name]

        # Can I handle it?
        if agent.available and agent.can_handle(task) > 0.4:
            agent.accept_task(task)
            return agent_name

        # Ask neighbors
        neighbor_scores = []
        for neighbor_name in self.neighbors.get(agent_name, []):
            if neighbor_name not in visited:
                neighbor = self.agents[neighbor_name]
                score = neighbor.can_handle(task)
                if neighbor.available:
                    neighbor_scores.append((neighbor_name, score))

        # Route to best neighbor
        neighbor_scores.sort(key=lambda x: x[1], reverse=True)
        for neighbor_name, _ in neighbor_scores:
            result = self._negotiate(task, neighbor_name, visited)
            if result:
                return result

        # Fallback: accept even if overloaded
        if agent.can_handle(task) > 0.3:
            agent.accept_task(task)
            return agent_name

        return ""

    def step(self) -> dict[str, int]:
        """Run one work step: all agents process their tasks."""
        completed_by_agent = {}
        for name, agent in self.agents.items():
            completed = agent.work()
            completed_by_agent[name] = len(completed)
        return completed_by_agent


TASK_TYPES = ["coding", "testing", "research", "planning", "review"]


def demo() -> None:
    """Demonstrate decentralized multi-agent coordination."""
    print("Chapter 2: Multi-Agent Coordination Without Central Control")
    print("=" * 60)

    random.seed(42)

    agents = [
        CoordinatingAgent("coder", "coding", skill=0.8, capacity=3),
        CoordinatingAgent("tester", "testing", skill=0.7, capacity=3),
        CoordinatingAgent("researcher", "research", skill=0.75, capacity=2),
        CoordinatingAgent("planner", "planning", skill=0.7, capacity=2),
        CoordinatingAgent("reviewer", "review", skill=0.65, capacity=3),
    ]

    coord = DecentralizedCoordinator(agents)

    print(f"\nAgents: {[a.name for a in agents]}")
    print("Neighbor graph:")
    for name, neighbors in coord.neighbors.items():
        print(f"  {name} <-> {neighbors}")

    # Generate 30 random tasks
    tasks = [
        Task(id=i, difficulty=random.uniform(0.2, 0.8), task_type=random.choice(TASK_TYPES))
        for i in range(30)
    ]

    print(f"\nDistributing {len(tasks)} tasks (no central controller)...")
    print("-" * 50)

    assigned = 0
    for task in tasks:
        result = coord.distribute_task(task)
        if result:
            assigned += 1

    print(f"Assigned: {assigned}/{len(tasks)} tasks")
    print("\nTask distribution:")
    for name, agent in coord.agents.items():
        print(f"  {name}: {len(agent.current_tasks)} tasks (load: {agent.load:.0%})")

    # Run 5 work steps
    print("\nRunning 5 work steps...")
    for step in range(5):
        completed = coord.step()
        total = sum(completed.values())
        if total > 0:
            who = ", ".join(f"{k}:{v}" for k, v in completed.items() if v > 0)
            print(f"  Step {step + 1}: {total} completed ({who})")

    print("\nFinal results:")
    for name, agent in coord.agents.items():
        print(f"  {name}: {agent.completed_count} completed, {len(agent.current_tasks)} remaining")

    total_completed = sum(a.completed_count for a in coord.agents.values())
    print(f"\n  Total completed: {total_completed}/{len(tasks)}")
    print()
    print("No central controller was used. Agents coordinated through")
    print("local negotiation with neighbors. This is how nature computes.")


if __name__ == "__main__":
    demo()
