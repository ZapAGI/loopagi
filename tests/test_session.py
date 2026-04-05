"""Tests for loopagi.session module."""

from __future__ import annotations

from pathlib import Path

from loopagi.core.session import SessionLogger


class TestSessionLogger:
    """Tests for the SessionLogger."""

    def test_start_creates_git_repo(self, tmp_path: Path) -> None:
        session_dir = tmp_path / "session"
        logger = SessionLogger(session_dir)
        logger.start("test task")
        assert (session_dir / ".git").exists()
        assert (session_dir / ".session.json").exists()

    def test_log_message(self, tmp_path: Path) -> None:
        session_dir = tmp_path / "session"
        logger = SessionLogger(session_dir)
        logger.start("test")
        logger.log_message("user", "hello")
        logger.log_message("agent", "hi there")
        assert (session_dir / "HISTORY.md").exists()
        content = (session_dir / "HISTORY.md").read_text()
        assert "hello" in content
        assert "hi there" in content

    def test_log_command(self, tmp_path: Path) -> None:
        session_dir = tmp_path / "session"
        logger = SessionLogger(session_dir)
        logger.start("test")
        logger.log_command("pytest tests/", exit_code=0)
        assert (session_dir / "COMMANDS.md").exists()
        content = (session_dir / "COMMANDS.md").read_text()
        assert "pytest" in content

    def test_log_file_write(self, tmp_path: Path) -> None:
        session_dir = tmp_path / "session"
        logger = SessionLogger(session_dir)
        logger.start("test")
        logger.log_file_write("main.py", action="create")
        assert (session_dir / "FILES.md").exists()
        content = (session_dir / "FILES.md").read_text()
        assert "main.py" in content

    def test_end_generates_all_artifacts(self, tmp_path: Path) -> None:
        session_dir = tmp_path / "session"
        logger = SessionLogger(session_dir)
        logger.start("build something")
        logger.log_message("user", "do a thing")
        logger.log_command("echo hi")
        logger.log_file_write("test.py")
        logger.end()

        for artifact in ["HISTORY.md", "COMMANDS.md", "FILES.md", "PROGRESS.md"]:
            assert (session_dir / artifact).exists(), f"Missing: {artifact}"

    def test_end_updates_metadata(self, tmp_path: Path) -> None:
        import json
        session_dir = tmp_path / "session"
        logger = SessionLogger(session_dir)
        logger.start("test")
        logger.end()

        meta = json.loads((session_dir / ".session.json").read_text())
        assert meta["status"] == "completed"
        assert "ended_at" in meta

    def test_progress_md_content(self, tmp_path: Path) -> None:
        session_dir = tmp_path / "session"
        logger = SessionLogger(session_dir)
        logger.start("my task")
        logger.log_message("user", "msg1")
        logger.log_message("agent", "msg2")
        logger.log_command("cmd1")
        logger.end()

        content = (session_dir / "PROGRESS.md").read_text()
        assert "my task" in content
        assert "Completed" in content
        assert "Messages: 2" in content
        assert "Commands: 1" in content

    def test_inactive_session_ignores_logs(self, tmp_path: Path) -> None:
        session_dir = tmp_path / "session"
        logger = SessionLogger(session_dir)
        # Do NOT start the session
        logger.log_message("user", "should be ignored")
        logger.log_command("also ignored")
        assert not (session_dir / "HISTORY.md").exists()

    def test_git_commits_created(self, tmp_path: Path) -> None:
        import git
        session_dir = tmp_path / "session"
        logger = SessionLogger(session_dir)
        logger.start("test")
        logger.log_message("user", "hello")
        logger.end()

        repo = git.Repo(session_dir)
        commits = list(repo.iter_commits())
        assert len(commits) >= 3  # start + message + end

    def test_repr(self, tmp_path: Path) -> None:
        logger = SessionLogger(tmp_path / "s")
        logger._task = "test"
        r = repr(logger)
        assert "SessionLogger" in r
