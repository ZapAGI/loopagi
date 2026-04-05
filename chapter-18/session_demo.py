"""
Chapter 18: Session-as-Git Demo

Every interaction is a git commit. Every session is a repo.
If it is not versioned, it did not happen.

Provenance is not a feature. It is a moral commitment to transparency.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from loopagi.core.session import SessionLogger


def demo() -> None:
    """Demonstrate session-as-git provenance logging."""
    print("Chapter 18: Session-as-Git Innovation")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        session_dir = Path(tmpdir) / "demo-session"
        session = SessionLogger(session_dir)

        # Start a session
        session.start("Build a REST API with FastAPI")
        print(f"\nSession started in: {session_dir}")

        # Simulate a conversation
        interactions = [
            ("user", "Create a FastAPI app with a /health endpoint"),
            ("agent", "I'll create the FastAPI application with a health check endpoint."),
            ("user", "Add a /users endpoint with GET and POST"),
            ("agent", "Adding the /users endpoint with both methods."),
        ]

        for role, message in interactions:
            session.log_message(role, message)
            print(f"  [{role}] {message[:60]}")

        # Simulate commands
        commands = [
            ("mkdir -p api", 0),
            ("touch api/__init__.py api/main.py", 0),
            ("uv run pytest tests/ -v", 0),
        ]

        for cmd, exit_code in commands:
            session.log_command(cmd, exit_code)
            print(f"  [cmd] {cmd}")

        # Simulate file changes
        files = ["api/__init__.py", "api/main.py", "tests/test_api.py"]
        for f in files:
            session.log_file_write(f)
            print(f"  [file] {f}")

        # End session
        session.end()

        # Show generated artifacts
        print("\nGenerated Artifacts:")
        print("-" * 50)
        for artifact in ["HISTORY.md", "COMMANDS.md", "FILES.md", "PROGRESS.md"]:
            path = session_dir / artifact
            if path.exists():
                content = path.read_text(encoding="utf-8")
                lines = len(content.splitlines())
                print(f"\n  {artifact} ({lines} lines):")
                # Show first few lines
                for line in content.splitlines()[:8]:
                    print(f"    {line}")
                if lines > 8:
                    print(f"    ... ({lines - 8} more lines)")

        # Show git log
        import git
        repo = git.Repo(session_dir)
        print(f"\n\nGit Log ({len(list(repo.iter_commits()))} commits):")
        print("-" * 50)
        for commit in list(repo.iter_commits())[:10]:
            print(f"  {commit.hexsha[:7]} {commit.message.strip()}")

    print()
    print("Every action is a commit. Every session is a repo.")
    print("Provenance answers: who wrote this code, and when?")


if __name__ == "__main__":
    demo()
