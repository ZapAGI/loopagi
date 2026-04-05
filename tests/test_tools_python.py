"""Tests for loopagi.tools_python module."""

from __future__ import annotations

from pathlib import Path

from loopagi.tools.python import PythonTool


class TestPythonToolExec:
    """Tests for Python code execution."""

    def test_exec_simple(self, tmp_path: Path) -> None:
        tool = PythonTool(timeout=10, cwd=str(tmp_path))
        result = tool.execute(action="exec", code="print('hello')")
        assert result.success
        assert "hello" in result.output

    def test_exec_math(self, tmp_path: Path) -> None:
        tool = PythonTool(timeout=10, cwd=str(tmp_path))
        result = tool.execute(action="exec", code="print(2 + 2)")
        assert result.success
        assert "4" in result.output

    def test_exec_error(self, tmp_path: Path) -> None:
        tool = PythonTool(timeout=10, cwd=str(tmp_path))
        result = tool.execute(action="exec", code="raise ValueError('test error')")
        assert not result.success
        assert "ValueError" in result.error

    def test_exec_empty(self, tmp_path: Path) -> None:
        tool = PythonTool(cwd=str(tmp_path))
        result = tool.execute(action="exec", code="")
        assert not result.success

    def test_exec_timeout(self, tmp_path: Path) -> None:
        tool = PythonTool(timeout=2, cwd=str(tmp_path))
        result = tool.execute(action="exec", code="import time; time.sleep(10)")
        assert not result.success
        assert "timed out" in result.error.lower()


class TestPythonToolRun:
    """Tests for running Python files."""

    def test_run_file(self, tmp_path: Path) -> None:
        script = tmp_path / "hello.py"
        script.write_text("print('from file')\n")
        tool = PythonTool(timeout=10, cwd=str(tmp_path))
        result = tool.execute(action="run", path=str(script))
        assert result.success
        assert "from file" in result.output

    def test_run_missing_file(self, tmp_path: Path) -> None:
        tool = PythonTool(cwd=str(tmp_path))
        result = tool.execute(action="run", path="/nonexistent/script.py")
        assert not result.success

    def test_run_no_path(self, tmp_path: Path) -> None:
        tool = PythonTool(cwd=str(tmp_path))
        result = tool.execute(action="run", path="")
        assert not result.success


class TestPythonToolEval:
    """Tests for safe expression evaluation."""

    def test_eval_math(self) -> None:
        tool = PythonTool()
        result = tool.execute(action="eval", expr="2 + 3 * 4")
        assert result.success
        assert result.output == "14"

    def test_eval_builtin(self) -> None:
        tool = PythonTool()
        result = tool.execute(action="eval", expr="len([1, 2, 3])")
        assert result.success
        assert result.output == "3"

    def test_eval_max(self) -> None:
        tool = PythonTool()
        result = tool.execute(action="eval", expr="max(1, 5, 3)")
        assert result.success
        assert result.output == "5"

    def test_eval_empty(self) -> None:
        tool = PythonTool()
        result = tool.execute(action="eval", expr="")
        assert not result.success

    def test_eval_unsafe_blocked(self) -> None:
        tool = PythonTool()
        result = tool.execute(action="eval", expr="__import__('os').system('ls')")
        assert not result.success

    def test_unknown_action(self) -> None:
        tool = PythonTool()
        result = tool.execute(action="unknown")
        assert not result.success

    def test_name(self) -> None:
        tool = PythonTool()
        assert tool.name == "python"
