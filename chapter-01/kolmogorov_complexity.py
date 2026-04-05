"""
Chapter 1: Kolmogorov Complexity Estimator

Kolmogorov complexity K(x) is the length of the shortest program
that produces string x. It is uncomputable in general, but we can
estimate it using compression ratios.

High K(x) = complex, hard to compress = random-looking
Low K(x)  = simple, easy to compress = patterned

The key insight: intelligence is about finding low-complexity
descriptions of high-complexity phenomena. Understanding is
compression.
"""

from __future__ import annotations

import zlib


def estimate_kolmogorov(data: str | bytes) -> float:
    """
    Estimate Kolmogorov complexity using zlib compression.

    Returns the compression ratio as a proxy for complexity.
    Lower values = more compressible = lower complexity.
    Higher values = less compressible = higher complexity.

    Args:
        data: String or bytes to analyze.

    Returns:
        Estimated normalized complexity in [0, 1].
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    if len(data) == 0:
        return 0.0

    compressed = zlib.compress(data, level=9)
    # Subtract zlib header/footer overhead (~11 bytes)
    compressed_size = max(len(compressed) - 11, 1)
    ratio = compressed_size / len(data)

    # Normalize to [0, 1]
    return min(ratio, 1.0)


def normalized_compression_distance(x: str, y: str) -> float:
    """
    Normalized Compression Distance (NCD) between two strings.

    NCD(x, y) = (C(xy) - min(C(x), C(y))) / max(C(x), C(y))

    Values close to 0 mean x and y are similar (share structure).
    Values close to 1 mean x and y are dissimilar.

    This is a universal similarity metric based on Kolmogorov complexity.
    """
    def compress_len(s: str) -> int:
        return len(zlib.compress(s.encode("utf-8"), level=9))

    cx = compress_len(x)
    cy = compress_len(y)
    cxy = compress_len(x + y)

    denominator = max(cx, cy)
    if denominator == 0:
        return 0.0

    return (cxy - min(cx, cy)) / denominator


def complexity_profile(text: str, window_size: int = 50) -> list[float]:
    """
    Generate a complexity profile: sliding window complexity analysis.

    Shows how complexity varies across different parts of the text.
    Useful for identifying regions of pattern vs. randomness.
    """
    if len(text) < window_size:
        return [estimate_kolmogorov(text)]

    profile = []
    for i in range(0, len(text) - window_size + 1, window_size // 2):
        window = text[i : i + window_size]
        profile.append(estimate_kolmogorov(window))

    return profile


# --- Demonstrations ---


def demo_complexity_comparison() -> None:
    """Compare complexity of different types of data."""
    examples = [
        ("Zeros (low K)", "0" * 1000),
        ("Pattern (low K)", "ABCD" * 250),
        ("English text", "The quick brown fox jumps over the lazy dog. " * 20),
        ("Python code", (
            "def fibonacci(n):\n    if n <= 1:\n"
            "        return n\n"
            "    return fibonacci(n-1) + fibonacci(n-2)\n"
        ) * 10),
        ("Pseudorandom", "".join(chr(((i * 7 + 13) % 94) + 33) for i in range(1000))),
    ]

    print("Kolmogorov Complexity Estimation")
    print("=" * 60)
    print(f"{'Label':<20} {'Size':<8} {'Compressed':<12} {'K estimate'}")
    print("-" * 60)

    for label, data in examples:
        k = estimate_kolmogorov(data)
        compressed_size = len(zlib.compress(data.encode("utf-8"), level=9))
        print(f"{label:<20} {len(data):<8} {compressed_size:<12} {k:.4f}")

    print("\nKey insight: intelligence finds low-K descriptions of high-K phenomena.")


def demo_ncd_similarity() -> None:
    """Demonstrate NCD as a universal similarity metric."""
    texts = {
        "python_1": "def add(a, b): return a + b",
        "python_2": "def multiply(a, b): return a * b",
        "english_1": "The cat sat on the mat",
        "english_2": "The dog lay on the rug",
        "random": "x9k2m7q4p1z8n3j6",
    }

    print("\nNormalized Compression Distance (NCD)")
    print("=" * 50)

    pairs = [
        ("python_1", "python_2"),
        ("english_1", "english_2"),
        ("python_1", "english_1"),
        ("python_1", "random"),
        ("english_1", "random"),
    ]

    for a, b in pairs:
        ncd = normalized_compression_distance(texts[a], texts[b])
        print(f"  NCD({a}, {b}) = {ncd:.4f}")

    print("\nLower NCD = more similar structure. Higher NCD = more different.")


def demo_complexity_profile() -> None:
    """Show complexity profile across a mixed text."""
    # Create text with varying complexity regions
    text = (
        "AAAA" * 50  # Low complexity region
        + "The quick brown fox jumps over the lazy dog. " * 10  # Medium
        + "".join(chr(((i * 7 + 13) % 26) + 65) for i in range(200))  # Higher
    )

    profile = complexity_profile(text, window_size=40)
    print("\nComplexity Profile (sliding window)")
    print("=" * 50)

    max_bar = 40
    for i, k in enumerate(profile):
        bar = "█" * int(k * max_bar)
        print(f"  Window {i:3d}: {bar} {k:.3f}")


if __name__ == "__main__":
    demo_complexity_comparison()
    demo_ncd_similarity()
    demo_complexity_profile()
