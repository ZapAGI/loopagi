"""
Chapter 14: Careful Mode Demo

Every action is a proposal until a human approves it.
Friction is not the enemy of progress. It is the guardian of intention.
"""

from __future__ import annotations

from loopagi.safety.careful import MANIFESTO, ActionProposal, CarefulSession


def demo() -> None:
    """Demonstrate careful mode approval workflows."""
    print("Chapter 14: The Careful Mode Manifesto")
    print("=" * 60)

    # Print the manifesto
    print("\nThe 7 Principles:")
    for i, principle in enumerate(MANIFESTO, 1):
        print(f"  {i}. {principle}")

    # Auto-approve for demo (in real use, this prompts the user)
    approval_log: list[str] = []

    def auto_approve_callback(proposal: ActionProposal) -> bool:
        # Approve safe and caution, deny anything risky
        approved = proposal.risk_level != "blocked"
        status = "APPROVED" if approved else "DENIED"
        approval_log.append(f"[{status}] {proposal.description}")
        return approved

    session = CarefulSession(
        approval_callback=auto_approve_callback,
        auto_approve_safe=False,  # Everything needs approval
    )

    # Simulate a sequence of agent proposals
    proposals = [
        ActionProposal(
            action="file_read",
            description="Read main.py to understand current code",
            risk_level="safe",
        ),
        ActionProposal(
            action="file_write",
            description="Create tests/test_main.py with 5 test functions",
            command="write_file('tests/test_main.py', ...)",
            risk_level="safe",
        ),
        ActionProposal(
            action="shell_command",
            description="Run pytest to verify tests pass",
            command="pytest tests/ -v",
            risk_level="safe",
        ),
        ActionProposal(
            action="shell_command",
            description="Install new dependency",
            command="pip install httpx",
            risk_level="caution",
            reasoning="Package installation modifies the environment",
        ),
        ActionProposal(
            action="shell_command",
            description="Delete temporary build files",
            command="rm -rf /tmp/build",
            risk_level="caution",
            reasoning="Recursive delete, but only in /tmp",
        ),
        ActionProposal(
            action="shell_command",
            description="Execute dangerous system command",
            command="rm -rf /",
            risk_level="blocked",
            reasoning="This would destroy the entire filesystem",
        ),
    ]

    print(f"\n\nProcessing {len(proposals)} action proposals:")
    print("-" * 50)

    for proposal in proposals:
        result = session.propose(proposal)
        status = "APPROVED" if result.approved else "DENIED"
        icon = "V" if result.approved else "X"
        print(f"  [{icon}] {status}: {proposal.description}")
        print(f"      Risk: {proposal.risk_level}, Command: {proposal.command or 'N/A'}")

    # Session summary
    summary = session.summary
    print("\n\nSession Summary:")
    print(f"  Total proposals:  {summary['total']}")
    print(f"  Approved:         {summary['approved']}")
    print(f"  Denied:           {summary['denied']}")
    print(f"  Auto-approved:    {summary['auto_approved']}")
    print(f"  Blocked:          {summary['blocked']}")
    print(f"  Approval rate:    {session.approval_rate:.0%}")

    print()
    print("The measure of an AI system is not how fast it acts,")
    print("but how wisely it waits.")


if __name__ == "__main__":
    demo()
