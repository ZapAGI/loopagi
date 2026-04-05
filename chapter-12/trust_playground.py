"""
Chapter 12: Interactive Trust Playground

An interactive terminal demo where the reader plays the role of
the human-in-the-loop, approving or denying agent actions. Trust
builds with approvals, decays with time, and drops with denials.

Watch the trust score change in real-time as you make decisions.
The exponential decay formula runs between your inputs:

    trust(t) = trust_0 * e^(-lambda * t)

This is the interactive version of the trust model the reader
builds into loopagi/safety.py.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass


@dataclass
class TrustEvent:
    """A recorded trust event."""

    time_offset: float
    action: str
    decision: str
    trust_before: float
    trust_after: float


class InteractiveTrust:
    """
    Interactive trust scoring with real-time decay.

    Between each user decision, trust decays exponentially.
    Approvals reinforce trust. Denials penalize it.
    """

    def __init__(
        self,
        initial: float = 0.5,
        decay_rate: float = 0.05,
        reinforce_amount: float = 0.08,
        penalize_amount: float = 0.15,
    ) -> None:
        self._score = initial
        self._decay_rate = decay_rate
        self._reinforce = reinforce_amount
        self._penalize = penalize_amount
        self._last_update = time.time()
        self._start_time = time.time()
        self.events: list[TrustEvent] = []

    @property
    def score(self) -> float:
        """Current trust with decay applied."""
        elapsed = time.time() - self._last_update
        decayed = self._score * math.exp(-self._decay_rate * elapsed)
        return max(0.05, min(1.0, decayed))

    @property
    def level(self) -> str:
        s = self.score
        if s >= 0.8:
            return "HIGH"
        elif s >= 0.5:
            return "MEDIUM"
        elif s >= 0.3:
            return "LOW"
        return "MINIMAL"

    def approve(self, action: str) -> float:
        """User approved an action. Trust increases."""
        before = self.score
        self._score = min(1.0, self.score + self._reinforce)
        self._last_update = time.time()
        self.events.append(TrustEvent(
            time_offset=time.time() - self._start_time,
            action=action,
            decision="APPROVED",
            trust_before=before,
            trust_after=self._score,
        ))
        return self._score

    def deny(self, action: str) -> float:
        """User denied an action. Trust decreases."""
        before = self.score
        self._score = max(0.05, self.score - self._penalize)
        self._last_update = time.time()
        self.events.append(TrustEvent(
            time_offset=time.time() - self._start_time,
            action=action,
            decision="DENIED",
            trust_before=before,
            trust_after=self._score,
        ))
        return self._score

    def render_bar(self, width: int = 40) -> str:
        """Visual trust bar."""
        s = self.score
        filled = int(s * width)
        bar = "=" * filled + "." * (width - filled)

        if s >= 0.8:
            return f"[{bar}]"
        elif s >= 0.5:
            return f"[{bar}]"
        elif s >= 0.3:
            return f"[{bar}]"
        return f"[{bar}]"


# Simulated agent actions for the playground
AGENT_ACTIONS = [
    ("Read file: main.py", "safe", "The coder agent wants to read main.py"),
    ("Execute: python main.py", "safe", "Run the main application"),
    ("Write file: utils.py", "caution", "Create a new utility module"),
    ("Execute: pip install requests", "caution", "Install a Python package"),
    ("Execute: git push origin main", "caution", "Push code to remote"),
    ("Execute: rm -r build/", "caution", "Delete the build directory"),
    ("Read file: .env", "caution", "Access environment variables"),
    ("Execute: docker rm -f webapp", "caution", "Remove a Docker container"),
    ("Write file: /etc/hosts", "dangerous", "Modify system hosts file"),
    ("Execute: sudo apt update", "dangerous", "System package update"),
    ("Execute: git reset --hard", "dangerous", "Discard all uncommitted changes"),
    ("Read file: config.py", "safe", "Read project configuration"),
    ("Execute: pytest tests/", "safe", "Run the test suite"),
    ("Write file: README.md", "safe", "Update documentation"),
]


def run_playground() -> None:
    """Run the interactive trust playground."""
    print("Chapter 12: Interactive Trust Playground")
    print("=" * 60)
    print()
    print("You are the human-in-the-loop. Approve or deny each action.")
    print("Trust builds with approvals and decays with time.")
    print("Denials cause a sharp trust drop.")
    print()
    print("  trust(t) = trust_0 * e^(-0.05 * t)")
    print("  Approve: +0.08  |  Deny: -0.15  |  Decay: continuous")
    print()
    print("Press Enter quickly to see trust hold. Wait to see it decay.")
    print("Type 'q' to quit at any time.")
    print()

    trust = InteractiveTrust()

    for i, (action, risk, description) in enumerate(AGENT_ACTIONS):
        bar = trust.render_bar()
        level = trust.level
        score = trust.score

        print(f"\n{'─' * 60}")
        print(f"  Trust: {score:.3f} ({level})  {bar}")
        print(f"\n  Agent proposes: {action}")
        print(f"  Risk level: {risk.upper()}")
        print(f"  Reason: {description}")

        try:
            response = input("\n  Approve? (y/n/q): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if response in ("q", "quit", "exit"):
            break

        if response in ("y", "yes", ""):
            new_score = trust.approve(action)
            print(f"  APPROVED. Trust: {score:.3f} -> {new_score:.3f} (+)")
        else:
            new_score = trust.deny(action)
            print(f"  DENIED. Trust: {score:.3f} -> {new_score:.3f} (-)")

    # Summary
    print(f"\n{'=' * 60}")
    print("SESSION SUMMARY")
    print(f"{'=' * 60}")
    print(f"\n  Final trust: {trust.score:.3f} ({trust.level})")
    print(f"  Decisions: {len(trust.events)}")

    approved = sum(1 for e in trust.events if e.decision == "APPROVED")
    denied = len(trust.events) - approved
    print(f"  Approved: {approved}  |  Denied: {denied}")

    if trust.events:
        print(f"\n  {'Time':<8} {'Decision':<10} {'Before':<8} {'After':<8} {'Action'}")
        print(f"  {'-'*8} {'-'*10} {'-'*8} {'-'*8} {'-'*25}")
        for e in trust.events:
            print(
                f"  {e.time_offset:>6.1f}s {e.decision:<10} "
                f"{e.trust_before:<8.3f} {e.trust_after:<8.3f} {e.action[:25]}"
            )

    print()
    print("Trust is not a boolean. It is a function that decays")
    print("without reinforcement. Every approval matters.")


def demo_non_interactive() -> None:
    """Non-interactive demo for automated testing."""
    print("Chapter 12: Trust Playground (Non-Interactive Demo)")
    print("=" * 60)
    print()

    trust = InteractiveTrust()

    decisions = [
        ("Read file: main.py", True),
        ("Execute: python main.py", True),
        ("Write file: utils.py", True),
        ("Execute: pip install requests", True),
        ("Execute: rm -r build/", False),
        ("Execute: sudo apt update", False),
        ("Read file: config.py", True),
        ("Execute: pytest tests/", True),
    ]

    print(f"  {'Action':<35} {'Decision':<10} {'Trust':<8} {'Level'}")
    print(f"  {'-'*35} {'-'*10} {'-'*8} {'-'*8}")

    for action, approved in decisions:
        if approved:
            trust.approve(action)
            decision = "APPROVE"
        else:
            trust.deny(action)
            decision = "DENY"

        print(f"  {action:<35} {decision:<10} {trust.score:<8.3f} {trust.level}")

    print(f"\n  Final trust: {trust.score:.3f} ({trust.level})")
    print("  4 approvals built trust. 2 denials caused sharp drops.")
    print("  This is the trust model from loopagi/safety.py in action.")


def demo() -> None:
    """Run the appropriate demo mode."""
    import sys
    if sys.stdin.isatty():
        run_playground()
    else:
        demo_non_interactive()


if __name__ == "__main__":
    demo()
