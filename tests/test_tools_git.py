"""Tests for loopagi.tools_git module."""

from __future__ import annotations

import subprocess
from pathlib import Path

from loopagi.tools.git import GitTool


class TestGitTool:
    """Tests for the GitTool."""

    def _init_repo(self, tmp_path: Path) -> Path:
        """Initialize a git repo for testing."""
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=str(tmp_path), capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=str(tmp_path), capture_output=True,
        )
        (tmp_path / "README.md").write_text("# Test\n")
        subprocess.run(["git", "add", "-A"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=str(tmp_path), capture_output=True,
        )
        return tmp_path

    def test_status_clean(self, tmp_path: Path) -> None:
        repo = self._init_repo(tmp_path)
        tool = GitTool(cwd=str(repo))
        result = tool.execute(action="status")
        assert result.success
        assert result.output == "" or "nothing to commit" not in result.error

    def test_status_dirty(self, tmp_path: Path) -> None:
        repo = self._init_repo(tmp_path)
        (repo / "new_file.txt").write_text("new content")
        tool = GitTool(cwd=str(repo))
        result = tool.execute(action="status")
        assert result.success
        assert "new_file" in result.output

    def test_log(self, tmp_path: Path) -> None:
        repo = self._init_repo(tmp_path)
        tool = GitTool(cwd=str(repo))
        result = tool.execute(action="log", count=5)
        assert result.success
        assert "initial" in result.output

    def test_add_and_commit(self, tmp_path: Path) -> None:
        repo = self._init_repo(tmp_path)
        (repo / "new.txt").write_text("content")
        tool = GitTool(cwd=str(repo))

        result = tool.execute(action="add", path="-A")
        assert result.success

        result = tool.execute(action="commit", message="add new file")
        assert result.success

    def test_commit_no_message(self, tmp_path: Path) -> None:
        repo = self._init_repo(tmp_path)
        tool = GitTool(cwd=str(repo))
        result = tool.execute(action="commit", message="")
        assert not result.success

    def test_diff_clean(self, tmp_path: Path) -> None:
        repo = self._init_repo(tmp_path)
        tool = GitTool(cwd=str(repo))
        result = tool.execute(action="diff")
        assert result.success

    def test_branch(self, tmp_path: Path) -> None:
        repo = self._init_repo(tmp_path)
        tool = GitTool(cwd=str(repo))
        result = tool.execute(action="branch")
        assert result.success
        assert "main" in result.output or "master" in result.output

    def test_checkout_new_branch(self, tmp_path: Path) -> None:
        repo = self._init_repo(tmp_path)
        tool = GitTool(cwd=str(repo))
        result = tool.execute(action="checkout", target="feature/test", create=True)
        assert result.success

    def test_unknown_action(self, tmp_path: Path) -> None:
        tool = GitTool(cwd=str(tmp_path))
        result = tool.execute(action="unknown_xyz")
        assert not result.success

    def test_name(self) -> None:
        tool = GitTool()
        assert tool.name == "git"
