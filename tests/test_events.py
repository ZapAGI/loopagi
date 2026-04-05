"""Tests for loopagi.events module."""

from __future__ import annotations

from loopagi.core.events import BackgroundAgent, Event, EventBus


class TestEventBus:
    """Tests for the EventBus."""

    def test_register_and_emit(self) -> None:
        bus = EventBus()
        received = []

        agent = BackgroundAgent(
            name="test_agent",
            event_types=["file_write"],
            handler=lambda e: received.append(e),
        )
        bus.register(agent)

        bus.emit(Event(event_type="file_write", data={"path": "test.py"}))
        assert len(received) == 1
        assert received[0].data["path"] == "test.py"

    def test_event_type_filtering(self) -> None:
        bus = EventBus()
        received = []

        agent = BackgroundAgent(
            name="file_watcher",
            event_types=["file_write"],
            handler=lambda e: received.append(e),
        )
        bus.register(agent)

        bus.emit(Event(event_type="shell_command", data={}))
        assert len(received) == 0

        bus.emit(Event(event_type="file_write", data={}))
        assert len(received) == 1

    def test_wildcard_subscriber(self) -> None:
        bus = EventBus()
        received = []

        agent = BackgroundAgent(
            name="monitor",
            event_types=["*"],
            handler=lambda e: received.append(e),
        )
        bus.register(agent)

        bus.emit(Event(event_type="file_write"))
        bus.emit(Event(event_type="shell_command"))
        bus.emit(Event(event_type="agent_delegation"))
        assert len(received) == 3

    def test_multiple_subscribers(self) -> None:
        bus = EventBus()
        counts = {"a": 0, "b": 0}

        bus.register(BackgroundAgent(
            name="a", event_types=["test"],
            handler=lambda e: counts.__setitem__("a", counts["a"] + 1),
        ))
        bus.register(BackgroundAgent(
            name="b", event_types=["test"],
            handler=lambda e: counts.__setitem__("b", counts["b"] + 1),
        ))

        notified = bus.emit(Event(event_type="test"))
        assert notified == 2
        assert counts["a"] == 1
        assert counts["b"] == 1

    def test_unregister(self) -> None:
        bus = EventBus()
        received = []

        bus.register(BackgroundAgent(
            name="temp", event_types=["test"],
            handler=lambda e: received.append(e),
        ))
        bus.unregister("temp")

        bus.emit(Event(event_type="test"))
        assert len(received) == 0

    def test_disabled_agent(self) -> None:
        bus = EventBus()
        received = []

        bus.register(BackgroundAgent(
            name="disabled",
            event_types=["test"],
            handler=lambda e: received.append(e),
            enabled=False,
        ))

        bus.emit(Event(event_type="test"))
        assert len(received) == 0

    def test_event_count(self) -> None:
        bus = EventBus()
        assert bus.event_count == 0
        bus.emit(Event(event_type="a"))
        bus.emit(Event(event_type="b"))
        assert bus.event_count == 2

    def test_recent_events(self) -> None:
        bus = EventBus()
        for i in range(5):
            bus.emit(Event(event_type=f"event_{i}"))
        recent = bus.recent_events(3)
        assert len(recent) == 3
        assert recent[-1].event_type == "event_4"

    def test_handler_error_does_not_crash(self) -> None:
        bus = EventBus()
        bus.register(BackgroundAgent(
            name="crasher",
            event_types=["test"],
            handler=lambda e: 1 / 0,  # Will raise ZeroDivisionError
        ))
        # Should not raise
        bus.emit(Event(event_type="test"))
