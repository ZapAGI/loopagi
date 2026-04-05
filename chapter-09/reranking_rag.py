"""
Chapter 9: Reranking RAG Implementation

Two-stage retrieval: retrieve broadly, then use the LLM to
rerank for precision. Elevates retrieval quality by trading
latency for accuracy.

Prerequisites:
    ollama pull llama3.2
    uv sync
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from loopagi.knowledge.rag import RAGEngine, RAGStrategy

KNOWLEDGE = """
Command Safety and Trust Scoring

The safety system uses 28 always-blocked patterns that are never
executed regardless of execution mode. These include dangerous
commands like recursive delete from root, fork bombs, direct disk
writes, and database drops. Blocked patterns use regex matching
for reliable detection.

Commands that are not blocked but potentially risky are classified
as "caution" level. These include sudo operations, package
installations, force pushes, and recursive deletes in non-root
directories. Caution commands require approval in Careful mode
but run automatically in Turbo mode.

Trust is modeled as a continuous function that decays over time
without reinforcement. The decay follows an exponential curve:
trust(t) = trust_0 * exp(-lambda * t), where lambda is the decay
rate and t is time since last reinforcement. Each successful
approved action reinforces trust. Each denied or failed action
penalizes it.

The trust score maps to four levels: high (0.8+), medium (0.5-0.8),
low (0.3-0.5), and minimal (below 0.3). The level determines
default behavior in borderline safety decisions.

Event-Driven Background Agents

Background agents subscribe to specific event types on the event
bus and react automatically when those events occur. The security
monitor subscribes to shell_command events. The test watcher
subscribes to file_write events. The health monitor subscribes to
all events using a wildcard subscription.

The event bus uses a publish-subscribe pattern with thread-safe
delivery. Events are processed synchronously by default but can
be emitted asynchronously using emit_async() for non-blocking
operation. Handler errors are caught and logged without crashing
the bus.

Each background agent can be enabled or disabled at runtime. This
allows the system to activate monitoring agents only when needed,
reducing overhead during lightweight operations.
"""


def demo() -> None:
    """Demonstrate Reranking RAG with two-stage retrieval."""
    print("Chapter 9: Reranking RAG - Two-Stage Retrieval")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        engine = RAGEngine(
            collection="reranking_demo",
            path=Path(tmpdir) / "rag",
            model="llama3.2",
            chunk_size=60,
            chunk_overlap=10,
        )

        print("\nIngesting knowledge base...")
        num_chunks = engine.ingest_text(KNOWLEDGE, source="safety_docs")
        print(f"  Stored {num_chunks} chunks")

        question = "How does the trust scoring system work?"

        print(f"\nQuestion: {question}\n")

        print("Strategy 1: Naive RAG")
        print("-" * 40)
        naive = engine.query(question, strategy=RAGStrategy.NAIVE, top_k=3)
        print(f"  Chunks: {naive.num_chunks_retrieved}")
        print(f"  Answer: {naive.answer[:200]}...")

        print("\nStrategy 2: Reranking RAG (retrieve 9, rerank to 3)")
        print("-" * 40)
        reranked = engine.query(question, strategy=RAGStrategy.RERANKING, top_k=3)
        print(f"  Chunks: {reranked.num_chunks_retrieved}")
        print(f"  Answer: {reranked.answer[:200]}...")

        print()
        print("Reranking RAG retrieves broadly (3x top_k), then uses the LLM")
        print("to rerank by relevance. Higher latency, higher precision.")


if __name__ == "__main__":
    demo()
