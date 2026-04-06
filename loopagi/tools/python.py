"""
Python code execution tool for LoopAGI agents.

Provides: execute Python code directly, run Python files,
capture output and errors.
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from loopagi.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class PythonTool(BaseTool):
    """
    Execute Python code and scripts.

    Supports: run code strings, run files, run with arguments.
    """

    name = "python"
    description = "Execute Python code and scripts"

    def __init__(self, timeout: int = 30, cwd: str | None = None) -> None:
        self.timeout = timeout
        self._cwd = cwd or str(Path.cwd())

    def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "exec")

        match action:
            case "exec":
                return self._exec_code(kwargs.get("code", ""))
            case "run":
                return self._run_file(
                    path=kwargs.get("path", ""),
                    args=kwargs.get("args", []),
                )
            case "eval":
                return self._eval_expr(kwargs.get("expr", ""))
            case _:
                return ToolResult(tool=self.name, success=False, error=f"Unknown action: {action}")

    def _exec_code(self, code: str) -> ToolResult:
        """Execute a Python code string."""
        if not code:
            return ToolResult(tool=self.name, success=False, error="No code provided")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, dir=self._cwd,
        ) as f:
            f.write(code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                ["python3", tmp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self._cwd,
            )
            return ToolResult(
                tool=self.name,
                success=result.returncode == 0,
                output=result.stdout.strip(),
                error=result.stderr.strip() if result.returncode != 0 else "",
                metadata={"exit_code": result.returncode, "action": "exec"},
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool=self.name, success=False,
                error=f"Execution timed out after {self.timeout}s",
            )
        except OSError as e:
            return ToolResult(tool=self.name, success=False, error=str(e))
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def _run_file(self, path: str, args: list[str]) -> ToolResult:
        """Run a Python file."""
        if not path:
            return ToolResult(tool=self.name, success=False, error="File path required")

        if not Path(path).exists() and not (Path(self._cwd) / path).exists():
            return ToolResult(tool=self.name, success=False, error=f"File not found: {path}")

        try:
            cmd = ["python3", path] + args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self._cwd,
            )
            return ToolResult(
                tool=self.name,
                success=result.returncode == 0,
                output=result.stdout.strip(),
                error=result.stderr.strip() if result.returncode != 0 else "",
                metadata={"exit_code": result.returncode, "path": path, "action": "run"},
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool=self.name, success=False,
                error=f"Execution timed out after {self.timeout}s",
            )
        except OSError as e:
            return ToolResult(tool=self.name, success=False, error=str(e))

    def _eval_expr(self, expr: str) -> ToolResult:
        """Evaluate a simple Python expression safely."""
        if not expr:
            return ToolResult(tool=self.name, success=False, error="Expression required")

        # Only allow safe builtins
        safe_builtins = {
            "abs": abs, "all": all, "any": any, "bin": bin, "bool": bool,
            "chr": chr, "dict": dict, "divmod": divmod, "enumerate": enumerate,
            "filter": filter, "float": float, "format": format, "hex": hex,
            "int": int, "isinstance": isinstance, "len": len, "list": list,
            "map": map, "max": max, "min": min, "oct": oct, "ord": ord,
            "pow": pow, "range": range, "repr": repr, "reversed": reversed,
            "round": round, "set": set, "slice": slice, "sorted": sorted,
            "str": str, "sum": sum, "tuple": tuple, "type": type, "zip": zip,
            "True": True, "False": False, "None": None,
        }

        try:
            result = eval(expr, {"__builtins__": safe_builtins})
            return ToolResult(
                tool=self.name,
                success=True,
                output=str(result),
                metadata={"expr": expr, "action": "eval"},
            )
        except Exception as e:
            return ToolResult(tool=self.name, success=False, error=f"Eval error: {e}")
