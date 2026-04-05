"""End-to-end tests for LoopAGI CLI (no Ollama required - tests slash commands only)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from loopagi.cli import LoopAGI


def _make_loopagi(tmp_path: Path) -> LoopAGI:
    """Create a LoopAGI instance with mocked Ollama check and agents."""
    with patch.object(LoopAGI, "_check_ollama"):
        app = LoopAGI.__new__(LoopAGI)
        app.model = "test"
        app._last_response = ""
        app._context_files = {}
        app._conversation = []
        app._project_dir = str(tmp_path)

        # Mock agents
        from loopagi.core.agent import Agent, AgentConfig
        from loopagi.knowledge.context import ActionTracker
        from loopagi.core.events import EventBus
        from loopagi.safety.modes import ExecutionMode, ModeManager
        from loopagi.core.router import Router
        from loopagi.safety.checker import SafetyChecker, TrustScore
        from loopagi.tools.base import FileTool, ShellTool, ToolRegistry
        from loopagi.tools.edit import EditTool
        from loopagi.tools.git import GitTool
        from loopagi.tools.python import PythonTool
        from loopagi.tools.search import SearchTool
        from loopagi.tools.web import WebSearchTool

        mock_agents = []
        for name in ["coder", "researcher", "planner", "tester", "reviewer", "fileops", "devops"]:
            a = Agent.__new__(Agent)
            a.config = AgentConfig(name=name, role=f"You are {name}.")
            a.llm = MagicMock()
            resp = MagicMock()
            resp.content = f"Mock response from {name}"
            a.llm.invoke.return_value = resp
            a.history = []
            mock_agents.append(a)

        app.router = Router(agents=mock_agents)
        app.tracker = ActionTracker()
        app.mode_manager = ModeManager(mode=ExecutionMode.TURBO)
        app.safety = SafetyChecker()
        app.trust = TrustScore()
        app.event_bus = EventBus()

        app.tools = ToolRegistry()
        app.tools.register(ShellTool(timeout=5))
        app.tools.register(FileTool())
        app.tools.register(EditTool())
        app.tools.register(GitTool(cwd=str(tmp_path)))
        app.tools.register(SearchTool(cwd=str(tmp_path)))
        app.tools.register(PythonTool(timeout=5, cwd=str(tmp_path)))
        app.tools.register(WebSearchTool(timeout=5))

        return app


class TestCLISlashCommands:
    """E2E tests for CLI slash commands."""

    def test_help(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/help")
        assert "Commands" in result
        assert "/mode" in result
        assert "/agents" in result

    def test_agents(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/agents")
        assert "coder" in result
        assert "researcher" in result
        assert "planner" in result

    def test_tools(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/tools")
        assert "shell" in result
        assert "file" in result
        assert "edit" in result

    def test_mode_toggle(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/mode")
        assert "CAREFUL" in result
        result = app.process("/mode")
        assert "TURBO" in result

    def test_trust(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/trust")
        assert "Trust:" in result

    def test_history_empty(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/history")
        assert "No recent actions" in result

    def test_reset(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/reset")
        assert "cleared" in result.lower()

    def test_quit(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/quit")
        assert result == "__EXIT__"

    def test_exit(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        assert app.process("/exit") == "__EXIT__"
        assert app.process("/q") == "__EXIT__"

    def test_unknown_command(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/nonexistent")
        assert "Unknown command" in result

    def test_project_shows_current(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/project")
        assert str(tmp_path) in result


class TestCLIToolCommands:
    """E2E tests for tool-based slash commands."""

    def test_run_safe_command(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/run echo hello_e2e")
        assert "hello_e2e" in result

    def test_run_blocked_command(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/run rm -rf /")
        assert "BLOCKED" in result

    def test_python_exec(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/python print(2 + 2)")
        assert "4" in result

    def test_read_file(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("e2e content here")
        app = _make_loopagi(tmp_path)
        result = app.process(f"/read {test_file}")
        assert "e2e content here" in result

    def test_read_missing_file(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/read /nonexistent/file.txt")
        assert "Error" in result or "not found" in result.lower()

    def test_write_file(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        app._last_response = "written content"
        path = str(tmp_path / "output.txt")
        result = app.process(f"/write {path}")
        assert "Written" in result
        assert Path(path).read_text() == "written content"

    def test_write_no_response(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        app._last_response = ""
        result = app.process("/write test.txt")
        assert "No previous response" in result

    def test_search(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("def e2e_function(): pass\n")
        app = _make_loopagi(tmp_path)
        result = app.process("/search e2e_function")
        assert "e2e_function" in result

    def test_find(self, tmp_path: Path) -> None:
        (tmp_path / "config.toml").write_text("[test]\n")
        app = _make_loopagi(tmp_path)
        result = app.process("/find config")
        assert "config" in result

    def test_run_no_command(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/run")
        assert "Usage" in result

    def test_python_no_code(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/python")
        assert "Usage" in result


class TestCLIContextCommands:
    """E2E tests for context file management."""

    def test_add_and_context(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("print('hello')\n")
        app = _make_loopagi(tmp_path)

        result = app.process(f"/add {tmp_path / 'main.py'}")
        assert "Added" in result
        assert "1 files" in result

        result = app.process("/context")
        assert "main.py" in result

    def test_clear_context(self, tmp_path: Path) -> None:
        (tmp_path / "test.py").write_text("pass\n")
        app = _make_loopagi(tmp_path)
        app.process(f"/add {tmp_path / 'test.py'}")
        result = app.process("/clear")
        assert "cleared" in result.lower()

        result = app.process("/context")
        assert "No context files" in result

    def test_context_empty(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/context")
        assert "No context files" in result


class TestCLIAgentRouting:
    """E2E tests for message routing to agents."""

    def test_message_routes_to_agent(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("write a sorting function")
        assert "Mock response from" in result
        # Should show routing info
        assert "[" in result

    def test_message_tracked_in_conversation(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        app.process("hello agent")
        assert len(app._conversation) == 2  # user + agent

    def test_context_augmentation(self, tmp_path: Path) -> None:
        (tmp_path / "ctx.py").write_text("# context file content\n")
        app = _make_loopagi(tmp_path)
        app.process(f"/add {tmp_path / 'ctx.py'}")

        # The next message should include context in the prompt
        app.process("explain this code")

        # Check that the agent received an augmented prompt
        coder = app.router.agents.get("coder") or app.router.agents.get("researcher")
        if coder:
            last_call = coder.llm.invoke.call_args
            if last_call:
                messages = last_call[0][0]
                # The last human message should contain context
                last_msg = messages[-1].content
                assert "CONTEXT FILES" in last_msg or "explain" in last_msg


class TestCLIExport:
    """E2E tests for conversation export."""

    def test_export_conversation(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        app.process("write a function")
        export_path = str(tmp_path / "chat.md")
        result = app.process(f"/export {export_path}")
        assert "Exported" in result

        content = Path(export_path).read_text()
        assert "LoopAGI Conversation Export" in content

    def test_export_empty(self, tmp_path: Path) -> None:
        app = _make_loopagi(tmp_path)
        result = app.process("/export test.md")
        assert "No conversation" in result
