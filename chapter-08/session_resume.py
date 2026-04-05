"""
Chapter 8: Session Persistence and Identity Continuity

Is the agent that resumes a session the same agent that started it?
Is the human who wakes up each morning the same person who fell asleep?

This demo shows how session state can be saved and restored,
creating the illusion of continuity. Memory is reconstruction,
not replay. Both for agents and for us.
"""

from __future__ import annotations

import json
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class AgentState:
    """Serializable state of an agent."""

    name: str
    role: str
    history: list[dict] = field(default_factory=list)
    memories: list[str] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    session_count: int = 0


@dataclass
class SessionSnapshot:
    """A complete session snapshot that can be saved and restored."""

    session_id: str
    agents: list[AgentState]
    context_files: list[str]
    action_history: list[str]
    trust_score: float
    mode: str
    created_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


def save_session(snapshot: SessionSnapshot, path: Path) -> None:
    """Save a session snapshot to disk."""
    data = {
        "session_id": snapshot.session_id,
        "agents": [asdict(a) for a in snapshot.agents],
        "context_files": snapshot.context_files,
        "action_history": snapshot.action_history,
        "trust_score": snapshot.trust_score,
        "mode": snapshot.mode,
        "created_at": snapshot.created_at,
        "metadata": snapshot.metadata,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_session(path: Path) -> SessionSnapshot:
    """Load a session snapshot from disk."""
    data = json.loads(path.read_text(encoding="utf-8"))
    agents = [AgentState(**a) for a in data["agents"]]
    return SessionSnapshot(
        session_id=data["session_id"],
        agents=agents,
        context_files=data["context_files"],
        action_history=data["action_history"],
        trust_score=data["trust_score"],
        mode=data["mode"],
        created_at=data["created_at"],
        metadata=data.get("metadata", {}),
    )


def compute_identity_score(original: AgentState, restored: AgentState) -> float:
    """
    How much of the original agent's identity survived the save/restore?

    Checks: name, role, history length, memories, preferences.
    Returns a score from 0.0 (completely different) to 1.0 (identical).
    """
    score = 0.0
    checks = 0

    # Name match
    checks += 1
    if original.name == restored.name:
        score += 1.0

    # Role match
    checks += 1
    if original.role == restored.role:
        score += 1.0

    # History preserved
    checks += 1
    if len(original.history) == len(restored.history):
        score += 1.0
    elif len(restored.history) > 0:
        score += len(restored.history) / max(len(original.history), 1)

    # Memories preserved
    checks += 1
    if original.memories == restored.memories:
        score += 1.0
    elif len(restored.memories) > 0:
        overlap = len(set(original.memories) & set(restored.memories))
        score += overlap / max(len(original.memories), 1)

    # Preferences preserved
    checks += 1
    if original.preferences == restored.preferences:
        score += 1.0

    return score / checks if checks > 0 else 0.0


def demo() -> None:
    """Demonstrate session save, restore, and identity continuity."""
    print("Chapter 8: Session Persistence and Identity Continuity")
    print("=" * 60)

    # Create a session with agent state
    agents = [
        AgentState(
            name="coder",
            role="Python coding specialist",
            history=[
                {"role": "user", "content": "Write a fibonacci function"},
                {"role": "agent", "content": "def fib(n): ..."},
                {"role": "user", "content": "Add memoization"},
                {"role": "agent", "content": "from functools import lru_cache ..."},
            ],
            memories=[
                "User prefers functional programming style",
                "Project uses pytest for testing",
                "Line length limit: 100 characters",
            ],
            preferences={"style": "functional", "testing": "pytest", "verbose": False},
            session_count=3,
        ),
        AgentState(
            name="researcher",
            role="Research specialist",
            history=[
                {"role": "user", "content": "What is the Kardashev scale?"},
                {"role": "agent", "content": "The Kardashev scale measures..."},
            ],
            memories=["User is interested in AGI and civilization theory"],
            preferences={"detail_level": "thorough"},
            session_count=2,
        ),
    ]

    snapshot = SessionSnapshot(
        session_id="20260315_2200_a1b2c3d4",
        agents=agents,
        context_files=["main.py", "tests/test_main.py", "README.md"],
        action_history=[
            "Created project scaffold",
            "Wrote fibonacci function",
            "Added memoization",
            "Generated tests",
            "All tests passing",
        ],
        trust_score=0.78,
        mode="turbo",
        metadata={"project": "fibonacci-lib", "model": "llama3.2"},
    )

    print(f"\nOriginal Session: {snapshot.session_id}")
    print(f"  Agents: {[a.name for a in snapshot.agents]}")
    print(f"  Trust: {snapshot.trust_score}")
    print(f"  Mode: {snapshot.mode}")
    print(f"  Actions: {len(snapshot.action_history)}")
    print(f"  Context files: {snapshot.context_files}")

    # Save to disk
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "session.json"
        save_session(snapshot, save_path)

        file_size = save_path.stat().st_size
        print(f"\n  Saved to: {save_path.name} ({file_size} bytes)")

        # Restore from disk
        restored = load_session(save_path)

        print(f"\nRestored Session: {restored.session_id}")
        print(f"  Agents: {[a.name for a in restored.agents]}")
        print(f"  Trust: {restored.trust_score}")
        print(f"  Mode: {restored.mode}")
        print(f"  Actions: {len(restored.action_history)}")

    # Identity analysis
    print("\n\nIdentity Continuity Analysis:")
    print("-" * 50)

    for orig, rest in zip(agents, restored.agents):
        score = compute_identity_score(orig, rest)
        print(f"\n  Agent: {orig.name}")
        print(f"    History: {len(orig.history)} messages -> {len(rest.history)} messages")
        print(f"    Memories: {len(orig.memories)} -> {len(rest.memories)}")
        print(f"    Preferences: {orig.preferences == rest.preferences}")
        print(f"    Identity score: {score:.2f} (1.0 = perfect continuity)")

    # The Ship of Theseus
    print("\n\nThe Ship of Theseus Question:")
    print("-" * 50)
    print("  If we save an agent's state, terminate it, and restore it")
    print("  on a different machine with a different model version:")
    print()
    print("  - Same name? Yes (serialized)")
    print("  - Same role? Yes (serialized)")
    print("  - Same memories? Yes (serialized)")
    print("  - Same conversation? Yes (serialized)")
    print("  - Same weights? Maybe not (different model version)")
    print("  - Same responses? Probably not (different weights + temperature)")
    print()
    print("  Is it the same agent? The same question applies to humans.")
    print("  Memory is reconstruction, not replay.")
    print("  Continuity is a series of reconstructions.")
    print("  And in this, we are more like our agents than we realize.")


if __name__ == "__main__":
    demo()
