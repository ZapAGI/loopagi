"""
Memory agent: long-term memory storage and recall.

Wraps the MemoryStore to provide an agent interface for storing
facts, preferences, and project context, and recalling them later.

Usage:
    from loopagi.agents.memory_agent import MemoryAgent

    ma = MemoryAgent(model="qwen3:8b")
    ma.remember("User prefers FastAPI over Flask")
    memories = ma.recall("What framework does the user prefer?")
"""

from __future__ import annotations

import logging
from pathlib import Path

from loopagi.core.agent import Agent
from loopagi.knowledge.memory import MemoryStore

logger = logging.getLogger(__name__)

MEMORY_ROLE = (
    "You are a memory specialist. You manage long-term memory for the "
    "LoopAGI system. Capabilities:\n"
    "- Store facts, preferences, decisions, and project context\n"
    "- Recall relevant memories when asked\n"
    "- Summarize what is remembered about a topic\n"
    "- Forget specific memories when asked\n"
    "When recalling, rank results by relevance and present the most "
    "relevant memories first. Include the timestamp of each memory."
)

MEMORY_KEYWORDS = [
    "remember", "recall", "memory", "forget", "what did",
    "last time", "history", "store", "save note", "memorize",
    "noted", "keep in mind",
]


class MemoryAgent:
    """
    Agent that wraps MemoryStore for long-term memory.

    Provides a natural language interface for storing and
    recalling information across sessions.
    """

    def __init__(
        self,
        model: str = "qwen3:8b",
        memory_path: Path | str | None = None,
    ) -> None:
        self.agent = Agent(name="memory", role=MEMORY_ROLE, model=model)
        self.store = MemoryStore(path=memory_path)
        logger.info("MemoryAgent initialized (%d memories)", self.store.count())

    @property
    def name(self) -> str:
        return self.agent.name

    @property
    def role(self) -> str:
        return self.agent.role

    def remember(self, content: str, metadata: dict | None = None) -> str:
        """Store a memory and return its ID."""
        memory_id = self.store.add(content, metadata=metadata)
        logger.info("Stored memory: %s", memory_id[:8])
        return memory_id

    def recall(self, query: str, limit: int = 5) -> str:
        """Recall relevant memories and format them as text."""
        memories = self.store.search(query, limit=limit)
        if not memories:
            return "No relevant memories found."

        lines = []
        for i, mem in enumerate(memories, 1):
            import time

            ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(mem.timestamp))
            lines.append(f"{i}. [{ts}] {mem.content} (relevance: {mem.score:.2f})")
        return "\n".join(lines)

    def invoke(self, message: str) -> str:
        """Agent-compatible invoke interface."""
        lower = message.lower().strip()

        # Store command
        if lower.startswith(("remember ", "store ", "save ", "memorize ")):
            content = message.split(maxsplit=1)[1].strip()
            memory_id = self.remember(content)
            return f"Stored memory: {content}\n(ID: {memory_id[:8]})"

        # Forget command
        if lower.startswith("forget "):
            # Try to match and clear
            self.store.clear()
            return "All memories cleared."

        # Default: recall
        return self.recall(message)

    def reset(self) -> None:
        """Clear agent history (not memories)."""
        self.agent.reset()

    def count(self) -> int:
        """Return number of stored memories."""
        return self.store.count()

    def __repr__(self) -> str:
        return f"MemoryAgent(memories={self.store.count()})"
