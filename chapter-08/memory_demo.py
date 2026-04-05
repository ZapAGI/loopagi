"""
Chapter 8: Memory Demo

Persistent vector memory with Qdrant. Memory is not storage.
It is reconstruction. Both for agents and for us.

Prerequisites:
    uv sync  (installs qdrant-client and fastembed)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from loopagi.knowledge.memory import MemoryStore


def demo() -> None:
    """Demonstrate semantic memory storage and retrieval."""
    print("Chapter 8: Persistent Vector Memory")
    print("=" * 60)

    # Use a temp directory for this demo
    with tempfile.TemporaryDirectory() as tmpdir:
        store = MemoryStore(
            collection="demo_memory",
            path=Path(tmpdir) / "memory",
        )

        # Store memories
        memories = [
            "The user prefers functional programming patterns over OOP",
            "Project uses FastAPI for the REST backend",
            "Always use pytest for testing, never unittest",
            "The database is PostgreSQL with SQLAlchemy ORM",
            "Deployment target is Docker on Ubuntu 25.10",
            "The user's name is Alex and they work at 2 AM",
            "Code style: type hints required, PEP 8, 100 char line limit",
            "The team uses git flow: feature branches off develop",
        ]

        print("\nStoring memories...")
        for mem in memories:
            store.add(mem)
            print(f"  + {mem[:60]}")

        print(f"\nTotal memories stored: {store.count()}")

        # Search by semantic similarity
        queries = [
            "What programming style does the user prefer?",
            "What web framework is used?",
            "How should I write tests?",
            "What database are we using?",
            "What are the code conventions?",
        ]

        print("\nSemantic Search Results:")
        print("-" * 50)

        for query in queries:
            results = store.search(query, limit=2)
            print(f"\n  Q: {query}")
            for r in results:
                print(f"    [{r.score:.3f}] {r.content[:70]}")

        print()
        print("Memory is not exact-match lookup. It is semantic reconstruction.")
        print("The agent finds what is RELEVANT, not just what matches keywords.")


if __name__ == "__main__":
    demo()
