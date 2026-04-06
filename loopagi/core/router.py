"""
Chapter 5: The Hierarchy of Thought

Hierarchical routing: Master agent delegates tasks to specialist Workers.
Flat organizations reach a ceiling at scale. Hierarchy is not authority;
it is the architecture of efficient coordination.

Usage:
    from loopagi.core.agent import Agent
    from loopagi.core.router import Router

    coder = Agent("coder", "You write Python code.")
    researcher = Agent("researcher", "You research topics.")
    router = Router(agents=[coder, researcher])

    result = router.route("Write a sorting algorithm")
    # Routes to coder based on task analysis
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from loopagi.core.agent import Agent

logger = logging.getLogger(__name__)

# Lazy-loaded embedding model for Phase 2 routing
_embedding_model = None
_agent_embeddings: dict[str, list[float]] = {}

# Keyword patterns for fast routing (O(1) lookup before LLM classification)
ROUTING_PATTERNS: dict[str, list[str]] = {
    "coder": [
        "write", "code", "implement", "function", "class", "debug", "fix",
        "refactor", "script", "program", "algorithm", "api", "endpoint",
        "create", "build", "add", "modify", "update", "generate",
    ],
    "tester": [
        "test", "assert", "coverage", "unittest", "pytest", "verify",
        "validate", "check", "spec", "mock", "fixture",
    ],
    "reviewer": [
        "review", "critique", "improve", "quality", "style", "lint",
        "smell", "pattern", "clean", "evaluate", "rate", "feedback",
    ],
    "researcher": [
        "research", "look up", "what is", "explain", "how does", "compare",
        "analyze", "summarize", "describe", "define", "difference between",
        "why", "when should", "best practice",
    ],
    "planner": [
        "plan", "design", "architect", "structure", "outline", "roadmap",
        "break down", "decompose", "strategy", "approach", "steps",
    ],
    "fileops": [
        "file", "directory", "folder", "move", "copy", "rename", "delete",
        "list", "tree", "organize", "path", "find file",
    ],
    "devops": [
        "git", "commit", "branch", "merge", "deploy", "docker", "ci",
        "pipeline", "environment", "setup", "install", "configure",
        "container", "kubernetes", "infrastructure",
    ],
    "debugger": [
        "debug", "error", "traceback", "exception", "bug", "crash",
        "fail", "broken", "stack trace", "not working", "wrong output",
        "segfault", "core dump", "assertion", "raise", "unexpected",
    ],
    "documenter": [
        "document", "readme", "docstring", "changelog", "comment",
        "explain code", "api doc", "type hint", "annotate", "describe",
        "documentation", "docs", "jsdoc", "sphinx", "mkdocs",
    ],
    "knowledge": [
        "knowledge", "search docs", "what does", "find in docs",
        "look up", "index", "ingest", "rag", "knowledge base",
        "search knowledge",
    ],
    "memory": [
        "remember", "recall", "memory", "forget", "what did",
        "last time", "history", "store", "save note", "memorize",
        "noted", "keep in mind",
    ],
    "listener": [
        "listen", "voice input", "microphone", "speech to text",
        "transcribe", "hear", "record audio", "stt",
    ],
    "speaker": [
        "say", "speak", "read aloud", "voice output", "text to speech",
        "tts", "pronounce", "narrate",
    ],
}


@dataclass
class RouteDecision:
    """The result of routing a task to an agent."""

    agent_name: str
    confidence: float
    method: str  # "keyword", "embedding", or "llm"
    reasoning: str


class Router:
    """
    Hierarchical router that delegates tasks to specialist agents.

    Two-phase routing:
    1. Fast keyword matching (O(1), no LLM call)
    2. LLM classification fallback (slower, more accurate)

    The philosophical question: is routing a form of judgment?
    """

    def __init__(
        self,
        agents: list[Agent],
        master: Agent | None = None,
        keyword_threshold: float = 0.3,
        embedding_threshold: float = 0.5,
        enable_embedding: bool = True,
        embedding_model: str = "BAAI/bge-small-en-v1.5",
    ) -> None:
        self.agents = {agent.name: agent for agent in agents}
        self.master = master or Agent(
            name="master",
            role=(
                "You are the Master Orchestrator. Your job is to analyze tasks and "
                "decide which specialist agent should handle them. Available agents: "
                + ", ".join(f"'{a.name}': {a.role}" for a in agents)
            ),
        )
        self.keyword_threshold = keyword_threshold
        self.embedding_threshold = embedding_threshold
        self.enable_embedding = enable_embedding
        self.embedding_model_name = embedding_model
        logger.info(
            "Router initialized with %d agents: %s",
            len(self.agents),
            list(self.agents.keys()),
        )

    def route(self, task: str) -> RouteDecision:
        """
        Route a task to the best specialist agent.

        Phase 1: Try keyword matching (fast, no LLM call).
        Phase 2: Try embedding similarity (fast, no LLM call).
        Phase 3: Fall back to LLM classification (accurate).
        """
        # Phase 1: Keyword matching
        decision = self._keyword_route(task)
        if decision and decision.confidence >= self.keyword_threshold:
            logger.info(
                "Keyword routed '%s' to [%s] (confidence: %.2f)",
                task[:50], decision.agent_name, decision.confidence,
            )
            return decision

        # Phase 2: Embedding similarity
        if self.enable_embedding:
            decision = self._embedding_route(task)
            if decision and decision.confidence >= self.embedding_threshold:
                logger.info(
                    "Embedding routed '%s' to [%s] (confidence: %.2f)",
                    task[:50], decision.agent_name, decision.confidence,
                )
                return decision

        # Phase 3: LLM classification
        decision = self._llm_route(task)
        logger.info(
            "LLM routed '%s' to [%s] (confidence: %.2f)",
            task[:50], decision.agent_name, decision.confidence,
        )
        return decision

    def execute(self, task: str) -> str:
        """Route a task and execute it with the selected agent."""
        decision = self.route(task)
        agent = self.agents.get(decision.agent_name)
        if not agent:
            logger.warning("Agent '%s' not found, falling back to master", decision.agent_name)
            return self.master.invoke(task)
        return agent.invoke(task)

    def _keyword_route(self, task: str) -> RouteDecision | None:
        """Fast keyword-based routing. O(1) lookup."""
        task_lower = task.lower()
        scores: dict[str, float] = {}

        for agent_name, keywords in ROUTING_PATTERNS.items():
            if agent_name not in self.agents:
                continue
            matches = sum(1 for kw in keywords if kw in task_lower)
            if matches > 0:
                scores[agent_name] = matches / len(keywords)

        if not scores:
            return None

        best = max(scores, key=lambda k: scores[k])
        return RouteDecision(
            agent_name=best,
            confidence=scores[best],
            method="keyword",
            reasoning=f"Matched keywords for '{best}' in task",
        )

    def _embedding_route(self, task: str) -> RouteDecision | None:
        """Phase 2: Embedding similarity routing."""
        global _embedding_model, _agent_embeddings

        try:
            if _embedding_model is None:
                from fastembed import TextEmbedding

                _embedding_model = TextEmbedding(model_name=self.embedding_model_name)
                logger.info("Loaded embedding model: %s", self.embedding_model_name)

            # Build agent embeddings if not cached
            if not _agent_embeddings:
                for name, agent in self.agents.items():
                    role_text = f"{name}: {agent.role}"
                    embs = list(_embedding_model.embed([role_text]))
                    _agent_embeddings[name] = embs[0].tolist()
                logger.info("Built embeddings for %d agents", len(_agent_embeddings))

            # Embed the task
            task_emb = list(_embedding_model.embed([task]))[0].tolist()

            # Compute cosine similarity
            scores: dict[str, float] = {}
            for name, agent_emb in _agent_embeddings.items():
                if name not in self.agents:
                    continue
                scores[name] = self._cosine_similarity(task_emb, agent_emb)

            if not scores:
                return None

            best = max(scores, key=lambda k: scores[k])
            return RouteDecision(
                agent_name=best,
                confidence=scores[best],
                method="embedding",
                reasoning=f"Embedding similarity {scores[best]:.3f} for '{best}'",
            )
        except Exception as e:
            logger.warning("Embedding routing failed: %s", e)
            return None

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _llm_route(self, task: str) -> RouteDecision:
        """LLM-based routing. More accurate but requires an inference call."""
        agent_list = "\n".join(
            f"- {name}: {agent.role}" for name, agent in self.agents.items()
        )
        prompt = (
            f"Analyze this task and decide which agent should handle it.\n\n"
            f"Task: {task}\n\n"
            f"Available agents:\n{agent_list}\n\n"
            f"Respond with ONLY the agent name (one word, lowercase)."
        )
        response = self.master.invoke(prompt).strip().lower()

        # Extract agent name from response
        for agent_name in self.agents:
            if agent_name in response:
                return RouteDecision(
                    agent_name=agent_name,
                    confidence=0.8,
                    method="llm",
                    reasoning=f"LLM selected '{agent_name}' for task",
                )

        # Default to first agent if LLM response is unclear
        default = next(iter(self.agents))
        return RouteDecision(
            agent_name=default,
            confidence=0.5,
            method="llm",
            reasoning=f"LLM response unclear ('{response}'), defaulting to '{default}'",
        )

    def add_agent(self, agent: Agent) -> None:
        """Register a new specialist agent."""
        self.agents[agent.name] = agent
        logger.info("Agent '%s' added to router", agent.name)

    def __repr__(self) -> str:
        return f"Router(agents={list(self.agents.keys())})"
