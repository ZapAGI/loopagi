"""
Chapter 1: Document Similarity Engine

A real-world tool using Normalized Compression Distance (NCD)
for document deduplication, plagiarism detection, and content
clustering. No ML models required. Works on any text.

NCD is a universal similarity metric based on Kolmogorov complexity:
    NCD(x, y) = (C(xy) - min(C(x), C(y))) / max(C(x), C(y))

Real-world applications:
  - Deduplicate a corpus before training
  - Detect near-duplicate documentation
  - Cluster related code files
  - Find plagiarism without embeddings

Usage:
    python chapter-01/document_similarity.py [directory]
"""

from __future__ import annotations

import sys
import zlib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SimilarityMatch:
    """A pair of documents with their similarity score."""

    file_a: str
    file_b: str
    ncd: float
    similarity_pct: float

    @property
    def is_near_duplicate(self) -> bool:
        return self.similarity_pct >= 80.0

    @property
    def is_related(self) -> bool:
        return self.similarity_pct >= 50.0


def compress_len(data: bytes) -> int:
    """Compressed length using zlib level 9."""
    return len(zlib.compress(data, level=9))


def ncd(a: bytes, b: bytes) -> float:
    """
    Normalized Compression Distance between two byte strings.

    Returns a value in [0, 1]:
      0.0 = identical structure
      1.0 = completely different
    """
    if not a and not b:
        return 0.0
    if not a or not b:
        return 1.0

    ca = compress_len(a)
    cb = compress_len(b)
    cab = compress_len(a + b)

    denom = max(ca, cb)
    if denom == 0:
        return 0.0

    return (cab - min(ca, cb)) / denom


def ncd_text(a: str, b: str) -> float:
    """NCD for text strings."""
    return ncd(a.encode("utf-8"), b.encode("utf-8"))


def find_similar_files(
    directory: Path,
    extensions: tuple[str, ...] = (".py", ".md", ".txt", ".rs", ".go", ".ts", ".java"),
    threshold: float = 0.5,
    max_file_size: int = 100_000,
) -> list[SimilarityMatch]:
    """
    Scan a directory and find similar file pairs using NCD.

    Args:
        directory: Root directory to scan
        extensions: File extensions to include
        threshold: NCD threshold (lower = more similar). Files with
                   NCD below this are reported.
        max_file_size: Skip files larger than this (bytes)

    Returns:
        List of SimilarityMatch objects, sorted by similarity.
    """
    files: dict[str, bytes] = {}

    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in extensions:
            continue
        if "__pycache__" in str(path) or ".venv" in str(path):
            continue
        if ".git" in path.parts:
            continue
        if path.stat().st_size > max_file_size:
            continue
        if path.stat().st_size == 0:
            continue

        try:
            content = path.read_bytes()
            rel = str(path.relative_to(directory))
            files[rel] = content
        except (OSError, UnicodeDecodeError):
            continue

    # Compare all pairs
    matches = []
    names = list(files.keys())

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            distance = ncd(files[names[i]], files[names[j]])
            if distance < threshold:
                similarity = (1.0 - distance) * 100
                matches.append(SimilarityMatch(
                    file_a=names[i],
                    file_b=names[j],
                    ncd=distance,
                    similarity_pct=similarity,
                ))

    matches.sort(key=lambda m: m.ncd)
    return matches


def find_duplicates_in_texts(
    texts: dict[str, str],
    threshold: float = 0.4,
) -> list[SimilarityMatch]:
    """
    Find near-duplicate texts from a dictionary of label -> content.

    Useful for deduplicating a training corpus, finding
    repeated documentation, or detecting plagiarism.
    """
    matches = []
    labels = list(texts.keys())

    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            distance = ncd_text(texts[labels[i]], texts[labels[j]])
            if distance < threshold:
                similarity = (1.0 - distance) * 100
                matches.append(SimilarityMatch(
                    file_a=labels[i],
                    file_b=labels[j],
                    ncd=distance,
                    similarity_pct=similarity,
                ))

    matches.sort(key=lambda m: m.ncd)
    return matches


def cluster_documents(
    texts: dict[str, str],
    threshold: float = 0.5,
) -> list[list[str]]:
    """
    Cluster documents by similarity using single-linkage clustering.

    Returns groups of related document labels.
    """
    labels = list(texts.keys())
    parent = {label: label for label in labels}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            distance = ncd_text(texts[labels[i]], texts[labels[j]])
            if distance < threshold:
                union(labels[i], labels[j])

    clusters: dict[str, list[str]] = {}
    for label in labels:
        root = find(label)
        clusters.setdefault(root, []).append(label)

    return [group for group in clusters.values() if len(group) > 1]


# --- Demonstrations ---


