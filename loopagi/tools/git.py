"""
Git operations tool for LoopAGI agents.

Provides: status, diff, log, commit, branch, checkout, add.
All operations include safety checking.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

from loopagi.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class GitTool(BaseTool):
    """
    Git version control operations.

    Supports: status, diff, log, commit, branch, checkout, add, stash.
    """

    name = "git"
    description = "Git version control operations"

    def __init__(self, cwd: str | None = None) -> None:
        self._cwd = cwd or str(Path.cwd())

    def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "status")

        match action:
            case "status":
                return self._run_git("status", "--short")
            case "diff":
                path = kwargs.get("path", "")
                staged = kwargs.get("staged", False)
                cmd = ["diff", "--staged"] if staged else ["diff"]
                if path:
                    cmd.append(path)
                return self._run_git(*cmd)
            case "log":
                count = kwargs.get("count", 10)
                return self._run_git("log", f"-{count}", "--oneline", "--decorate")
            case "add":
                path = kwargs.get("path", "-A")
                return self._run_git("add", path)
            case "commit":
                message = kwargs.get("message", "")
                if not message:
                    return ToolResult(
                        tool=self.name, success=False, error="Commit message required",
                    )
                return self._run_git("commit", "-m", message)
            case "branch":
                return self._run_git("branch", "-a")
            case "checkout":
                target = kwargs.get("target", "")
                if not target:
                    return ToolResult(
                        tool=self.name, success=False, error="Branch/commit target required",
                    )
                create = kwargs.get("create", False)
                if create:
                    return self._run_git("checkout", "-b", target)
                return self._run_git("checkout", target)
            case "stash":
                sub = kwargs.get("sub", "push")
                if sub == "pop":
                    return self._run_git("stash", "pop")
                return self._run_git("stash", "push")
            case "blame":
                path = kwargs.get("path", "")
                if not path:
                    return ToolResult(tool=self.name, success=False, error="File path required")
                return self._run_git("blame", "--line-porcelain", path)
            case _:
                return ToolResult(
                    tool=self.name, success=False,
                    error=f"Unknown git action: {action}",
                )

    def _run_git(self, *args: str) -> ToolResult:
        """Run a git command and return the result."""
        cmd = ["git"] + list(args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self._cwd,
            )
            return ToolResult(
                tool=self.name,
                success=result.returncode == 0,
                output=result.stdout.strip(),
                error=result.stderr.strip() if result.returncode != 0 else "",
                metadata={"command": " ".join(cmd), "exit_code": result.returncode},
            )
        except subprocess.TimeoutExpired:
            return ToolResult(tool=self.name, success=False, error="Git command timed out")
        except FileNotFoundError:
            return ToolResult(tool=self.name, success=False, error="Git is not installed")
        except OSError as e:
            return ToolResult(tool=self.name, success=False, error=str(e))
