"""
Chapter 19: 58 Services and the Docker Agent

Tool integration for agents: shell commands, file operations,
and Docker management. An agent with access to infrastructure
is an agent that can build.

Usage:
    from loopagi.tools.base import ShellTool, FileTool, ToolRegistry

    registry = ToolRegistry()
    registry.register(ShellTool())
    registry.register(FileTool())

    result = registry.execute("shell", command="ls -la")
    result = registry.execute("file_read", path="main.py")
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loopagi.safety.checker import SafetyChecker

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Result from a tool execution."""

    tool: str
    success: bool
    output: str = ""
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseTool:
    """Base class for all tools."""

    name: str = "base"
    description: str = "Base tool"

    def execute(self, **kwargs: Any) -> ToolResult:
        raise NotImplementedError


class ShellTool(BaseTool):
    """
    Execute shell commands with safety checking.

    All commands pass through the SafetyChecker before execution.
    Blocked commands are never executed regardless of mode.
    """

    name = "shell"
    description = "Execute shell commands safely"

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout
        self.checker = SafetyChecker()

    def execute(self, **kwargs: Any) -> ToolResult:
        command = kwargs.get("command", "")
        if not command:
            return ToolResult(tool=self.name, success=False, error="No command provided")

        # Safety check
        safety = self.checker.check(command)
        if safety.blocked:
            logger.warning("Shell command BLOCKED: %s", command)
            return ToolResult(
                tool=self.name,
                success=False,
                error=f"Command blocked: {safety.reason}",
            )

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=kwargs.get("cwd"),
            )
            return ToolResult(
                tool=self.name,
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else "",
                metadata={"exit_code": result.returncode, "command": command},
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool=self.name,
                success=False,
                error=f"Command timed out after {self.timeout}s",
            )
        except OSError as e:
            return ToolResult(
                tool=self.name,
                success=False,
                error=str(e),
            )


class FileTool(BaseTool):
    """
    File operations: read, write, list, search.
    """

    name = "file"
    description = "File system operations"

    def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "read")
        path = kwargs.get("path", "")

        match action:
            case "read":
                return self._read(path)
            case "write":
                return self._write(path, kwargs.get("content", ""))
            case "list":
                return self._list(path or ".")
            case "exists":
                return self._exists(path)
            case _:
                return ToolResult(
                    tool=self.name,
                    success=False,
                    error=f"Unknown action: {action}",
                )

    def _read(self, path: str) -> ToolResult:
        """Read a file."""
        try:
            content = Path(path).read_text(encoding="utf-8")
            return ToolResult(
                tool=self.name,
                success=True,
                output=content,
                metadata={"path": path, "action": "read", "size": len(content)},
            )
        except FileNotFoundError:
            return ToolResult(tool=self.name, success=False, error=f"File not found: {path}")
        except OSError as e:
            return ToolResult(tool=self.name, success=False, error=str(e))

    def _write(self, path: str, content: str) -> ToolResult:
        """Write content to a file."""
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return ToolResult(
                tool=self.name,
                success=True,
                output=f"Written {len(content)} bytes to {path}",
                metadata={"path": path, "action": "write", "size": len(content)},
            )
        except OSError as e:
            return ToolResult(tool=self.name, success=False, error=str(e))

    def _list(self, path: str) -> ToolResult:
        """List directory contents."""
        try:
            entries = []
            p = Path(path)
            for entry in sorted(p.iterdir()):
                prefix = "d" if entry.is_dir() else "f"
                size = entry.stat().st_size if entry.is_file() else 0
                entries.append(f"[{prefix}] {entry.name} ({size} bytes)")
            return ToolResult(
                tool=self.name,
                success=True,
                output="\n".join(entries),
                metadata={"path": path, "action": "list", "count": len(entries)},
            )
        except OSError as e:
            return ToolResult(tool=self.name, success=False, error=str(e))

    def _exists(self, path: str) -> ToolResult:
        """Check if a path exists."""
        exists = Path(path).exists()
        return ToolResult(
            tool=self.name,
            success=True,
            output=str(exists),
            metadata={"path": path, "action": "exists", "exists": exists},
        )


class ToolRegistry:
    """
    Central registry for all available tools.

    Agents interact with the world through tools. The registry
    provides a uniform interface for tool discovery and execution.
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.info("Registered tool: %s", tool.name)

    def execute(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """Execute a tool by name."""
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult(
                tool=tool_name,
                success=False,
                error=f"Tool not found: {tool_name}",
            )
        return tool.execute(**kwargs)

    def list_tools(self) -> list[dict[str, str]]:
        """List all registered tools."""
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
        ]

    def __repr__(self) -> str:
        return f"ToolRegistry(tools={list(self._tools.keys())})"