def demo_text_dedup() -> None:
    """Demonstrate real-world text deduplication."""
    print("Real-World Text Deduplication")
    print("=" * 60)
    print()

    corpus = {
        "doc_1": (
            "Machine learning is a subset of artificial intelligence"
            " that enables systems to learn from data."
        ),
        "doc_2": (
            "ML is a branch of AI that allows systems to learn"
            " from data and improve over time."
        ),
        "doc_3": (
            "The Fibonacci sequence is defined as F(n) = F(n-1)"
            " + F(n-2) with base cases F(0)=0, F(1)=1."
        ),
        "doc_4": (
            "Deep learning uses neural networks with multiple"
            " layers to extract features from data."
        ),
        "doc_5": (
            "Machine learning, a subset of AI, enables computer"
            " systems to learn from data automatically."
        ),
        "doc_6": (
            "The weather in March is unpredictable with"
            " temperatures ranging from 30 to 70 degrees."
        ),
        "doc_7": (
            "Neural networks with many layers (deep learning)"
            " extract hierarchical features from data."
        ),
    }

    print("Corpus:")
    for label, text in corpus.items():
        print(f"  {label}: {text[:70]}...")

    matches = find_duplicates_in_texts(corpus, threshold=0.6)

    print(f"\nFound {len(matches)} similar pairs (threshold: NCD < 0.6):")
    print(f"  {'Pair':<22} {'NCD':<8} {'Similarity':<12} {'Status'}")
    print("  " + "-" * 55)

    for m in matches:
        status = "NEAR-DUP" if m.is_near_duplicate else "related" if m.is_related else ""
        print(f"  {m.file_a} <-> {m.file_b:<8} {m.ncd:<8.3f} {m.similarity_pct:<12.1f}% {status}")


def demo_code_similarity() -> None:
    """Demonstrate code similarity detection."""
    print("\n\nCode Similarity Detection")
    print("=" * 60)
    print()

    code_samples = {
        "sort_v1": "def sort(arr):\n    return sorted(arr)\n",
        "sort_v2": "def sort_list(items):\n    return sorted(items)\n",
        "sort_v3": (
            "def bubble_sort(arr):\n    n = len(arr)\n"
            "    for i in range(n):\n"
            "        for j in range(0, n-i-1):\n"
            "            if arr[j] > arr[j+1]:\n"
            "                arr[j], arr[j+1] = arr[j+1], arr[j]\n"
            "    return arr\n"
        ),
        "fib_v1": "def fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)\n",
        "fib_v2": (
            "def fibonacci(n):\n    if n <= 1: return n\n"
            "    a, b = 0, 1\n    for _ in range(2, n+1):\n"
            "        a, b = b, a + b\n    return b\n"
        ),
        "hello": "def greet(name):\n    print(f'Hello, {name}!')\n",
    }

    print("Code samples:")
    for label, code in code_samples.items():
        print(f"  {label}: {code.splitlines()[0]}")

    matches = find_duplicates_in_texts(code_samples, threshold=0.65)

    print("\nSimilar code pairs:")
    print(f"  {'Pair':<26} {'NCD':<8} {'Similarity'}")
    print("  " + "-" * 45)

    for m in matches:
        print(f"  {m.file_a} <-> {m.file_b:<10} {m.ncd:<8.3f} {m.similarity_pct:.1f}%")


def demo_clustering() -> None:
    """Demonstrate document clustering."""
    print("\n\nDocument Clustering")
    print("=" * 60)
    print()

    docs = {
        "python_intro": (
            "Python is a high-level programming language known"
            " for its simplicity and readability."
        ),
        "python_guide": (
            "Python is an easy-to-learn programming language"
            " with clean, readable syntax."
        ),
        "rust_intro": (
            "Rust is a systems programming language focused"
            " on safety, speed, and concurrency."
        ),
        "rust_guide": (
            "Rust provides memory safety without garbage"
            " collection through its ownership system."
        ),
        "cooking_1": "To make pasta, boil water, add salt, cook for 8-10 minutes until al dente.",
        "cooking_2": "Boil salted water, add dried pasta, cook for about 10 minutes until tender.",
    }

    clusters = cluster_documents(docs, threshold=0.55)

    print("Input documents:")
    for label in docs:
        print(f"  {label}")

    print(f"\nClusters found: {len(clusters)}")
    for i, group in enumerate(clusters, 1):
        print(f"  Cluster {i}: {group}")

    print("\nDocuments clustered by content similarity without any ML model.")


def demo_directory_scan() -> None:
    """Scan the repository itself for similar files."""
    print("\n\nRepository Self-Scan")
    print("=" * 60)

    repo_root = Path(__file__).parent.parent
    print(f"Scanning: {repo_root}")

    matches = find_similar_files(repo_root, threshold=0.35)

    if matches:
        print("\nMost similar file pairs (top 10):")
        print(f"  {'File A':<35} {'File B':<35} {'Similarity'}")
        print("  " + "-" * 80)

        for m in matches[:10]:
            print(f"  {m.file_a:<35} {m.file_b:<35} {m.similarity_pct:.1f}%")
    else:
        print("\n  No highly similar file pairs found (threshold: NCD < 0.35)")
        print("  This is good: the codebase has low redundancy.")


def demo() -> None:
    """Run all document similarity demonstrations."""
    print("Chapter 1: Document Similarity Engine")
    print("NCD-Based Deduplication, Plagiarism Detection, and Clustering")
    print("No ML models. No embeddings. Pure information theory.")
    print()

    demo_text_dedup()
    demo_code_similarity()
    demo_clustering()
    demo_directory_scan()

    print("\n" + "=" * 60)
    print("NCD is a universal similarity metric. It works on any data")
    print("type (text, code, binary) without training or embeddings.")
    print("Understanding is compression. Similarity is shared structure.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if target.is_dir():
            print(f"Scanning directory: {target}")
            matches = find_similar_files(target)
            for m in matches:
                status = "NEAR-DUP" if m.is_near_duplicate else ""
                print(f"  {m.file_a} <-> {m.file_b}  {m.similarity_pct:.1f}% {status}")
        else:
            print(f"Not a directory: {target}")
    else:
        demo()
