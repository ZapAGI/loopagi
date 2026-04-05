"""
Chapter 2: Emergence Simulation

Demonstrates emergent behavior: simple agents following simple rules
produce complex, coordinated behavior that none was designed for.

Inspired by Craig Reynolds' Boids (1987):
- Separation: avoid crowding nearby agents
- Alignment: steer toward average heading of neighbors
- Cohesion: steer toward average position of neighbors

Three simple rules. No central controller. Emergent flocking.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


@dataclass
class Vector2D:
    """Simple 2D vector."""

    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vector2D:
        return Vector2D(self.x * scalar, self.y * scalar)

    def magnitude(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def normalize(self) -> Vector2D:
        m = self.magnitude()
        if m == 0:
            return Vector2D(0, 0)
        return Vector2D(self.x / m, self.y / m)

    def distance_to(self, other: Vector2D) -> float:
        return (self - other).magnitude()


@dataclass
class SimpleAgent:
    """An agent with position, velocity, and simple rules."""

    id: int
    position: Vector2D = field(default_factory=Vector2D)
    velocity: Vector2D = field(default_factory=Vector2D)
    max_speed: float = 2.0
    perception_radius: float = 50.0


class EmergenceSimulation:
    """
    Simulate emergent flocking behavior.

    N agents, each following three simple rules, produce
    coordinated group behavior that no individual agent
    was programmed to exhibit.

    Hypothesis E1: Emergence occurs when Phi(S) > sum(Phi(s_i))
    """

    def __init__(
        self,
        num_agents: int = 30,
        world_size: float = 200.0,
        separation_weight: float = 1.5,
        alignment_weight: float = 1.0,
        cohesion_weight: float = 1.0,
    ) -> None:
        self.world_size = world_size
        self.separation_weight = separation_weight
        self.alignment_weight = alignment_weight
        self.cohesion_weight = cohesion_weight

        # Initialize agents with random positions and velocities
        self.agents = [
            SimpleAgent(
                id=i,
                position=Vector2D(
                    random.uniform(0, world_size),
                    random.uniform(0, world_size),
                ),
                velocity=Vector2D(
                    random.uniform(-1, 1),
                    random.uniform(-1, 1),
                ),
            )
            for i in range(num_agents)
        ]

    def step(self) -> dict[str, float]:
        """
        Advance the simulation by one time step.

        Returns metrics about the current state.
        """
        new_velocities = []

        for agent in self.agents:
            neighbors = self._get_neighbors(agent)

            if not neighbors:
                new_velocities.append(agent.velocity)
                continue

            # Rule 1: Separation (avoid crowding)
            sep = self._separation(agent, neighbors) * self.separation_weight

            # Rule 2: Alignment (match heading)
            ali = self._alignment(neighbors) * self.alignment_weight

            # Rule 3: Cohesion (move toward center)
            coh = self._cohesion(agent, neighbors) * self.cohesion_weight

            # Combine forces
            new_vel = agent.velocity + sep + ali + coh

            # Limit speed
            if new_vel.magnitude() > agent.max_speed:
                new_vel = new_vel.normalize() * agent.max_speed

            new_velocities.append(new_vel)

        # Update all agents simultaneously
        for agent, new_vel in zip(self.agents, new_velocities):
            agent.velocity = new_vel
            agent.position = agent.position + new_vel

            # Wrap around world boundaries
            agent.position.x %= self.world_size
            agent.position.y %= self.world_size

        return self._compute_metrics()

    def _get_neighbors(self, agent: SimpleAgent) -> list[SimpleAgent]:
        """Find agents within perception radius."""
        return [
            other for other in self.agents
            if other.id != agent.id
            and agent.position.distance_to(other.position) < agent.perception_radius
        ]

    def _separation(self, agent: SimpleAgent, neighbors: list[SimpleAgent]) -> Vector2D:
        """Rule 1: Steer away from nearby agents."""
        steer = Vector2D()
        for neighbor in neighbors:
            diff = agent.position - neighbor.position
            dist = diff.magnitude()
            if dist > 0:
                steer = steer + diff * (1.0 / dist)
        return steer.normalize() * 0.5

    def _alignment(self, neighbors: list[SimpleAgent]) -> Vector2D:
        """Rule 2: Match average velocity of neighbors."""
        avg_vel = Vector2D()
        for neighbor in neighbors:
            avg_vel = avg_vel + neighbor.velocity
        avg_vel = Vector2D(avg_vel.x / len(neighbors), avg_vel.y / len(neighbors))
        return avg_vel.normalize() * 0.3

    def _cohesion(self, agent: SimpleAgent, neighbors: list[SimpleAgent]) -> Vector2D:
        """Rule 3: Steer toward average position of neighbors."""
        center = Vector2D()
        for neighbor in neighbors:
            center = center + neighbor.position
        center = Vector2D(center.x / len(neighbors), center.y / len(neighbors))
        return (center - agent.position).normalize() * 0.2

    def _compute_metrics(self) -> dict[str, float]:
        """Compute emergence metrics for the current state."""
        # Average velocity alignment (how coordinated the group is)
        total_vel = Vector2D()
        for agent in self.agents:
            total_vel = total_vel + agent.velocity.normalize()
        avg_alignment = total_vel.magnitude() / len(self.agents)

        # Average distance to center (how clustered the group is)
        center = Vector2D()
        for agent in self.agents:
            center = center + agent.position
        center = Vector2D(center.x / len(self.agents), center.y / len(self.agents))
        avg_dist = sum(
            agent.position.distance_to(center) for agent in self.agents
        ) / len(self.agents)

        # Average speed
        avg_speed = sum(
            agent.velocity.magnitude() for agent in self.agents
        ) / len(self.agents)

        return {
            "alignment": avg_alignment,  # 0=random, 1=perfectly aligned
            "clustering": 1.0 - min(avg_dist / self.world_size, 1.0),  # 0=spread, 1=tight
            "avg_speed": avg_speed,
        }


# --- Demonstration ---


def demo() -> None:
    """Run the emergence simulation and show metrics over time."""
    print("Emergence Simulation: Boids Flocking")
    print("=" * 60)
    print("30 agents, 3 simple rules, no central controller")
    print()

    sim = EmergenceSimulation(num_agents=30)

    print(f"{'Step':<8} {'Alignment':<12} {'Clustering':<12} {'Avg Speed':<12} {'Emergent?'}")
    print("-" * 60)

    for step in range(50):
        metrics = sim.step()

        # Emergence threshold: alignment > 0.5 AND clustering > 0.3
        emergent = metrics["alignment"] > 0.5 and metrics["clustering"] > 0.3

        if step % 5 == 0 or emergent:
            print(
                f"{step:<8} "
                f"{metrics['alignment']:<12.4f} "
                f"{metrics['clustering']:<12.4f} "
                f"{metrics['avg_speed']:<12.4f} "
                f"{'YES' if emergent else 'no'}"
            )

    print()
    print("Key insight: coordinated flocking EMERGES from three simple rules.")
    print("No agent was programmed to flock. The behavior is emergent.")
    print()
    print("Hypothesis E1: Phi(S) > sum(Phi(s_i))")
    print("The system exhibits behavior that exceeds the sum of its parts.")


if __name__ == "__main__":
    demo()
