"""
Chapter 4: Agents, Not Models

The base Agent class. Every specialist in LoopAGI inherits from this.
An agent is not just a model. It is a model plus its role, its tools,
its constraints, and its relationships.

Usage:
    from loopagi.core.agent import Agent

    coder = Agent(
        name="coder",
        role="You are a Python coding specialist.",
        model="llama3.2",
    )
    response = coder.invoke("Write a fibonacci function")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for an agent instance."""

    name: str
    role: str
    model: str = "llama3.2"
    temperature: float = 0.7
    tools: list[str] = field(default_factory=list)
    max_history: int = 20


class Agent:
    """
    Base agent powered by a local Ollama model.

    Every agent has:
    - A name (identity)
    - A role (system prompt that defines behavior)
    - A model (the LLM that powers reasoning)
    - A conversation history (short-term memory)
    - A set of available tools (capabilities)
    """

    def __init__(self, name: str, role: str, model: str = "llama3.2", **kwargs: Any) -> None:
        self.config = AgentConfig(name=name, role=role, model=model, **kwargs)
        self.llm = ChatOllama(model=model, temperature=self.config.temperature)
        self.history: list[HumanMessage | AIMessage | SystemMessage] = []
        logger.info("Agent '%s' initialized with model '%s'", name, model)

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def role(self) -> str:
        return self.config.role

    def invoke(self, message: str) -> str:
        """Send a message to the agent and get a response."""
        messages = self._build_messages(message)
        response = self.llm.invoke(messages)
        content = response.content if isinstance(response.content, str) else str(response.content)

        # Maintain conversation history
        self.history.append(HumanMessage(content=message))
        self.history.append(AIMessage(content=content))
        self._trim_history()

        logger.info("[%s] responded (%d chars)", self.name, len(content))
        return content

    async def ainvoke(self, message: str) -> str:
        """Async version of invoke."""
        messages = self._build_messages(message)
        response = await self.llm.ainvoke(messages)
        content = response.content if isinstance(response.content, str) else str(response.content)

        self.history.append(HumanMessage(content=message))
        self.history.append(AIMessage(content=content))
        self._trim_history()

        logger.info("[%s] responded (%d chars)", self.name, len(content))
        return content

    def reset(self) -> None:
        """Clear conversation history."""
        self.history.clear()
        logger.info("[%s] history cleared", self.name)

    def _build_messages(self, message: str) -> list[SystemMessage | HumanMessage | AIMessage]:
        """Build the full message list with system prompt, history, and new message."""
        return [
            SystemMessage(content=self.role),
            *self.history,
            HumanMessage(content=message),
        ]

    def _trim_history(self) -> None:
        """Keep history within bounds to manage context window."""
        max_messages = self.config.max_history * 2  # pairs of human + ai
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', model='{self.config.model}')"
