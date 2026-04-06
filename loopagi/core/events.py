"""
Chapter 13: The Ethics of Autonomous Action

Event bus and background agents. Ethics in AI is not a constraint on
capability. It is the architecture that makes capability trustworthy.

Usage:
    from loopagi.core.events import EventBus, Event, BackgroundAgent

    bus = EventBus()

    # Register a background agent
    scanner = BackgroundAgent(
        name="security_scanner",
        event_types=["file_write", "shell_command"],
        handler=lambda event: print(f"Scanning: {event.data}"),
    )
    bus.register(scanner)

    # Emit events
    bus.emit(Event(event_type="file_write", data={"path": "main.py"}))
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """An event in the system."""

    event_type: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    source: str = ""


@dataclass
class BackgroundAgent:
    """
    A background agent that subscribes to specific event types.

    Background agents are automation that serves without being asked.
    They monitor the event bus and respond to events they care about.
    The question: when the auto-scanner discovers a vulnerability
    while you sleep, who should it tell?
    """

    name: str
    event_types: list[str]
    handler: Callable[[Event], None]
    enabled: bool = True
    description: str = ""


class EventBus:
    """
    Event-driven architecture for background agent coordination.

    Who subscribes to what? This is a moral framework as much as
    a technical one. The event bus determines which agents are
    aware of which actions, and therefore which agents can respond.

    The opt-out question: the tension between autonomy and authority.
    Every subscription is a statement about what the agent is
    permitted to observe.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[BackgroundAgent]] = defaultdict(list)
        self._global_subscribers: list[BackgroundAgent] = []
        self._event_log: list[Event] = []
        self._lock = threading.Lock()
        logger.info("EventBus initialized")

    def register(self, agent: BackgroundAgent) -> None:
        """Register a background agent to receive events."""
        with self._lock:
            if "*" in agent.event_types:
                self._global_subscribers.append(agent)
            else:
                for event_type in agent.event_types:
                    self._subscribers[event_type].append(agent)

        logger.info(
            "Registered background agent '%s' for events: %s",
            agent.name, agent.event_types,
        )

    def unregister(self, agent_name: str) -> None:
        """Unregister a background agent."""
        with self._lock:
            self._global_subscribers = [
                a for a in self._global_subscribers if a.name != agent_name
            ]
            for event_type in list(self._subscribers.keys()):
                self._subscribers[event_type] = [
                    a for a in self._subscribers[event_type] if a.name != agent_name
                ]
        logger.info("Unregistered background agent '%s'", agent_name)

    def emit(self, event: Event) -> int:
        """
        Emit an event to all subscribed background agents.

        Returns the number of agents that received the event.
        """
        with self._lock:
            self._event_log.append(event)
            subscribers = list(self._subscribers.get(event.event_type, []))
            subscribers.extend(self._global_subscribers)

        notified = 0
        for agent in subscribers:
            if not agent.enabled:
                continue
            try:
                agent.handler(event)
                notified += 1
            except Exception as e:
                logger.error(
                    "Background agent '%s' failed on event '%s': %s",
                    agent.name, event.event_type, e,
                )

        logger.debug(
            "Event '%s' emitted to %d agents", event.event_type, notified,
        )
        return notified

    def emit_async(self, event: Event) -> None:
        """Emit an event asynchronously in a background thread."""
        thread = threading.Thread(
            target=self.emit,
            args=(event,),
            daemon=True,
        )
        thread.start()

    @property
    def event_count(self) -> int:
        return len(self._event_log)

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            count = len(self._global_subscribers)
            for agents in self._subscribers.values():
                count += len(agents)
            return count

    def recent_events(self, count: int = 10) -> list[Event]:
        """Get the most recent events."""
        return self._event_log[-count:]

    def __repr__(self) -> str:
        return f"EventBus(subscribers={self.subscriber_count}, events={self.event_count})"
