"""
Chapter 1: Shannon Entropy Calculator

Information theory foundations. Shannon entropy measures the
uncertainty (or information content) of a random variable.

    H(X) = -sum( p(x) * log2(p(x)) ) for all x in X

High entropy = more uncertainty = more information content.
Low entropy = more predictable = less information content.

This is the mathematical foundation for understanding why
intelligence requires the ability to compress and generalize,
not just memorize.
"""

from __future__ import annotations

import math
from collections import Counter


def shannon_entropy(data: str | list) -> float:
    """
    Calculate Shannon entropy of a sequence.

    Args:
        data: A string or list of symbols.

    Returns:
        Entropy in bits (base-2 logarithm).

    Example:
        >>> shannon_entropy("AAAA")
        0.0
        >>> shannon_entropy("AABB")
        1.0
        >>> round(shannon_entropy("ABCD"), 2)
        2.0
    """
    if not data:
        return 0.0

    counts = Counter(data)
    total = len(data)
    entropy = 0.0

    for count in counts.values():
        probability = count / total
        if probability > 0:
            entropy -= probability * math.log2(probability)

    return entropy


def relative_entropy(data: str | list) -> float:
    """
    Calculate relative entropy (normalized to [0, 1]).

    0.0 = perfectly ordered (one symbol repeated)
    1.0 = maximum disorder (all symbols equally likely)
    """
    if not data:
        return 0.0

    h = shannon_entropy(data)
    unique = len(set(data))
    max_entropy = math.log2(unique) if unique > 1 else 1.0
    return h / max_entropy


def information_content(probability: float) -> float:
    """
    Calculate the information content (surprisal) of a single event.

    I(x) = -log2(p(x))

    Rare events carry more information than common ones.
    """
    if probability <= 0 or probability > 1:
        raise ValueError(f"Probability must be in (0, 1], got {probability}")
    return -math.log2(probability)


def cross_entropy(p: list[float], q: list[float]) -> float:
    """
    Calculate cross-entropy between two distributions.

    H(p, q) = -sum( p(x) * log2(q(x)) )

    Measures how well distribution q predicts samples from p.
    Used in machine learning loss functions.
    """
    if len(p) != len(q):
        raise ValueError("Distributions must have the same length")

    result = 0.0
    for pi, qi in zip(p, q):
        if pi > 0 and qi > 0:
            result -= pi * math.log2(qi)
    return result


def kl_divergence(p: list[float], q: list[float]) -> float:
    """
    Calculate KL divergence (relative entropy) from q to p.

    D_KL(p || q) = sum( p(x) * log2(p(x) / q(x)) )

    Measures how much information is lost when q is used
    to approximate p. Always non-negative (Gibbs' inequality).
    """
    if len(p) != len(q):
        raise ValueError("Distributions must have the same length")

    result = 0.0
    for pi, qi in zip(p, q):
        if pi > 0 and qi > 0:
            result += pi * math.log2(pi / qi)
    return result


# --- Demonstrations ---


def demo_entropy_comparison() -> None:
    """Compare entropy of different types of text."""
    examples = [
        ("Repeated", "AAAAAAAAAA"),
        ("Binary", "ABABABABAB"),
        ("English word", "intelligence"),
        ("Random-looking", "x9k2m7q4p1"),
        ("DNA sequence", "ATCGATCGAT"),
        ("Python code", "def f(x): return x * 2"),
    ]

    print("Shannon Entropy Comparison")
    print("=" * 60)
    print(f"{'Label':<20} {'Text':<25} {'H (bits)':<10} {'Relative'}")
    print("-" * 60)

    for label, text in examples:
        h = shannon_entropy(text)
        r = relative_entropy(text)
        display = text if len(text) <= 22 else text[:19] + "..."
        print(f"{label:<20} {display:<25} {h:<10.4f} {r:.4f}")


def demo_information_content() -> None:
    """Show information content of events with different probabilities."""
    print("\nInformation Content (Surprisal)")
    print("=" * 40)
    print(f"{'Event':<20} {'P(x)':<10} {'I(x) bits'}")
    print("-" * 40)

    events = [
        ("Coin flip (heads)", 0.5),
        ("Die roll (6)", 1 / 6),
        ("Common word 'the'", 0.07),
        ("Rare word 'AGI'", 0.0001),
        ("Certain event", 0.999),
    ]

    for label, prob in events:
        info = information_content(prob)
        print(f"{label:<20} {prob:<10.4f} {info:.4f}")


def demo_cross_entropy() -> None:
    """Demonstrate cross-entropy between distributions."""
    print("\nCross-Entropy & KL Divergence")
    print("=" * 50)

    # True distribution vs model predictions
    p_true = [0.7, 0.2, 0.1]  # True: mostly class A
    q_good = [0.6, 0.3, 0.1]  # Good model
    q_bad = [0.33, 0.33, 0.34]  # Bad model (uniform)

    h_good = cross_entropy(p_true, q_good)
    h_bad = cross_entropy(p_true, q_bad)
    kl_good = kl_divergence(p_true, q_good)
    kl_bad = kl_divergence(p_true, q_bad)

    print(f"True distribution:    {p_true}")
    print(f"Good model:           {q_good}")
    print(f"Bad model (uniform):  {q_bad}")
    print(f"\nCross-entropy (good model): {h_good:.4f} bits")
    print(f"Cross-entropy (bad model):  {h_bad:.4f} bits")
    print(f"KL divergence (good model): {kl_good:.4f} bits")
    print(f"KL divergence (bad model):  {kl_bad:.4f} bits")
    print(f"\nThe good model loses less information ({kl_good:.4f} < {kl_bad:.4f})")


if __name__ == "__main__":
    demo_entropy_comparison()
    demo_information_content()
    demo_cross_entropy()
