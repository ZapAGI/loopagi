"""
Chapter 18: The Session-as-Git Innovation

Every interaction is a git commit. Every session is a repo.
If it is not versioned, it did not happen.

Usage:
    from loopagi.core.session import SessionLogger

    session = SessionLogger("./my-session")
    session.start("Build a REST API")

    session.log_message("user", "Create a FastAPI app with /health endpoint")
    session.log_message("agent", "I'll create the FastAPI app now.")
    session.log_command("mkdir api && touch api/main.py")
    session.log_file_write("api/main.py")

    session.end()
    # Generates: HISTORY.md, COMMANDS.md, FILES.md, PROGRESS.md
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import git

logger = logging.getLogger(__name__)


@dataclass
class SessionMessage:
    """A message in the session history."""

    role: str  # "user" or "agent"
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class SessionCommand:
    """A command executed during the session."""

    command: str
    exit_code: int = 0
    output: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class SessionFileChange:
    """A file change during the session."""

    path: str
    action: str = "write"  # write, create, delete, modify
    timestamp: float = field(default_factory=time.time)


class SessionLogger:
    """
    Session-as-git provenance logger.

    Every session is a git repository. Every action is a commit.
    This creates a complete, versioned audit trail of everything
    that happened during an AI-assisted coding session.

    Automatic artifacts generated:
    - HISTORY.md: Conversation transcript
    - COMMANDS.md: All commands executed
    - FILES.md: All files created/modified
    - PROGRESS.md: Session progress summary

    Provenance is not a feature. It is a moral commitment
    to transparency.
    """

    def __init__(self, session_dir: Path | str) -> None:
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self._messages: list[SessionMessage] = []
        self._commands: list[SessionCommand] = []
        self._file_changes: list[SessionFileChange] = []
        self._start_time: float = 0.0
        self._task: str = ""
        self._repo: git.Repo | None = None
        self._active = False

    def start(self, task: str) -> None:
        """Start a new session with a task description."""
        self._task = task
        self._start_time = time.time()
        self._active = True

        # Initialize git repo
        if not (self.session_dir / ".git").exists():
            self._repo = git.Repo.init(self.session_dir)
        else:
            self._repo = git.Repo(self.session_dir)

        # Create session metadata
        metadata = {
            "task": task,
            "started_at": datetime.now().isoformat(),
            "status": "active",
        }
        meta_path = self.session_dir / ".session.json"
        import json
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        self._commit("Session started: " + task[:60])
        logger.info("Session started: %s", task[:60])

    def log_message(self, role: str, content: str) -> None:
        """Log a conversation message."""
        if not self._active:
            return
        self._messages.append(SessionMessage(role=role, content=content))
        self._regenerate_artifacts()
        self._commit(f"[{role}] {content[:50]}")

    def log_command(self, command: str, exit_code: int = 0, output: str = "") -> None:
        """Log a command execution."""
        if not self._active:
            return
        self._commands.append(SessionCommand(
            command=command, exit_code=exit_code, output=output,
        ))
        self._regenerate_artifacts()
        self._commit(f"[cmd] {command[:50]}")

    def log_file_write(self, path: str, action: str = "write") -> None:
        """Log a file change."""
        if not self._active:
            return
        self._file_changes.append(SessionFileChange(path=path, action=action))
        self._regenerate_artifacts()
        self._commit(f"[file:{action}] {path}")

    def end(self) -> None:
        """End the session and generate final artifacts."""
        if not self._active:
            return
        self._active = False
        self._regenerate_artifacts()

        # Update metadata
        import json
        meta_path = self.session_dir / ".session.json"
        if meta_path.exists():
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            metadata["status"] = "completed"
            metadata["ended_at"] = datetime.now().isoformat()
            metadata["duration_seconds"] = time.time() - self._start_time
            metadata["message_count"] = len(self._messages)
            metadata["command_count"] = len(self._commands)
            metadata["file_change_count"] = len(self._file_changes)
            meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        self._commit("Session completed")
        logger.info(
            "Session ended: %d messages, %d commands, %d file changes",
            len(self._messages), len(self._commands), len(self._file_changes),
        )

    def _regenerate_artifacts(self) -> None:
        """Regenerate all markdown artifacts."""
        self._generate_history()
        self._generate_commands()
        self._generate_files()
        self._generate_progress()

    def _generate_history(self) -> None:
        """Generate HISTORY.md: conversation transcript."""
        lines = [
            "# Session History",
            "",
            f"**Task:** {self._task}",
            f"**Started:** {datetime.fromtimestamp(self._start_time).isoformat()}",
            "",
            "---",
            "",
        ]
        for msg in self._messages:
            ts = datetime.fromtimestamp(msg.timestamp).strftime("%H:%M:%S")
            role_label = "USER" if msg.role == "user" else "AGENT"
            lines.append(f"### [{ts}] {role_label}")
            lines.append("")
            lines.append(msg.content)
            lines.append("")

        path = self.session_dir / "HISTORY.md"
        path.write_text("\n".join(lines), encoding="utf-8")

    def _generate_commands(self) -> None:
        """Generate COMMANDS.md: all commands executed."""
        lines = [
            "# Commands Executed",
            "",
            f"**Total:** {len(self._commands)}",
            "",
        ]
        for i, cmd in enumerate(self._commands, 1):
            ts = datetime.fromtimestamp(cmd.timestamp).strftime("%H:%M:%S")
            status = "OK" if cmd.exit_code == 0 else f"EXIT {cmd.exit_code}"
            lines.append(f"{i}. `{cmd.command}` [{status}] ({ts})")

        path = self.session_dir / "COMMANDS.md"
        path.write_text("\n".join(lines), encoding="utf-8")

    def _generate_files(self) -> None:
        """Generate FILES.md: all files created/modified."""
        lines = [
            "# Files Changed",
            "",
            f"**Total:** {len(self._file_changes)}",
            "",
        ]
        for change in self._file_changes:
            ts = datetime.fromtimestamp(change.timestamp).strftime("%H:%M:%S")
            lines.append(f"- [{change.action}] `{change.path}` ({ts})")

        path = self.session_dir / "FILES.md"
        path.write_text("\n".join(lines), encoding="utf-8")

    def _generate_progress(self) -> None:
        """Generate PROGRESS.md: session progress summary."""
        elapsed = time.time() - self._start_time if self._start_time else 0
        minutes = int(elapsed / 60)

        lines = [
            "# Session Progress",
            "",
            f"**Task:** {self._task}",
            f"**Duration:** {minutes} minutes",
            f"**Status:** {'Active' if self._active else 'Completed'}",
            "",
            "## Statistics",
            "",
            f"- Messages: {len(self._messages)}",
            f"- Commands: {len(self._commands)}",
            f"- File changes: {len(self._file_changes)}",
            "",
        ]

        path = self.session_dir / "PROGRESS.md"
        path.write_text("\n".join(lines), encoding="utf-8")

    def _commit(self, message: str) -> None:
        """Create a git commit with the current state."""
        if not self._repo:
            return
        try:
            self._repo.index.add("*")
            if self._repo.is_dirty() or self._repo.untracked_files:
                self._repo.index.add(self._repo.untracked_files)
                self._repo.index.commit(message)
        except Exception as e:
            logger.debug("Git commit skipped: %s", e)

    def __repr__(self) -> str:
        return (
            f"SessionLogger(task='{self._task[:40]}', "
            f"messages={len(self._messages)}, active={self._active})"
        )
