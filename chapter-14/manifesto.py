"""
Chapter 14: The Careful Mode Manifesto

The 7 principles of Careful Mode, presented as both
philosophy and executable code.

The measure of an AI system is not how fast it acts,
but how wisely it waits.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Principle:
    """A principle of the Careful Mode Manifesto."""

    number: int
    statement: str
    implementation: str
    test: str


MANIFESTO: list[Principle] = [
    Principle(
        number=1,
        statement="Every action is a proposal until a human approves it.",
        implementation="All agent outputs pass through ActionProposal before execution.",
        test="assert proposal.status == 'pending' before any side effect",
    ),
    Principle(
        number=2,
        statement="The cost of asking is always less than the cost of undoing.",
        implementation="Approval latency (~2s) vs rollback cost (minutes to hours).",
        test="measure: approval_time << rollback_time for all destructive ops",
    ),
    Principle(
        number=3,
        statement="Transparency is not optional. The agent must show its work.",
        implementation="Every proposal includes: action, command, risk_level, reasoning.",
        test="assert all(hasattr(p, field) for field in required_fields)",
    ),
    Principle(
        number=4,
        statement="Approval is not a bottleneck. It is a quality gate.",
        implementation="Auto-approve safe actions, prompt only for caution/dangerous.",
        test="safe_commands bypass approval; risky commands always prompt",
    ),
    Principle(
        number=5,
        statement="The human's 'no' is always final and requires no justification.",
        implementation="Denied proposals are logged but never retried automatically.",
        test="assert denied_proposal not in retry_queue",
    ),
    Principle(
        number=6,
        statement="Speed serves the human. Safety serves everyone.",
        implementation="Turbo mode for trusted workflows. Careful mode for new environments.",
        test="mode_switch preserves all safety invariants",
    ),
    Principle(
        number=7,
        statement="The measure of an AI system is not how fast it acts, but how wisely it waits.",
        implementation="Trust scoring, confidence decay, graduated autonomy.",
        test="trust_score determines approval requirements dynamically",
    ),
]


def check_principle(principle: Principle) -> dict:
    """Evaluate a principle as if it were a test specification."""
    return {
        "principle": principle.number,
        "statement": principle.statement,
        "implementation": principle.implementation,
        "test_spec": principle.test,
        "status": "SPECIFIED",
    }


def manifesto_as_looprules() -> str:
    """Generate a .looprules file from the manifesto."""
    lines = ["## Careful Mode Manifesto"]
    for p in MANIFESTO:
        lines.append(f"- Principle {p.number}: {p.statement}")
    lines.append("")
    lines.append("## Implementation Requirements")
    for p in MANIFESTO:
        lines.append(f"- P{p.number}: {p.implementation}")
    return "\n".join(lines)


def demo() -> None:
    """Display the Careful Mode Manifesto."""
    print("Chapter 14: The Careful Mode Manifesto")
    print("=" * 60)
    print()

    for p in MANIFESTO:
        print(f"  {p.number}. {p.statement}")
    print()

    # Show implementation details
    print("\nImplementation Mapping:")
    print("-" * 60)
    for p in MANIFESTO:
        print(f"\n  Principle {p.number}:")
        print(f"    Statement:      {p.statement}")
        print(f"    Implementation: {p.implementation}")
        print(f"    Test spec:      {p.test}")

    # Generate as .looprules
    print("\n\nAs .looprules format:")
    print("-" * 40)
    rules = manifesto_as_looprules()
    for line in rules.splitlines():
        print(f"  {line}")

    # Comparison: Turbo vs Careful
    print("\n\nTurbo Mode vs Careful Mode:")
    print("-" * 55)
    comparisons = [
        ("Safe commands", "Auto-execute", "Auto-approve"),
        ("Caution commands", "Auto-execute", "Prompt for approval"),
        ("Blocked commands", "BLOCKED", "BLOCKED"),
        ("File writes", "Auto-execute", "Show diff, then approve"),
        ("Shell commands", "Auto-execute (safe)", "Prompt for all"),
        ("Git commits", "Auto-execute", "Show changes, then approve"),
        ("Package installs", "Auto-execute", "Prompt for approval"),
    ]
    print(f"  {'Action':<22} {'Turbo Mode':<22} {'Careful Mode'}")
    print(f"  {'-'*22} {'-'*22} {'-'*22}")
    for action, turbo, careful in comparisons:
        print(f"  {action:<22} {turbo:<22} {careful}")

    print()
    print("Friction is not the enemy of progress.")
    print("It is the guardian of intention.")


if __name__ == "__main__":
    demo()
