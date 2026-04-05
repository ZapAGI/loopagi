"""
Chapter 10: The Context Engine

Rules parser, action tracker, and repository map.
Context is not data. It is relevance.

Usage:
    from loopagi.knowledge.context import RulesParser, ActionTracker, RepoMap

    # Parse project rules
    rules = RulesParser.parse(".looprules")

    # Track actions for situational awareness
    tracker = ActionTracker()
    tracker.record("file_write", "Created main.py")

    # Generate dependency map
    repo_map = RepoMap("./src")
    print(repo_map.generate())
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


# --- Rules Parser ---


@dataclass
class Rule:
    """A single rule parsed from .looprules."""

    section: str
    content: str
    source: str  # "project" or "global"


class RulesParser:
    """
    Parse .looprules files (project-level) and global rules.

    Rules are markdown files with ## headings as sections and
    - bullets as individual rules. Project rules override global.

    Format:
        ## Code Style
        - Use type hints on all functions
        - Prefer composition over inheritance

        ## Testing
        - Every function needs at least one test
        - Use pytest, not unittest
    """

    @staticmethod
    def parse(path: Path | str) -> list[Rule]:
        """Parse a .looprules file into a list of Rule objects."""
        path = Path(path)
        if not path.exists():
            logger.warning("Rules file not found: %s", path)
            return []

        rules: list[Rule] = []
        current_section = "General"
        source = "project" if path.name == ".looprules" else "global"

        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("## "):
                current_section = line[3:].strip()
            elif line.startswith("- "):
                rules.append(Rule(
                    section=current_section,
                    content=line[2:].strip(),
                    source=source,
                ))

        logger.info("Parsed %d rules from %s", len(rules), path)
        return rules

    @staticmethod
    def merge(project_rules: list[Rule], global_rules: list[Rule]) -> list[Rule]:
        """Merge project and global rules. Project rules override global."""
        project_sections = {r.section for r in project_rules}
        merged = list(project_rules)
        for rule in global_rules:
            if rule.section not in project_sections:
                merged.append(rule)
        return merged

    @staticmethod
    def format_for_prompt(rules: list[Rule], max_chars: int = 2000) -> str:
        """Format rules for injection into an agent's system prompt."""
        if not rules:
            return ""

        sections: dict[str, list[str]] = {}
        for rule in rules:
            sections.setdefault(rule.section, []).append(rule.content)

        lines = ["PROJECT RULES:"]
        total = len(lines[0])
        for section, items in sections.items():
            header = f"\n## {section}"
            if total + len(header) > max_chars:
                break
            lines.append(header)
            total += len(header)
            for item in items:
                bullet = f"- {item}"
                if total + len(bullet) > max_chars:
                    break
                lines.append(bullet)
                total += len(bullet)

        return "\n".join(lines)


# --- Action Tracker ---


class ActionType(str, Enum):
    """Types of tracked actions."""

    FILE_WRITE = "file_write"
    FILE_READ = "file_read"
    FILE_EDIT = "file_edit"
    SHELL_COMMAND = "shell_command"
    CODE_EXEC = "code_exec"
    AGENT_DELEGATION = "agent_delegation"
    TOOL_CALL = "tool_call"
    ERROR = "error"
    MEMORY_STORE = "memory_store"
    RAG_QUERY = "rag_query"
    GIT_OPERATION = "git_operation"
    CONTEXT_ADD = "context_add"
    PIPELINE = "pipeline"
    WEB_SEARCH = "web_search"


@dataclass
class Action:
    """A single tracked action."""

    action_type: ActionType
    description: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


