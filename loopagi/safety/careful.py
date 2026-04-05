"""
Chapter 14: The Careful Mode Manifesto

Careful mode approval workflows. Friction is not the enemy of
progress. It is the guardian of intention.

The Careful Mode Manifesto (7 Principles):
1. Every action is a proposal until a human approves it.
2. The cost of asking is always less than the cost of undoing.
3. Transparency is not optional. The agent must show its work.
4. Approval is not a bottleneck. It is a quality gate.
5. The human's "no" is always final and requires no justification.
6. Speed serves the human. Safety serves everyone.
7. The measure of an AI system is not how fast it acts, but how wisely it waits.

Usage:
    from loopagi.safety.careful import CarefulSession, ActionProposal

    session = CarefulSession()
    proposal = ActionProposal(
        action="shell_command",
        description="Install pytest package",
        command="pip install pytest",
        risk_level="caution",
    )
    result = session.propose(proposal)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


MANIFESTO = [
    "Every action is a proposal until a human approves it.",
    "The cost of asking is always less than the cost of undoing.",
    "Transparency is not optional. The agent must show its work.",
    "Approval is not a bottleneck. It is a quality gate.",
    "The human's 'no' is always final and requires no justification.",
    "Speed serves the human. Safety serves everyone.",
    "The measure of an AI system is not how fast it acts, but how wisely it waits.",
]


class ProposalStatus(str, Enum):
    """Status of an action proposal."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    AUTO_APPROVED = "auto_approved"
    BLOCKED = "blocked"


@dataclass
class ActionProposal:
    """A proposed action awaiting approval."""

    action: str
    description: str
    command: str = ""
    risk_level: str = "safe"  # safe, caution, blocked
    reasoning: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    status: ProposalStatus = ProposalStatus.PENDING
    timestamp: float = field(default_factory=time.time)


@dataclass
class ApprovalResult:
    """Result of an approval request."""

    proposal: ActionProposal
    approved: bool
    response_time: float = 0.0
    reason: str = ""


class CarefulSession:
    """
    Careful mode session manager.

    In careful mode, every action the agent wants to take is
    presented as a proposal. The human reviews and approves or
    denies each one. This creates an explicit audit trail of
    decisions and their justifications.

    The philosophical case for patience: building AI that knows
    when to wait is harder than building AI that acts quickly.
    But it is infinitely more trustworthy.
    """

    def __init__(
        self,
        approval_callback: Callable[[ActionProposal], bool] | None = None,
        auto_approve_safe: bool = False,
    ) -> None:
        self._approval_callback = approval_callback or self._terminal_approval
        self._auto_approve_safe = auto_approve_safe
        self._proposals: list[ActionProposal] = []
        self._results: list[ApprovalResult] = []
        logger.info(
            "CarefulSession started (auto_approve_safe=%s)", auto_approve_safe,
        )

    def propose(self, proposal: ActionProposal) -> ApprovalResult:
        """
        Submit an action proposal for approval.

        Blocked actions are immediately denied.
        Safe actions may be auto-approved if configured.
        All others require human approval.
        """
        self._proposals.append(proposal)

        # Blocked actions are always denied
        if proposal.risk_level == "blocked":
            proposal.status = ProposalStatus.BLOCKED
            result = ApprovalResult(
                proposal=proposal,
                approved=False,
                reason="Action matches a blocked pattern",
            )
            self._results.append(result)
            logger.warning("BLOCKED: %s", proposal.description)
            return result

        # Auto-approve safe actions if configured
        if self._auto_approve_safe and proposal.risk_level == "safe":
            proposal.status = ProposalStatus.AUTO_APPROVED
            result = ApprovalResult(
                proposal=proposal,
                approved=True,
                reason="Auto-approved (safe action)",
            )
            self._results.append(result)
            logger.info("AUTO-APPROVED: %s", proposal.description)
            return result

        # Request human approval
        start = time.time()
        approved = self._approval_callback(proposal)
        elapsed = time.time() - start

        proposal.status = (
            ProposalStatus.APPROVED if approved else ProposalStatus.DENIED
        )
        result = ApprovalResult(
            proposal=proposal,
            approved=approved,
            response_time=elapsed,
            reason="Human approved" if approved else "Human denied",
        )
        self._results.append(result)
        return result

    @property
    def approval_rate(self) -> float:
        """Calculate the approval rate for this session."""
        if not self._results:
            return 0.0
        approved = sum(1 for r in self._results if r.approved)
        return approved / len(self._results)

    @property
    def summary(self) -> dict[str, int]:
        """Summary of proposal outcomes."""
        counts: dict[str, int] = {
            "total": len(self._results),
            "approved": 0,
            "denied": 0,
            "auto_approved": 0,
            "blocked": 0,
        }
        for result in self._results:
            status = result.proposal.status.value
            if status in counts:
                counts[status] += 1
        return counts

    @staticmethod
    def _terminal_approval(proposal: ActionProposal) -> bool:
        """Default approval callback: prompt in terminal with full context."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text

        console = Console()

        # Build proposal display
        content = Text()
        content.append("Action: ", style="bold")
        content.append(f"{proposal.action}\n")
        content.append("Description: ", style="bold")
        content.append(f"{proposal.description}\n")
        if proposal.command:
            content.append("Command: ", style="bold")
            content.append(f"{proposal.command}\n", style="cyan")
        content.append("Risk Level: ", style="bold")
        risk_style = {
            "safe": "green",
            "caution": "yellow",
            "blocked": "red bold",
        }.get(proposal.risk_level, "white")
        content.append(f"{proposal.risk_level.upper()}\n", style=risk_style)
        if proposal.reasoning:
            content.append("Reasoning: ", style="bold")
            content.append(f"{proposal.reasoning}\n")

        console.print(Panel(content, title="[bold]ACTION PROPOSAL[/bold]", border_style="yellow"))

        try:
            response = input("Approve? (y/n): ").strip().lower()
            return response in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False

    def __repr__(self) -> str:
        s = self.summary
        return (
            f"CarefulSession(proposals={s['total']}, "
            f"approved={s['approved']}, denied={s['denied']})"
        )
