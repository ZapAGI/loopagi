"""
Chapter 9: Fusion RAG Implementation

Multi-query expansion for better recall. Generate multiple
phrasings of the same question, retrieve for each, merge
and deduplicate results.

Prerequisites:
    ollama pull llama3.2
    uv sync
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from loopagi.knowledge.rag import RAGEngine, RAGStrategy

KNOWLEDGE = """
Agent Pools and Parallel Execution

Agent pools allow multiple instances of the same specialist to work
simultaneously on different tasks. A pool of three coder agents can
write three different modules at the same time, reducing total
completion time by up to 3x for independent tasks.

The pool manager distributes tasks round-robin across available
instances. When all instances are busy, new tasks queue until an
instance becomes available. Results are collected and returned in
submission order.

The identity question arises naturally: if three coder agents with
identical prompts produce different code for the same task, which
one is the "real" coder? The answer from the book: parallel minds
are not copies, they are perspectives.

Quality Pipeline Architecture

The quality pipeline chains four specialist agents in sequence:
planner, coder, tester, and reviewer. The planner creates an
implementation plan. The coder writes code following that plan.
The tester generates pytest tests. The reviewer evaluates both
code and tests against quality criteria.

If the reviewer rejects the code, the pipeline loops back to the
planner with specific feedback. This feedback loop is the first
example of machine self-improvement in the system.

The maximum iteration count prevents infinite loops. Typical
tasks converge within 2-3 iterations.

Hierarchical Routing

The routing engine uses a three-tier architecture: Master
orchestrator at the top, team leads in the middle, and worker
agents at the bottom. This reduces coordination overhead from
O(n squared) for flat organizations to O(n) for hierarchical ones.

Routing decisions use a two-phase approach: fast keyword matching
first (no LLM call required), then LLM-based classification as
a fallback for ambiguous queries. The keyword phase handles about
70 percent of queries with zero latency overhead.
"""


def demo() -> None:
    """Demonstrate Fusion RAG with multi-query expansion."""
    print("Chapter 9: Fusion RAG - Multi-Query Expansion")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        engine = RAGEngine(
            collection="fusion_demo",
            path=Path(tmpdir) / "rag",
            model="llama3.2",
            chunk_size=60,
            chunk_overlap=10,
        )

        print("\nIngesting knowledge base...")
        num_chunks = engine.ingest_text(KNOWLEDGE, source="architecture_docs")
        print(f"  Stored {num_chunks} chunks")

        # Compare Naive vs Fusion
        question = "How do parallel agents handle tasks?"

        print(f"\nQuestion: {question}\n")

        print("Strategy 1: Naive RAG (single query)")
        print("-" * 40)
        naive_result = engine.query(question, strategy=RAGStrategy.NAIVE, top_k=3)
        print(f"  Retrieved {naive_result.num_chunks_retrieved} chunks")
        print(f"  Answer: {naive_result.answer[:200]}...")

        print("\nStrategy 2: Fusion RAG (multi-query expansion)")
        print("-" * 40)
        fusion_result = engine.query(question, strategy=RAGStrategy.FUSION, top_k=3)
        print(f"  Retrieved {fusion_result.num_chunks_retrieved} chunks")
        print(f"  Answer: {fusion_result.answer[:200]}...")

        print("\nFusion RAG generates multiple query variants and merges results,")
        print("improving recall for questions that can be phrased multiple ways.")


if __name__ == "__main__":
    demo()
