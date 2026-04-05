"""Tests for loopagi.careful module."""

from __future__ import annotations

from loopagi.safety.careful import (
    MANIFESTO,
    ActionProposal,
    CarefulSession,
    ProposalStatus,
)


class TestManifesto:
    """Tests for the 7 principles."""

    def test_seven_principles(self) -> None:
        assert len(MANIFESTO) == 7

    def test_all_strings(self) -> None:
        for p in MANIFESTO:
            assert isinstance(p, str)
            assert len(p) > 10


class TestProposalStatus:
    """Tests for ProposalStatus enum."""

    def test_values(self) -> None:
        assert ProposalStatus.PENDING.value == "pending"
        assert ProposalStatus.APPROVED.value == "approved"
        assert ProposalStatus.DENIED.value == "denied"
        assert ProposalStatus.AUTO_APPROVED.value == "auto_approved"
        assert ProposalStatus.BLOCKED.value == "blocked"


class TestActionProposal:
    """Tests for ActionProposal dataclass."""

    def test_creation(self) -> None:
        p = ActionProposal(action="shell_command", description="run pytest")
        assert p.action == "shell_command"
        assert p.risk_level == "safe"
        assert p.status == ProposalStatus.PENDING

    def test_with_command(self) -> None:
        p = ActionProposal(
            action="shell_command",
            description="install package",
            command="pip install httpx",
            risk_level="caution",
        )
        assert p.command == "pip install httpx"
        assert p.risk_level == "caution"


class TestCarefulSession:
    """Tests for CarefulSession."""

    def test_approve_safe(self) -> None:
        session = CarefulSession(approval_callback=lambda p: True)
        proposal = ActionProposal(action="file_read", description="read file", risk_level="safe")
        result = session.propose(proposal)
        assert result.approved
        assert proposal.status == ProposalStatus.APPROVED

    def test_deny(self) -> None:
        session = CarefulSession(approval_callback=lambda p: False)
        proposal = ActionProposal(action="shell", description="run cmd", risk_level="safe")
        result = session.propose(proposal)
        assert not result.approved
        assert proposal.status == ProposalStatus.DENIED

    def test_blocked_always_denied(self) -> None:
        session = CarefulSession(approval_callback=lambda p: True)  # Would approve
        proposal = ActionProposal(action="shell", description="rm rf", risk_level="blocked")
        result = session.propose(proposal)
        assert not result.approved
        assert proposal.status == ProposalStatus.BLOCKED

    def test_auto_approve_safe(self) -> None:
        session = CarefulSession(
            approval_callback=lambda p: False,  # Would deny
            auto_approve_safe=True,
        )
        proposal = ActionProposal(action="file_read", description="read", risk_level="safe")
        result = session.propose(proposal)
        assert result.approved
        assert proposal.status == ProposalStatus.AUTO_APPROVED

    def test_auto_approve_does_not_apply_to_caution(self) -> None:
        session = CarefulSession(
            approval_callback=lambda p: False,
            auto_approve_safe=True,
        )
        proposal = ActionProposal(action="shell", description="sudo", risk_level="caution")
        result = session.propose(proposal)
        assert not result.approved  # Callback denied it
        assert proposal.status == ProposalStatus.DENIED

    def test_approval_rate(self) -> None:
        call_count = [0]
        def alternating(p):
            call_count[0] += 1
            return call_count[0] % 2 == 1  # Approve odd, deny even

        session = CarefulSession(approval_callback=alternating)
        for _ in range(4):
            session.propose(ActionProposal(action="test", description="test", risk_level="safe"))

        assert session.approval_rate == 0.5

    def test_summary(self) -> None:
        session = CarefulSession(approval_callback=lambda p: True)
        session.propose(ActionProposal(action="a", description="a", risk_level="safe"))
        session.propose(ActionProposal(action="b", description="b", risk_level="blocked"))

        s = session.summary
        assert s["total"] == 2
        assert s["approved"] == 1
        assert s["blocked"] == 1

    def test_repr(self) -> None:
        session = CarefulSession(approval_callback=lambda p: True)
        r = repr(session)
        assert "CarefulSession" in r
