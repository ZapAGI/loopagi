"""
Chapter 13: Event-Driven Background Agents

When the auto-scanner discovers a vulnerability at 3 AM,
who should it tell? Who gave it permission to look?

Ethics in AI is not a constraint on capability.
It is the architecture that makes capability trustworthy.
"""

from __future__ import annotations

from loopagi.core.events import BackgroundAgent, Event, EventBus


def demo() -> None:
    """Demonstrate event-driven background agent architecture."""
    print("Chapter 13: Event-Driven Background Agents")
    print("=" * 60)

    bus = EventBus()

    # Track what each agent observed
    observations: dict[str, list[str]] = {}

    def make_handler(name: str):
        observations[name] = []
        def handler(event: Event):
            msg = f"[{name}] saw {event.event_type}: {event.data}"
            observations[name].append(msg)
            print(f"  {msg}")
        return handler

    # Register specialized background agents
    agents = [
        BackgroundAgent(
            name="security_scanner",
            event_types=["file_write", "shell_command"],
            handler=make_handler("security_scanner"),
            description="Monitors file writes and commands for security risks",
        ),
        BackgroundAgent(
            name="test_watcher",
            event_types=["file_write", "code_exec"],
            handler=make_handler("test_watcher"),
            description="Triggers test re-runs when code changes",
        ),
        BackgroundAgent(
            name="health_monitor",
            event_types=["*"],
            handler=make_handler("health_monitor"),
            description="Monitors all system events for anomalies",
        ),
        BackgroundAgent(
            name="memory_indexer",
            event_types=["agent_response", "user_preference"],
            handler=make_handler("memory_indexer"),
            description="Indexes significant interactions for memory",
        ),
    ]

    for agent in agents:
        bus.register(agent)

    print(f"\nRegistered {bus.subscriber_count} background agents:")
    for agent in agents:
        print(f"  - {agent.name}: {agent.description}")
        print(f"    Listens to: {agent.event_types}")

    # Simulate a sequence of system events
    print("\nSimulating events...")
    print("-" * 50)

    events = [
        Event(event_type="file_write", data={"path": "main.py", "lines": 42}),
        Event(event_type="shell_command", data={"command": "pytest tests/"}),
        Event(event_type="code_exec", data={"file": "main.py", "exit_code": 0}),
        Event(event_type="agent_response", data={"agent": "coder", "task": "fibonacci"}),
        Event(event_type="user_preference", data={"key": "style", "value": "functional"}),
        Event(event_type="file_write", data={"path": "utils.py", "lines": 15}),
    ]

    for event in events:
        notified = bus.emit(event)
        print(f"  Event '{event.event_type}' -> {notified} agents notified")

    # Summary
    print("\nEvent Summary:")
    print(f"  Total events: {bus.event_count}")
    print("\nAgent Activity:")
    for name, obs in observations.items():
        print(f"  {name}: {len(obs)} events observed")

    print()
    print("Each background agent only sees the events it subscribed to,")
    print("except the health_monitor which sees everything (wildcard *).")
    print()
    print("The ethical question: who subscribes to what determines")
    print("what each agent is PERMITTED to observe and act upon.")


if __name__ == "__main__":
    demo()
