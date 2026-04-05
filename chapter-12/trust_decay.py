"""
Chapter 12: Trust Decay Visualization

Trust is not a boolean. It is a function that decays without reinforcement.

    trust(t) = trust_0 * e^(-lambda * t)

This script visualizes the trust decay curve and shows how
reinforcement and penalties affect the score over time.
"""

from __future__ import annotations

import math


def trust_at_time(initial: float, decay_rate: float, t: float) -> float:
    """Calculate trust score at time t with exponential decay."""
    return initial * math.exp(-decay_rate * t)


def simulate_trust_timeline(
    initial: float = 0.8,
    decay_rate: float = 0.002,
    duration_seconds: int = 3600,
    events: list[tuple[int, str, float]] | None = None,
) -> list[tuple[int, float, str]]:
    """
    Simulate trust score over time with events.

    Args:
        initial: Starting trust score
        decay_rate: Exponential decay rate (lambda)
        duration_seconds: Total simulation duration
        events: List of (time, type, amount) tuples
                type is "reinforce" or "penalize"

    Returns:
        List of (time, score, event_label) tuples
    """
    events = events or []
    event_map = {t: (etype, amount) for t, etype, amount in events}

    timeline = []
    current_trust = initial
    last_reinforcement = 0

    for t in range(0, duration_seconds + 1, 60):  # Sample every minute
        # Apply decay since last reinforcement
        elapsed = t - last_reinforcement
        decayed = current_trust * math.exp(-decay_rate * elapsed)

        label = ""
        if t in event_map:
            etype, amount = event_map[t]
            if etype == "reinforce":
                decayed = min(1.0, decayed + amount)
                label = f"+{amount:.2f}"
                current_trust = decayed
                last_reinforcement = t
            elif etype == "penalize":
                decayed = max(0.1, decayed - amount)
                label = f"-{amount:.2f}"
                current_trust = decayed
                last_reinforcement = t

        timeline.append((t, decayed, label))

    return timeline


def trust_level(score: float) -> str:
    """Map trust score to human-readable level."""
    if score >= 0.8:
        return "HIGH"
    elif score >= 0.5:
        return "MEDIUM"
    elif score >= 0.3:
        return "LOW"
    return "MINIMAL"


def render_bar(score: float, width: int = 40) -> str:
    """Render a visual bar for a trust score."""
    filled = int(score * width)
    return "=" * filled + "." * (width - filled)


def demo() -> None:
    """Visualize trust decay with events."""
    print("Chapter 12: Trust Decay Visualization")
    print("=" * 60)
    print()
    print("  trust(t) = trust_0 * e^(-lambda * t)")
    print("  lambda = 0.002 (decays ~50% per 6 minutes without reinforcement)")
    print()

    # Scenario: active session with events
    events = [
        (300, "reinforce", 0.10),   # 5 min: approved a file write
        (600, "reinforce", 0.10),   # 10 min: approved a shell command
        (900, "penalize", 0.15),    # 15 min: denied a dangerous command
        (1200, "reinforce", 0.10),  # 20 min: successful test run
        (1800, "reinforce", 0.10),  # 30 min: code review passed
        # 30-60 min: no activity (trust decays)
    ]

    timeline = simulate_trust_timeline(
        initial=0.5,
        decay_rate=0.002,
        duration_seconds=3600,
        events=events,
    )

    print("Trust Timeline (1 hour session):")
    print("-" * 65)
    print(f"  {'Time':<8} {'Score':<8} {'Level':<8} {'Bar':<42} {'Event'}")
    print("-" * 65)

    # Show every 5 minutes
    for t, score, label in timeline:
        if t % 300 == 0:  # Every 5 minutes
            minutes = t // 60
            bar = render_bar(score)
            level = trust_level(score)
            event_str = f"  [{label}]" if label else ""
            print(f"  {minutes:>3}m    {score:<8.3f} {level:<8} |{bar}|{event_str}")

    # Pure decay curve (no events)
    print("\n\nPure Decay Curve (no reinforcement):")
    print("-" * 50)
    initial = 0.8
    for minutes in [0, 1, 2, 5, 10, 15, 20, 30, 45, 60]:
        t = minutes * 60
        score = trust_at_time(initial, 0.002, t)
        bar = render_bar(score, 30)
        print(f"  {minutes:>3}m  {score:.3f}  |{bar}|  {trust_level(score)}")

    print()
    print("Without reinforcement, trust decays to near-zero in ~30 minutes.")
    print("Active sessions maintain trust through successful interactions.")
    print("Trust is earned continuously, not granted once.")


if __name__ == "__main__":
    demo()
