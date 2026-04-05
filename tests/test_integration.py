"""Integration tests for LoopAGI - testing module interactions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from loopagi.core.agent import Agent, AgentConfig
from loopagi.core.events import BackgroundAgent, Event, EventBus
from loopagi.core.router import Router
from loopagi.knowledge.context import ActionTracker, RulesParser
from loopagi.safety.checker import SafetyChecker, TrustScore
from loopagi.safety.modes import ExecutionMode, ModeManager
from loopagi.tools.base import FileTool, ShellTool, ToolRegistry
from loopagi.tools.edit import EditTool
from loopagi.tools.search import SearchTool


def _mock_agent(name: str, role: str = "test") -> Agent:
    """Create a mock agent (no Ollama)."""
    agent = Agent.__new__(Agent)
    agent.config = AgentConfig(name=name, role=role)
    agent.llm = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = f"Response from {name}"
    agent.llm.invoke.return_value = mock_resp
    agent.history = []
    return agent


class TestRouterToAgentIntegration:
    """Test routing to agents and getting responses."""

    def test_route_and_execute(self) -> None:
        coder = _mock_agent("coder", "You code.")
        researcher = _mock_agent("researcher", "You research.")
        router = Router(agents=[coder, researcher])

        # Route a coding task
        decision = router.route("write a function to sort a list")
        assert decision.agent_name == "coder"

        # Execute with the routed agent
        agent = router.agents[decision.agent_name]
        result = agent.invoke("write sort")
        assert "coder" in result

    def test_route_unknown_falls_back(self) -> None:
        coder = _mock_agent("coder", "You code.")
        router = Router(agents=[coder])

        # Ambiguous query - should still route somewhere
        decision = router.route("xyzzy blargh")
        # Either keyword fails and LLM is used, or default
        assert decision.agent_name is not None


class TestToolChainIntegration:
    """Test tool chains: file write -> file read -> search."""

    def test_write_read_search(self, tmp_path: Path) -> None:
        registry = ToolRegistry()
        registry.register(FileTool())
        registry.register(SearchTool(cwd=str(tmp_path)))
        registry.register(EditTool())

        # Write a file
        path = str(tmp_path / "app.py")
        result = registry.execute(
            "file", action="write", path=path,
            content="def hello():\n    return 'world'\n",
        )
        assert result.success

        # Read it back
        result = registry.execute("file", action="read", path=path)
        assert result.success
        assert "hello" in result.output

        # Search for content
        result = registry.execute("search", action="grep", pattern="hello", path=".")
        assert result.success
        assert "hello" in result.output

        # Edit it
        result = registry.execute("edit", action="replace", path=path, old="world", new="universe")
        assert result.success

        # Verify edit
        result = registry.execute("file", action="read", path=path)
        assert "universe" in result.output


class TestEventBusToTrackerIntegration:
    """Test events flowing from bus to action tracker."""

    def test_events_tracked(self) -> None:
        tracker = ActionTracker()
        bus = EventBus()

        # Register a background agent that logs to tracker
        bus.register(BackgroundAgent(
            name="logger",
            event_types=["*"],
            handler=lambda e: tracker.record(e.event_type, str(e.data)[:100]),
        ))

        # Emit events
        bus.emit(Event(event_type="file_write", data={"path": "test.py"}))
        bus.emit(Event(event_type="shell_command", data={"command": "pytest"}))
        bus.emit(Event(event_type="agent_delegation", data={"agent": "coder"}))

        assert tracker.count == 3
        recent = tracker.recent(10)
        types = [a.action_type.value for a in recent]
        assert "file_write" in types
        assert "shell_command" in types


class TestSafetyToModeIntegration:
    """Test safety checker + execution mode interaction."""

    def test_turbo_mode_safe_no_approval(self) -> None:
        manager = ModeManager(mode=ExecutionMode.TURBO)
        checker = SafetyChecker()

        result = checker.check("ls -la")
        assert result.risk_level == "safe"
        assert not manager.requires_approval("ls -la")

    def test_turbo_mode_caution_needs_approval(self) -> None:
        manager = ModeManager(mode=ExecutionMode.TURBO)
        assert manager.requires_approval("sudo apt update")

    def test_careful_mode_everything_needs_approval(self) -> None:
        manager = ModeManager(mode=ExecutionMode.CAREFUL)
        assert manager.requires_approval("ls -la")
        assert manager.requires_approval("echo hello")

    def test_blocked_commands_always_blocked(self) -> None:
        checker = SafetyChecker()
        for mode in [ExecutionMode.TURBO, ExecutionMode.CAREFUL]:
            result = checker.check("rm -rf /")
            assert result.blocked

    def test_trust_affects_over_time(self) -> None:
        trust = TrustScore(initial=0.8)
        # Reinforce
        trust.reinforce(0.1)
        assert trust.score > 0.8
        # Penalize
        trust.penalize(0.3)
        assert trust.score < 0.8


class TestRulesIntegration:
    """Test rules loading and injection into agent context."""

    def test_rules_format_for_agents(self, tmp_path: Path) -> None:
        rules_file = tmp_path / ".looprules"
        rules_file.write_text("## Style\n- Use type hints\n- PEP 8\n\n## Testing\n- Use pytest\n")

        rules = RulesParser.parse(rules_file)
        assert len(rules) == 3

        prompt_text = RulesParser.format_for_prompt(rules)
        assert "PROJECT RULES:" in prompt_text
        assert "type hints" in prompt_text

        # Simulate injecting into agent role
        agent = _mock_agent("coder", "You code.")
        original_role = agent.config.role
        agent.config.role = original_role + "\n\n" + prompt_text
        assert "PROJECT RULES:" in agent.config.role
        assert "type hints" in agent.config.role


class TestFullToolRegistryIntegration:
    """Test all tools registered and working together."""

    def test_all_tools_registered(self, tmp_path: Path) -> None:
        registry = ToolRegistry()
        registry.register(ShellTool(timeout=5))
        registry.register(FileTool())
        registry.register(EditTool())
        registry.register(SearchTool(cwd=str(tmp_path)))

        tools = registry.list_tools()
        names = [t["name"] for t in tools]
        assert "shell" in names
        assert "file" in names
        assert "edit" in names
        assert "search" in names

    def test_shell_safety_integration(self) -> None:
        registry = ToolRegistry()
        registry.register(ShellTool())

        # Safe command works
        result = registry.execute("shell", command="echo safe")
        assert result.success

        # Blocked command is denied
        result = registry.execute("shell", command="rm -rf /")
        assert not result.success
        assert "blocked" in result.error.lower()
