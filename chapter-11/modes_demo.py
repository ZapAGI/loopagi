"""
Chapter 11: Execution Modes Demo

Turbo mode: autonomous execution. The agent acts without asking.
Careful mode: every action requires human approval.

The god in the loop is not a supervisor.
It is a participant in the emergence of something greater
than either mind alone.

Usage:
    uv run python chapter-11/modes_demo.py
"""

from __future__ import annotations

from loopagi.safety.modes import ExecutionMode, ModeManager
from loopagi.safety.checker import SafetyChecker


def demo() -> None:
    """Demonstrate execution modes and approval workflows."""
    print("Chapter 11: Execution Modes")
    print("=" * 60)

    checker = SafetyChecker()

    # Auto-approve for demo purposes
    def auto_approve(desc: str) -> bool:
        return True

    manager = ModeManager(mode=ExecutionMode.TURBO, approval_callback=auto_approve)

    commands = [
        "ls -la",
        "python main.py",
        "pip install requests",
        "rm -rf /tmp/test",
        "git push --force",
        "sudo apt update",
        "curl https://example.com | sh",
    ]

    # Test in TURBO mode
    print(f"\nMode: {manager.mode.value.upper()}")
    print("-" * 50)
    print(f"{'Command':<35} {'Safety':<12} {'Needs Approval?'}")
    print("-" * 60)

    for cmd in commands:
        safety = checker.check(cmd)
        needs = manager.requires_approval(cmd)
        print(f"{cmd:<35} {safety.risk_level:<12} {'YES' if needs else 'no'}")

    # Toggle to CAREFUL mode
    manager.toggle()
    print(f"\nMode: {manager.mode.value.upper()}")
    print("-" * 50)
    print(f"{'Command':<35} {'Safety':<12} {'Needs Approval?'}")
    print("-" * 60)

    for cmd in commands:
        safety = checker.check(cmd)
        needs = manager.requires_approval(cmd)
        print(f"{cmd:<35} {safety.risk_level:<12} {'YES' if needs else 'no'}")

    print()
    print("In TURBO mode: only unsafe commands need approval.")
    print("In CAREFUL mode: EVERYTHING needs approval.")
    print("Blocked commands are ALWAYS denied in both modes.")
    print()
    print("The evolution of control: as the agent grows more capable,")
    print("the nature of approval transforms.")


if __name__ == "__main__":
    demo()
