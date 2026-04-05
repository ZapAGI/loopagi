"""
Code search tool for LoopAGI agents.

Provides: grep (text search), find (file search), symbols (function/class search).
"""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Any

from loopagi.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class SearchTool(BaseTool):
    """
    Search across project files.

    Supports: grep (content search), find (filename search),
    symbols (function/class definitions).
    """

    name = "search"
    description = "Search code and files across the project"

    def __init__(self, cwd: str | None = None) -> None:
        self._cwd = cwd or str(Path.cwd())

    def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "grep")

        match action:
            case "grep":
                return self._grep(
                    pattern=kwargs.get("pattern", ""),
                    path=kwargs.get("path", "."),
                    includes=kwargs.get("includes", ""),
                    case_sensitive=kwargs.get("case_sensitive", False),
                    max_results=kwargs.get("max_results", 50),
                )
            case "find":
                return self._find(
                    pattern=kwargs.get("pattern", ""),
                    path=kwargs.get("path", "."),
                    file_type=kwargs.get("file_type", "any"),
                )
            case "symbols":
                return self._symbols(
                    path=kwargs.get("path", "."),
                    symbol_type=kwargs.get("symbol_type", "all"),
                )
            case _:
                return ToolResult(tool=self.name, success=False, error=f"Unknown action: {action}")

    def _grep(
        self,
        pattern: str,
        path: str,
        includes: str,
        case_sensitive: bool,
        max_results: int,
    ) -> ToolResult:
        """Search file contents using grep or ripgrep."""
        if not pattern:
            return ToolResult(tool=self.name, success=False, error="Search pattern required")

        # Try ripgrep first, fall back to grep
        rg = self._which("rg")
        if rg:
            cmd = [rg, "--line-number", "--no-heading", f"--max-count={max_results}"]
            if not case_sensitive:
                cmd.append("--ignore-case")
            if includes:
                cmd.extend(["--glob", includes])
            cmd.extend([pattern, path])
        else:
            cmd = ["grep", "-rn", f"--max-count={max_results}"]
            if not case_sensitive:
                cmd.append("-i")
            if includes:
                cmd.extend(["--include", includes])
            cmd.extend([pattern, path])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=15, cwd=self._cwd,
            )
            output = result.stdout.strip()
            lines = output.split("\n") if output else []
            return ToolResult(
                tool=self.name,
                success=True,
                output=output or "(no matches)",
                metadata={"pattern": pattern, "matches": len(lines)},
            )
        except subprocess.TimeoutExpired:
            return ToolResult(tool=self.name, success=False, error="Search timed out")
        except OSError as e:
            return ToolResult(tool=self.name, success=False, error=str(e))

    def _find(self, pattern: str, path: str, file_type: str) -> ToolResult:
        """Search for files by name."""
        if not pattern:
            return ToolResult(tool=self.name, success=False, error="File pattern required")

        # Try fd first, fall back to find
        fd = self._which("fd") or self._which("fdfind")
        if fd:
            cmd = [fd, pattern, path]
            if file_type == "file":
                cmd.extend(["--type", "f"])
            elif file_type == "directory":
                cmd.extend(["--type", "d"])
        else:
            cmd = ["find", path, "-name", f"*{pattern}*"]
            if file_type == "file":
                cmd.extend(["-type", "f"])
            elif file_type == "directory":
                cmd.extend(["-type", "d"])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10, cwd=self._cwd,
            )
            output = result.stdout.strip()
            lines = output.split("\n") if output else []
            return ToolResult(
                tool=self.name,
                success=True,
                output=output or "(no matches)",
                metadata={"pattern": pattern, "matches": len(lines)},
            )
        except (subprocess.TimeoutExpired, OSError) as e:
            return ToolResult(tool=self.name, success=False, error=str(e))

    def _symbols(self, path: str, symbol_type: str) -> ToolResult:
        """Find Python function and class definitions using regex."""
        results = []
        root = Path(self._cwd) / path if not Path(path).is_absolute() else Path(path)

        try:
            for py_file in sorted(root.rglob("*.py")):
                if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                    continue
                rel = py_file.relative_to(root)
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(content.splitlines(), 1):
                    stripped = line.strip()
                    if symbol_type in ("all", "function") and stripped.startswith("def "):
                        match = re.match(r"def\s+(\w+)", stripped)
                        if match:
                            results.append(f"{rel}:{i}: def {match.group(1)}()")
                    if symbol_type in ("all", "class") and stripped.startswith("class "):
                        match = re.match(r"class\s+(\w+)", stripped)
                        if match:
                            results.append(f"{rel}:{i}: class {match.group(1)}")

            output = "\n".join(results[:100])
            return ToolResult(
                tool=self.name,
                success=True,
                output=output or "(no symbols found)",
                metadata={"symbols": len(results)},
            )
        except OSError as e:
            return ToolResult(tool=self.name, success=False, error=str(e))

    @staticmethod
    def _which(cmd: str) -> str | None:
        """Check if a command exists on PATH."""
        import shutil
        return shutil.which(cmd)