class ActionTracker:
    """
    Ring buffer of recent actions for situational awareness.

    Agents use this to understand what has happened recently,
    providing context for their next decision. The buffer has a
    fixed size to manage memory, keeping only the most recent
    actions (like a sliding window of consciousness).
    """

    def __init__(self, max_actions: int = 100) -> None:
        self._actions: deque[Action] = deque(maxlen=max_actions)
        logger.info("ActionTracker initialized (max=%d)", max_actions)

    def record(
        self,
        action_type: str | ActionType,
        description: str,
        metadata: dict | None = None,
    ) -> None:
        """Record a new action."""
        if isinstance(action_type, str):
            action_type = ActionType(action_type)

        action = Action(
            action_type=action_type,
            description=description,
            metadata=metadata or {},
        )
        self._actions.append(action)
        logger.debug("Tracked: [%s] %s", action_type.value, description[:80])

    def recent(self, count: int = 10) -> list[Action]:
        """Get the most recent actions."""
        return list(self._actions)[-count:]

    def format_for_prompt(self, max_items: int = 10) -> str:
        """Format recent actions for injection into an agent's prompt."""
        actions = self.recent(max_items)
        if not actions:
            return ""

        lines = ["RECENT ACTIONS:"]
        for action in reversed(actions):
            lines.append(f"- [{action.action_type.value}] {action.description}")
        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all tracked actions."""
        self._actions.clear()

    @property
    def count(self) -> int:
        return len(self._actions)


# --- Repository Map ---


@dataclass
class FileNode:
    """A node in the repository dependency graph."""

    path: str
    imports: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    lines: int = 0


class RepoMap:
    """
    Repository map using dependency analysis.

    Generates a structured overview of a codebase by analyzing
    imports, function definitions, and class definitions across
    all Python files. This gives agents a "bird's eye view" of
    the project structure.

    In the full LoopAGI implementation, this uses tree-sitter
    for 165+ language support and PageRank for importance weighting.
    This companion version focuses on Python with regex parsing.
    """

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.nodes: dict[str, FileNode] = {}

    def scan(self) -> dict[str, FileNode]:
        """Scan the repository and build the dependency graph."""
        self.nodes.clear()
        for py_file in sorted(self.root.rglob("*.py")):
            if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                continue
            node = self._analyze_file(py_file)
            rel_path = str(py_file.relative_to(self.root))
            self.nodes[rel_path] = node

        logger.info("Scanned %d Python files in %s", len(self.nodes), self.root)
        return self.nodes

    def generate(self, max_files: int = 50) -> str:
        """Generate a formatted repository map string."""
        if not self.nodes:
            self.scan()

        lines = [f"REPOSITORY MAP ({len(self.nodes)} files):"]
        for path, node in list(self.nodes.items())[:max_files]:
            lines.append(f"\n  {path} ({node.lines} lines)")
            for cls in node.classes:
                lines.append(f"    class {cls}")
            for func in node.functions[:10]:
                lines.append(f"    def {func}()")
            if node.imports:
                lines.append(f"    imports: {', '.join(node.imports[:5])}")

        return "\n".join(lines)

    def _analyze_file(self, path: Path) -> FileNode:
        """Analyze a single Python file for imports, functions, and classes."""
        import re

        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return FileNode(path=str(path))

        lines = content.splitlines()
        imports = []
        functions = []
        classes = []

        for line in lines:
            stripped = line.strip()
            # Imports
            if stripped.startswith("import ") or stripped.startswith("from "):
                match = re.match(r"(?:from\s+(\S+)|import\s+(\S+))", stripped)
                if match:
                    module = match.group(1) or match.group(2)
                    imports.append(module.split(".")[0])
            # Functions
            elif stripped.startswith("def "):
                match = re.match(r"def\s+(\w+)", stripped)
                if match:
                    functions.append(match.group(1))
            # Classes
            elif stripped.startswith("class "):
                match = re.match(r"class\s+(\w+)", stripped)
                if match:
                    classes.append(match.group(1))

        return FileNode(
            path=str(path),
            imports=list(set(imports)),
            functions=functions,
            classes=classes,
            lines=len(lines),
        )

    def __repr__(self) -> str:
        return f"RepoMap(root='{self.root}', files={len(self.nodes)})"
