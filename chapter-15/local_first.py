"""
Chapter 15: Local-First Architecture Patterns

Your code should never leave your machine. No API keys required.
No data leaves the device. This provides privacy, reduces latency,
and ensures the system works offline.

The best way to predict the future is to build it. Locally.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass


@dataclass
class LocalService:
    """A service that runs entirely on the local machine."""

    name: str
    description: str
    binary: str
    check_command: str
    default_port: int | None = None


LOCAL_STACK: list[LocalService] = [
    LocalService(
        name="Ollama",
        description="Local LLM inference (llama3.2, deepseek-r1, qwen2.5-coder)",
        binary="ollama",
        check_command="ollama list",
        default_port=11434,
    ),
    LocalService(
        name="Qdrant",
        description="Vector database for semantic memory and RAG (local mode, no server)",
        binary="python",  # qdrant_client local mode
        check_command="python -c 'import qdrant_client; print(\"OK\")'",
    ),
    LocalService(
        name="fastembed",
        description="CPU-based text embeddings (BAAI/bge-small-en-v1.5, 384-dim)",
        binary="python",
        check_command="python -c 'import fastembed; print(\"OK\")'",
    ),
    LocalService(
        name="Git",
        description="Version control for session-as-git provenance",
        binary="git",
        check_command="git --version",
    ),
    LocalService(
        name="Python",
        description="Runtime for all agent logic and tools",
        binary="python3",
        check_command="python3 --version",
    ),
]


def check_local_stack() -> dict[str, bool]:
    """Check which components of the local stack are available."""
    results = {}
    for service in LOCAL_STACK:
        available = shutil.which(service.binary) is not None
        results[service.name] = available
    return results


def demo() -> None:
    """Demonstrate local-first architecture principles."""
    print("Chapter 15: Local-First Architecture")
    print("=" * 60)

    print("\nPrinciples:")
    principles = [
        "All computation runs on the user's machine",
        "No API keys required for core functionality",
        "No data leaves the device (privacy by default)",
        "Works offline after initial model download",
        "User owns all data, models, and outputs",
        "No vendor lock-in: swap any component",
    ]
    for i, p in enumerate(principles, 1):
        print(f"  {i}. {p}")

    print("\n\nLocal Stack Components:")
    print("-" * 60)

    status = check_local_stack()
    for service in LOCAL_STACK:
        available = status.get(service.name, False)
        icon = "OK" if available else "MISSING"
        port = f" (:{service.default_port})" if service.default_port else ""
        print(f"  [{icon:>7}] {service.name}{port}")
        print(f"           {service.description}")

    print("\n\nCloud vs Local Comparison:")
    print("-" * 60)
    comparisons = [
        ("Latency", "100-500ms (network)", "10-50ms (local GPU)"),
        ("Privacy", "Data sent to cloud", "Data stays on machine"),
        ("Cost", "$0.01-0.10 per request", "Free after model download"),
        ("Availability", "Requires internet", "Works offline"),
        ("Control", "Vendor decides models", "You choose models"),
        ("Data ownership", "Vendor stores data", "You own everything"),
    ]
    print(f"  {'Dimension':<15} {'Cloud API':<25} {'Local-First'}")
    print(f"  {'-'*15} {'-'*25} {'-'*25}")
    for dim, cloud, local in comparisons:
        print(f"  {dim:<15} {cloud:<25} {local}")

    all_ok = all(status.values())
    msg = "All components available!" if all_ok else (
        "Some components missing. Install them to get started."
    )
    print(f"\n{msg}")
    print("\nThe innovation imperative: build it locally, own it completely.")


if __name__ == "__main__":
    demo()
