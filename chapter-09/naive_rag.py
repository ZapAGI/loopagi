"""
Chapter 9: Naive RAG Implementation

The foundation everyone starts with. Retrieve top-k chunks
from a vector store and stuff them into the LLM prompt.

Retrieval is the bridge between what a model knows
and what the world contains.

Prerequisites:
    ollama pull llama3.2
    uv sync
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from loopagi.knowledge.rag import RAGEngine, RAGStrategy

# Sample knowledge base about multi-agent systems
KNOWLEDGE_BASE = """
Multi-Agent Systems in Artificial Intelligence

Agent Orchestration
An agent orchestration system coordinates multiple specialized AI agents
to solve complex tasks. Each agent has a specific role, such as coding,
testing, reviewing, or researching. The orchestrator decides which agent
handles each subtask based on the requirements.

Hierarchical Architecture
A three-tier hierarchy consists of a Master orchestrator, Team Leads for
each domain, and Worker agents that execute specific tasks. This structure
reduces coordination overhead from O(n-squared) to O(n), where n is the
number of agents.

Agent Pools
Agent pools allow multiple instances of the same agent type to work in
parallel. For example, three coder agents can work on different files
simultaneously. This is particularly useful when tasks are independent
and can be parallelized.

Quality Pipeline
The quality pipeline chains four agents in sequence: Planner creates the
implementation plan, Coder writes the code, Tester generates tests, and
Reviewer evaluates the result. If the reviewer rejects the code, it loops
back to the planner with feedback.

RAG Systems
Retrieval-Augmented Generation combines the knowledge of a language model
with external data sources. The system retrieves relevant documents from
a vector store and includes them in the prompt, giving the model access
to information beyond its training data.

Vector Embeddings
Text is converted into numerical vectors using embedding models. Similar
texts produce similar vectors. Cosine similarity measures how close two
vectors are, enabling semantic search that finds relevant documents based
on meaning rather than exact keyword matches.

Local-First Philosophy
A local-first approach keeps all data and processing on the user's machine.
No API keys are needed. No data leaves the device. This provides privacy,
reduces latency, and ensures the system works offline.

Session as Git
Every AI interaction session is stored as a git repository. Each message
and action becomes a commit. This creates a complete provenance trail
showing who wrote what code and when, enabling reproducibility and
collaboration through standard git workflows.
"""


def demo() -> None:
    """Demonstrate Naive RAG with a sample knowledge base."""
    print("Chapter 9: Naive RAG Implementation")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        engine = RAGEngine(
            collection="demo_rag",
            path=Path(tmpdir) / "rag",
            model="llama3.2",
            chunk_size=80,
            chunk_overlap=10,
        )

        # Ingest knowledge base
        print("\nIngesting knowledge base...")
        num_chunks = engine.ingest_text(KNOWLEDGE_BASE, source="multi_agent_intro")
        print(f"  Stored {num_chunks} chunks")

        # Query with different strategies
        questions = [
            "How does agent routing work?",
            "What is the quality pipeline?",
            "Why use local-first architecture?",
            "How are sessions tracked?",
        ]

        print("\nQuerying with Naive RAG strategy:")
        print("-" * 50)

        for question in questions:
            result = engine.query(question, strategy=RAGStrategy.NAIVE, top_k=3)
            print(f"\nQ: {question}")
            print(f"A: {result.answer[:200]}...")
            print(f"   (Retrieved {result.num_chunks_retrieved} chunks)")

    print()
    print("Naive RAG: the foundation. Simple, effective, and the starting")
    print("point for all more advanced strategies.")


if __name__ == "__main__":
    demo()
