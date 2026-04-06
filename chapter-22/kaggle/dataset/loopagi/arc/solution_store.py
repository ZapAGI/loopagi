"""Solution store for cross-task transfer learning (Phase AA).

Stores solutions from solved tasks and retrieves them as few-shot code
examples for similar unsolved tasks. Works with the existing task_similarity
index to find relevant solved tasks.

Usage:
    from loopagi.arc.solution_store import SolutionStore
    store = SolutionStore()
    store.add("task_001", "def transform(g): return [[v+1 for v in r] for r in g]", 1.0)
    examples = store.get_similar_solutions(task, index, k=2)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import ArcTask
    from loopagi.arc.task_similarity import TaskIndex

logger = logging.getLogger(__name__)


@dataclass
class StoredSolution:
    """A solved task's code solution."""

    task_id: str
    code: str
    similarity: float  # training accuracy achieved
    method: str = ""  # how it was solved (transduced, synthesized, evolved)


@dataclass
class SolutionExample:
    """A solution example for few-shot injection into prompts."""

    task_id: str
    code: str
    relevance: float  # similarity to the query task


class SolutionStore:
    """Persistent store of solved task solutions for cross-task transfer."""

    def __init__(self) -> None:
        self._solutions: dict[str, StoredSolution] = {}

    def __len__(self) -> int:
        return len(self._solutions)

    def add(
        self, task_id: str, code: str, similarity: float, method: str = "",
    ) -> None:
        """Store a solution for a solved task."""
        if not code or similarity < 0.9:
            return  # Only store high-quality solutions
        self._solutions[task_id] = StoredSolution(
            task_id=task_id, code=code, similarity=similarity, method=method,
        )

    def has(self, task_id: str) -> bool:
        """Check if a solution exists for a task."""
        return task_id in self._solutions

    def get(self, task_id: str) -> StoredSolution | None:
        """Get a stored solution by task ID."""
        return self._solutions.get(task_id)

    def get_similar_solutions(
        self,
        task: ArcTask,
        index: TaskIndex,
        k: int = 3,
    ) -> list[SolutionExample]:
        """Find stored solutions from tasks similar to the query task.

        Uses the task_similarity index to find similar tasks, then returns
        solutions for any that have been solved.
        """
        if not self._solutions:
            return []

        from loopagi.arc.task_similarity import find_similar_tasks

        similar = find_similar_tasks(task, index, k=k * 3)
        examples: list[SolutionExample] = []

        for sim_task in similar:
            if sim_task.task_id in self._solutions:
                sol = self._solutions[sim_task.task_id]
                examples.append(SolutionExample(
                    task_id=sol.task_id,
                    code=sol.code,
                    relevance=sim_task.similarity,
                ))
                if len(examples) >= k:
                    break

        return examples

    def format_for_synthesis(self, examples: list[SolutionExample]) -> str:
        """Format solution examples for injection into synthesis prompts."""
        if not examples:
            return ""
        lines: list[str] = [
            "",
            "Code solutions from similar solved tasks (adapt, don't copy):",
        ]
        for ex in examples:
            lines.append(f"  Solved task ({ex.relevance:.0%} similar):")
            lines.append(f"  ```python\n  {ex.code}\n  ```")
        return "\n".join(lines)

    def save(self, path: str | Path) -> None:
        """Save solutions to a JSON file."""
        data = {
            tid: {
                "task_id": sol.task_id,
                "code": sol.code,
                "similarity": sol.similarity,
                "method": sol.method,
            }
            for tid, sol in self._solutions.items()
        }
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info("Saved %d solutions to %s", len(data), path)

    def load(self, path: str | Path) -> None:
        """Load solutions from a JSON file."""
        p = Path(path)
        if not p.exists():
            return
        data = json.loads(p.read_text(encoding="utf-8"))
        for tid, sol_data in data.items():
            self._solutions[tid] = StoredSolution(
                task_id=sol_data["task_id"],
                code=sol_data["code"],
                similarity=sol_data.get("similarity", 1.0),
                method=sol_data.get("method", ""),
            )
        logger.info("Loaded %d solutions from %s", len(self._solutions), path)

    def summary(self) -> str:
        """Return a compact summary."""
        if not self._solutions:
            return "SolutionStore: empty"
        methods = {}
        for sol in self._solutions.values():
            m = sol.method or "unknown"
            methods[m] = methods.get(m, 0) + 1
        method_str = ", ".join(f"{k}={v}" for k, v in methods.items())
        return f"SolutionStore: {len(self._solutions)} solutions ({method_str})"
