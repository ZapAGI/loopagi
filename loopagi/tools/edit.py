"""
File editing tool for LoopAGI agents.

Provides: find-and-replace editing, insert lines, delete lines,
patch application. More surgical than full file overwrites.
"""

from __future__ import annotations

import difflib
import logging
from pathlib import Path
from typing import Any

from loopagi.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class EditTool(BaseTool):
    """
    Surgical file editing: find-and-replace, insert, delete.

    Unlike the FileTool which overwrites entire files, this tool
    makes precise edits at specific locations.
    """

    name = "edit"
    description = "Edit files with find-and-replace, insert, or delete operations"

    def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "replace")

        match action:
            case "replace":
                return self._replace(
                    path=kwargs.get("path", ""),
                    old=kwargs.get("old", ""),
                    new=kwargs.get("new", ""),
                    count=kwargs.get("count", 1),
                )
            case "insert":
                return self._insert(
                    path=kwargs.get("path", ""),
                    line=kwargs.get("line", 0),
                    content=kwargs.get("content", ""),
                )
            case "delete_lines":
                return self._delete_lines(
                    path=kwargs.get("path", ""),
                    start=kwargs.get("start", 0),
                    end=kwargs.get("end", 0),
                )
            case "patch":
                return self._apply_edits(
                    path=kwargs.get("path", ""),
                    edits=kwargs.get("edits", []),
                )
            case "diff":
                return self._show_diff(
                    path=kwargs.get("path", ""),
                    old_content=kwargs.get("old_content", ""),
                    new_content=kwargs.get("new_content", ""),
                )
            case _:
                return ToolResult(tool=self.name, success=False, error=f"Unknown action: {action}")

    def _replace(self, path: str, old: str, new: str, count: int) -> ToolResult:
        """Find and replace text in a file."""
        if not path:
            return ToolResult(tool=self.name, success=False, error="File path required")
        if not old:
            return ToolResult(tool=self.name, success=False, error="Old text required")

        try:
            p = Path(path)
            content = p.read_text(encoding="utf-8")

            if old not in content:
                return ToolResult(
                    tool=self.name,
                    success=False,
                    error=f"Text not found in {path}",
                    metadata={"path": path},
                )

            occurrences = content.count(old)
            if count == 0:
                new_content = content.replace(old, new)
                replaced = occurrences
            else:
                new_content = content.replace(old, new, count)
                replaced = min(count, occurrences)

            p.write_text(new_content, encoding="utf-8")
            return ToolResult(
                tool=self.name,
                success=True,
                output=f"Replaced {replaced} occurrence(s) in {path}",
                metadata={"path": path, "replacements": replaced},
            )
        except FileNotFoundError:
            return ToolResult(tool=self.name, success=False, error=f"File not found: {path}")
        except OSError as e:
            return ToolResult(tool=self.name, success=False, error=str(e))

    def _insert(self, path: str, line: int, content: str) -> ToolResult:
        """Insert content at a specific line number (1-indexed)."""
        if not path:
            return ToolResult(tool=self.name, success=False, error="File path required")
        if not content:
            return ToolResult(tool=self.name, success=False, error="Content required")

        try:
            p = Path(path)
            lines = p.read_text(encoding="utf-8").splitlines(keepends=True)

            # Convert to 0-indexed, clamp to valid range
            idx = max(0, min(line - 1, len(lines)))
            new_lines = content.splitlines(keepends=True)
            if not new_lines[-1].endswith("\n"):
                new_lines[-1] += "\n"

            lines[idx:idx] = new_lines
            p.write_text("".join(lines), encoding="utf-8")

            return ToolResult(
                tool=self.name,
                success=True,
                output=f"Inserted {len(new_lines)} line(s) at line {line} in {path}",
                metadata={"path": path, "line": line, "lines_inserted": len(new_lines)},
            )
        except FileNotFoundError:
            return ToolResult(tool=self.name, success=False, error=f"File not found: {path}")
        except OSError as e:
            return ToolResult(tool=self.name, success=False, error=str(e))

    def _delete_lines(self, path: str, start: int, end: int) -> ToolResult:
        """Delete lines from start to end (1-indexed, inclusive)."""
        if not path:
            return ToolResult(tool=self.name, success=False, error="File path required")
        if start < 1 or end < start:
            return ToolResult(tool=self.name, success=False, error="Invalid line range")

        try:
            p = Path(path)
            lines = p.read_text(encoding="utf-8").splitlines(keepends=True)

            deleted = lines[start - 1 : end]
            remaining = lines[: start - 1] + lines[end:]
            p.write_text("".join(remaining), encoding="utf-8")

            return ToolResult(
                tool=self.name,
                success=True,
                output=f"Deleted lines {start}-{end} ({len(deleted)} lines) from {path}",
                metadata={"path": path, "lines_deleted": len(deleted)},
            )
        except FileNotFoundError:
            return ToolResult(tool=self.name, success=False, error=f"File not found: {path}")
        except OSError as e:
            return ToolResult(tool=self.name, success=False, error=str(e))

    def _apply_edits(self, path: str, edits: list[dict]) -> ToolResult:
        """Apply multiple find-and-replace edits sequentially."""
        if not path:
            return ToolResult(tool=self.name, success=False, error="File path required")
        if not edits:
            return ToolResult(tool=self.name, success=False, error="Edits list required")

        try:
            p = Path(path)
            content = p.read_text(encoding="utf-8")
            applied = 0

            for edit in edits:
                old = edit.get("old", "")
                new = edit.get("new", "")
                if old and old in content:
                    content = content.replace(old, new, 1)
                    applied += 1

            p.write_text(content, encoding="utf-8")
            return ToolResult(
                tool=self.name,
                success=True,
                output=f"Applied {applied}/{len(edits)} edits to {path}",
                metadata={"path": path, "applied": applied, "total": len(edits)},
            )
        except (FileNotFoundError, OSError) as e:
            return ToolResult(tool=self.name, success=False, error=str(e))

    def _show_diff(self, path: str, old_content: str, new_content: str) -> ToolResult:
        """Generate a unified diff between two versions of content."""
        if not old_content and path:
            try:
                old_content = Path(path).read_text(encoding="utf-8")
            except (FileNotFoundError, OSError) as e:
                return ToolResult(tool=self.name, success=False, error=str(e))

        diff = difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{path}" if path else "a/original",
            tofile=f"b/{path}" if path else "b/modified",
        )
        output = "".join(diff)
        return ToolResult(
            tool=self.name,
            success=True,
            output=output or "(no differences)",
            metadata={"path": path},
        )
