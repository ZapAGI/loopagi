"""
Chapter 6: The Pool - Parallel Minds

Agent pools for parallel execution. When you create three copies of
the same mind, are they the same entity? Different entities?
Parallel minds are not copies. They are perspectives.

Usage:
    from loopagi.core.pool import AgentPool

    pool = AgentPool(
        name="coder",
        role="You write Python code.",
        size=3,
    )
    results = pool.execute_parallel([
        "Write a sort function",
        "Write a search function",
        "Write a hash function",
    ])
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from loopagi.core.agent import Agent

logger = logging.getLogger(__name__)


@dataclass
class PoolResult:
    """Result from a single agent in the pool."""

    agent_index: int
    agent_name: str
    task: str
    response: str
    success: bool
    error: str | None = None


class AgentPool:
    """
    A pool of identical agent instances for parallel task execution.

    When VRAM or context limits constrain a single agent, pools
    allow multiple instances to work simultaneously on different
    tasks. The philosophical question: if three instances of the
    same agent produce three different answers, which one is "right"?

    The answer: all of them. Parallel minds are perspectives.
    """

    def __init__(
        self,
        name: str,
        role: str,
        size: int = 3,
        model: str = "llama3.2",
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.size = size
        self.agents = [
            Agent(
                name=f"{name}:{i}",
                role=role,
                model=model,
                **kwargs,
            )
            for i in range(size)
        ]
        self._task_queue: list[str] = []
        self._next_agent = 0
        logger.info("AgentPool '%s' created with %d instances", name, size)

    def execute(self, task: str) -> str:
        """Execute a task using the next available agent (round-robin)."""
        agent = self.agents[self._next_agent]
        self._next_agent = (self._next_agent + 1) % self.size
        logger.info("Pool '%s' dispatching to %s", self.name, agent.name)
        return agent.invoke(task)

    def execute_parallel(self, tasks: list[str]) -> list[PoolResult]:
        """
        Execute multiple tasks in parallel across pool agents.

        Tasks are distributed round-robin across available agents.
        Results are returned in the same order as input tasks.
        """
        return asyncio.run(self._execute_parallel_async(tasks))

    async def _execute_parallel_async(self, tasks: list[str]) -> list[PoolResult]:
        """Async implementation of parallel execution."""
        async_tasks = []
        for i, task in enumerate(tasks):
            agent = self.agents[i % self.size]
            async_tasks.append(self._execute_one(agent, i, task))
        return await asyncio.gather(*async_tasks)

    async def _execute_one(self, agent: Agent, index: int, task: str) -> PoolResult:
        """Execute a single task with error handling."""
        try:
            response = await agent.ainvoke(task)
            return PoolResult(
                agent_index=index,
                agent_name=agent.name,
                task=task,
                response=response,
                success=True,
            )
        except Exception as e:
            logger.error("Pool '%s' agent %s failed: %s", self.name, agent.name, e)
            return PoolResult(
                agent_index=index,
                agent_name=agent.name,
                task=task,
                response="",
                success=False,
                error=str(e),
            )

    def execute_consensus(self, task: str) -> str:
        """
        Execute the same task on ALL agents and return the best result.

        All agents answer the same question independently.
        The Master (or caller) can then pick the best response.
        This is the "parallel perspectives" pattern.
        """
        results = self.execute_parallel([task] * self.size)
        successful = [r for r in results if r.success]
        if not successful:
            raise RuntimeError(f"All {self.size} agents failed for task: {task[:100]}")

        # Return the longest successful response (heuristic: more detail = better)
        best = max(successful, key=lambda r: len(r.response))
        logger.info(
            "Consensus: selected %s (%d chars) from %d responses",
            best.agent_name, len(best.response), len(successful),
        )
        return best.response

    def reset_all(self) -> None:
        """Clear history for all agents in the pool."""
        for agent in self.agents:
            agent.reset()

    def __repr__(self) -> str:
        return f"AgentPool(name='{self.name}', size={self.size})"
