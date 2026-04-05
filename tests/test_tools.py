"""Tests for loopagi.tools module (ShellTool, FileTool, ToolRegistry)."""

from __future__ import annotations

from pathlib import Path

from loopagi.tools.base import FileTool, ShellTool, ToolRegistry, ToolResult


class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_creation(self) -> None:
        r = ToolResult(tool="test", success=True, output="ok")
        assert r.tool == "test"
        assert r.success is True
        assert r.output == "ok"
        assert r.error == ""

    def test_failure(self) -> None:
        r = ToolResult(tool="test", success=False, error="bad")
        assert r.success is False
        assert r.error == "bad"


class TestShellTool:
    """Tests for the ShellTool."""

    def test_echo(self) -> None:
        tool = ShellTool(timeout=5)
        result = tool.execute(command="echo hello")
        assert result.success
        assert "hello" in result.output

    def test_blocked_command(self) -> None:
        tool = ShellTool()
        result = tool.execute(command="rm -rf /")
        assert not result.success
        assert "blocked" in result.error.lower()

    def test_empty_command(self) -> None:
        tool = ShellTool()
        result = tool.execute()
        assert not result.success

    def test_exit_code(self) -> None:
        tool = ShellTool(timeout=5)
        result = tool.execute(command="true")
        assert result.success
        assert result.metadata.get("exit_code") == 0

    def test_failing_command(self) -> None:
        tool = ShellTool(timeout=5)
        result = tool.execute(command="false")
        assert not result.success
        assert result.metadata.get("exit_code") == 1

    def test_timeout(self) -> None:
        tool = ShellTool(timeout=1)
        result = tool.execute(command="sleep 10")
        assert not result.success
        assert "timed out" in result.error.lower()

    def test_name_and_description(self) -> None:
        tool = ShellTool()
        assert tool.name == "shell"
        assert len(tool.description) > 0


class TestFileTool:
    """Tests for the FileTool."""

    def test_write_and_read(self, tmp_path: Path) -> None:
        tool = FileTool()
        path = str(tmp_path / "test.txt")

        # Write
        result = tool.execute(action="write", path=path, content="hello world")
        assert result.success
        assert "Written" in result.output

        # Read
        result = tool.execute(action="read", path=path)
        assert result.success
        assert result.output == "hello world"

    def test_read_nonexistent(self) -> None:
        tool = FileTool()
        result = tool.execute(action="read", path="/nonexistent/file.txt")
        assert not result.success
        assert "not found" in result.error.lower()

    def test_list_directory(self, tmp_path: Path) -> None:
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.py").write_text("b")
        (tmp_path / "sub").mkdir()

        tool = FileTool()
        result = tool.execute(action="list", path=str(tmp_path))
        assert result.success
        assert "a.txt" in result.output
        assert "b.py" in result.output
        assert "sub" in result.output

    def test_exists_true(self, tmp_path: Path) -> None:
        f = tmp_path / "exists.txt"
        f.write_text("yes")
        tool = FileTool()
        result = tool.execute(action="exists", path=str(f))
        assert result.success
        assert result.output == "True"

    def test_exists_false(self) -> None:
        tool = FileTool()
        result = tool.execute(action="exists", path="/nonexistent/xyz")
        assert result.success
        assert result.output == "False"

    def test_unknown_action(self) -> None:
        tool = FileTool()
        result = tool.execute(action="delete_everything")
        assert not result.success

    def test_write_creates_parents(self, tmp_path: Path) -> None:
        tool = FileTool()
        path = str(tmp_path / "deep" / "nested" / "file.txt")
        result = tool.execute(action="write", path=path, content="deep")
        assert result.success
        assert Path(path).read_text() == "deep"

    def test_name_and_description(self) -> None:
        tool = FileTool()
        assert tool.name == "file"
        assert len(tool.description) > 0


class TestToolRegistry:
    """Tests for the ToolRegistry."""

    def test_register_and_execute(self) -> None:
        registry = ToolRegistry()
        registry.register(ShellTool(timeout=5))
        result = registry.execute("shell", command="echo test")
        assert result.success

    def test_unknown_tool(self) -> None:
        registry = ToolRegistry()
        result = registry.execute("nonexistent")
        assert not result.success
        assert "not found" in result.error.lower()

    def test_list_tools(self) -> None:
        registry = ToolRegistry()
        registry.register(ShellTool())
        registry.register(FileTool())
        tools = registry.list_tools()
        assert len(tools) == 2
        names = [t["name"] for t in tools]
        assert "shell" in names
        assert "file" in names

    def test_repr(self) -> None:
        registry = ToolRegistry()
        registry.register(ShellTool())
        r = repr(registry)
        assert "ToolRegistry" in r
        assert "shell" in r
