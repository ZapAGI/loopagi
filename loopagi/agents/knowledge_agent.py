"""
Knowledge agent: RAG-powered retrieval from project documentation.

Wraps the RAGEngine to provide an agent interface for ingesting
documents and answering questions from indexed content.

Usage:
    from loopagi.agents.knowledge_agent import KnowledgeAgent

    ka = KnowledgeAgent(model="qwen3:8b")
    ka.ingest("docs/")
    answer = ka.ask("How does routing work?")
"""

from __future__ import annotations

import logging
from pathlib import Path

from loopagi.core.agent import Agent
from loopagi.knowledge.rag import RAGEngine, RAGStrategy

logger = logging.getLogger(__name__)

KNOWLEDGE_ROLE = (
    "You are a knowledge retrieval specialist. You manage the project's "
    "knowledge base using RAG (Retrieval-Augmented Generation). "
    "Capabilities:\n"
    "- Ingest documents, code files, and text into the knowledge base\n"
    "- Answer questions using only indexed content (cite sources)\n"
    "- Summarize ingested documents\n"
    "- Report what is and is not in the knowledge base\n"
    "Always cite the source document when answering. If the knowledge base "
    "does not contain the answer, say so clearly."
)

KNOWLEDGE_KEYWORDS = [
    "knowledge", "search docs", "what does", "find in docs",
    "look up", "index", "ingest", "rag", "knowledge base",
    "search knowledge",
]


class KnowledgeAgent:
    """
    Agent that wraps RAGEngine for knowledge retrieval.

    Combines an LLM agent with a RAG engine so that queries
    are answered from indexed project documentation.
    """

    def __init__(
        self,
        model: str = "qwen3:8b",
        rag_path: Path | str | None = None,
    ) -> None:
        self.agent = Agent(name="knowledge", role=KNOWLEDGE_ROLE, model=model)
        self.rag = RAGEngine(
            collection="loopagi_knowledge",
            path=rag_path,
            model=model,
        )
        logger.info("KnowledgeAgent initialized")

    @property
    def name(self) -> str:
        return self.agent.name

    @property
    def role(self) -> str:
        return self.agent.role

    def ingest(self, path: Path | str, pattern: str = "*.md") -> int:
        """Ingest documents from a directory into the knowledge base."""
        path = Path(path)
        if path.is_file():
            count = self.rag.ingest_file(path)
        elif path.is_dir():
            count = self.rag.ingest_directory(path, pattern=pattern)
        else:
            raise FileNotFoundError(f"Path not found: {path}")
        logger.info("Ingested %d chunks from %s", count, path)
        return count

    def ask(
        self,
        question: str,
        strategy: RAGStrategy = RAGStrategy.NAIVE,
    ) -> str:
        """Answer a question using the knowledge base."""
        result = self.rag.query(question, strategy=strategy)
        if not result.chunks:
            return (
                "No relevant information found in the knowledge base. "
                "Try ingesting documents first with /ingest <path>."
            )
        return result.answer

    def invoke(self, message: str) -> str:
        """Agent-compatible invoke interface."""
        # Check if it's an ingest command
        lower = message.lower().strip()
        if lower.startswith("ingest ") or lower.startswith("index "):
            path = message.split(maxsplit=1)[1].strip()
            try:
                count = self.ingest(path)
                return f"Ingested {count} chunks from {path}"
            except Exception as e:
                return f"Ingest failed: {e}"

        # Otherwise, query the knowledge base
        return self.ask(message)

    def reset(self) -> None:
        """Clear agent history."""
        self.agent.reset()

    def __repr__(self) -> str:
        return f"KnowledgeAgent(rag={self.rag!r})"
