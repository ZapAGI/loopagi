"""
Chapter 9: RAG Evaluation with RAGAS Metrics

Evaluate RAG quality using four key metrics:
- Faithfulness: does the answer stick to the retrieved context?
- Answer Relevancy: does the answer address the question?
- Context Precision: are the retrieved chunks relevant?
- Context Recall: did we retrieve all necessary information?

These metrics can be computed without ground truth labels
using LLM-as-judge patterns.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RAGASScore:
    """RAGAS evaluation scores for a single query."""

    query: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float

    @property
    def overall(self) -> float:
        """Harmonic mean of all four metrics."""
        scores = [self.faithfulness, self.answer_relevancy,
                  self.context_precision, self.context_recall]
        scores = [s for s in scores if s > 0]
        if not scores:
            return 0.0
        return len(scores) / sum(1.0 / s for s in scores)


def faithfulness_score(answer: str, context: str) -> float:
    """
    Measure faithfulness: how much of the answer is grounded in context.

    Simple heuristic: fraction of answer sentences that contain
    words from the context. Production systems use LLM-as-judge.
    """
    if not answer or not context:
        return 0.0

    context_words = set(context.lower().split())
    # Remove common stop words
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
                  "to", "for", "of", "and", "or", "but", "with", "this", "that"}
    context_words -= stop_words

    sentences = [s.strip() for s in answer.replace("\n", ". ").split(".") if s.strip()]
    if not sentences:
        return 0.0

    grounded = 0
    for sentence in sentences:
        sentence_words = set(sentence.lower().split()) - stop_words
        if not sentence_words:
            continue
        overlap = len(sentence_words & context_words) / len(sentence_words)
        if overlap > 0.3:  # At least 30% of words from context
            grounded += 1

    return grounded / len(sentences)


def answer_relevancy_score(answer: str, query: str) -> float:
    """
    Measure answer relevancy: does the answer address the question?

    Simple heuristic: fraction of query keywords present in the answer.
    Production systems use LLM-as-judge.
    """
    if not answer or not query:
        return 0.0

    stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
                  "to", "for", "of", "and", "or", "but", "with", "what", "how",
                  "why", "when", "where", "does", "do", "should", "can"}

    query_words = set(query.lower().split()) - stop_words
    answer_words = set(answer.lower().split()) - stop_words

    if not query_words:
        return 1.0

    overlap = len(query_words & answer_words)
    return overlap / len(query_words)


def context_precision_score(chunks: list[str], query: str) -> float:
    """
    Measure context precision: are the retrieved chunks relevant?

    Fraction of retrieved chunks that contain query-related terms.
    """
    if not chunks or not query:
        return 0.0

    stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
                  "to", "for", "of", "and", "or", "but", "with"}

    query_words = set(query.lower().split()) - stop_words
    relevant = 0

    for chunk in chunks:
        chunk_words = set(chunk.lower().split()) - stop_words
        overlap = len(query_words & chunk_words)
        if overlap >= 2:  # At least 2 query terms present
            relevant += 1

    return relevant / len(chunks)


def context_recall_score(chunks: list[str], reference_answer: str) -> float:
    """
    Measure context recall: did we retrieve all necessary information?

    Fraction of reference answer sentences supported by at least one chunk.
    Requires a reference answer (ground truth).
    """
    if not chunks or not reference_answer:
        return 0.0

    stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
                  "to", "for", "of", "and", "or", "but", "with"}

    all_chunk_words = set()
    for chunk in chunks:
        all_chunk_words |= set(chunk.lower().split()) - stop_words

    sentences = [s.strip() for s in reference_answer.split(".") if len(s.strip()) > 10]
    if not sentences:
        return 0.0

    supported = 0
    for sentence in sentences:
        sentence_words = set(sentence.lower().split()) - stop_words
        if not sentence_words:
            continue
        overlap = len(sentence_words & all_chunk_words) / len(sentence_words)
        if overlap > 0.3:
            supported += 1

    return supported / len(sentences)


def evaluate_rag(
    query: str,
    answer: str,
    context_chunks: list[str],
    reference_answer: str = "",
) -> RAGASScore:
    """Run full RAGAS evaluation on a RAG query result."""
    context = " ".join(context_chunks)
    return RAGASScore(
        query=query,
        faithfulness=faithfulness_score(answer, context),
        answer_relevancy=answer_relevancy_score(answer, query),
        context_precision=context_precision_score(context_chunks, query),
        context_recall=context_recall_score(context_chunks, reference_answer or answer),
    )


# --- Demonstration ---


def demo() -> None:
    """Demonstrate RAGAS evaluation metrics."""
    print("Chapter 9: RAG Evaluation (RAGAS Metrics)")
    print("=" * 60)

    # Simulate three RAG scenarios
    scenarios = [
        {
            "name": "Good RAG",
            "query": "How does agent routing work in a multi-agent system?",
            "chunks": [
                (
                    "The routing engine uses keyword matching and LLM"
                    " classification to route tasks to specialist agents."
                ),
                (
                    "Agent routing supports a three-tier hierarchy:"
                    " master orchestrator, team leads, and worker agents."
                ),
                (
                    "Fast keyword routing handles 70% of queries."
                    " LLM fallback handles ambiguous cases."
                ),
            ],
            "answer": (
                "Agent routing in a multi-agent system works through a two-phase approach. "
                "First, fast keyword matching handles about 70% of queries without an LLM call. "
                "For ambiguous cases, LLM classification determines the best specialist agent. "
                "The system uses a three-tier hierarchy with a master orchestrator routing to "
                "team leads who then delegate to worker agents."
            ),
        },
        {
            "name": "Hallucinated RAG",
            "query": "How does agent routing work in a multi-agent system?",
            "chunks": [
                "The routing engine uses keyword matching to route tasks.",
                "Agents are organized in a hierarchy.",
            ],
            "answer": (
                "Agent routing uses quantum entanglement to instantly determine the best agent. "
                "The system reads the user's mind through neural interfaces and predicts their "
                "intent before they finish typing. Routes are cached"
                " in a blockchain for immutability."
            ),
        },
        {
            "name": "Irrelevant Context RAG",
            "query": "How does agent routing work in a multi-agent system?",
            "chunks": [
                "Docker containers provide isolation for running services.",
                "Python 3.12 introduced new pattern matching features.",
                "The weather in March is unpredictable.",
            ],
            "answer": (
                "Agent routing probably involves some kind of message passing between agents. "
                "The details depend on the specific implementation."
            ),
        },
    ]

    for scenario in scenarios:
        score = evaluate_rag(
            query=scenario["query"],
            answer=scenario["answer"],
            context_chunks=scenario["chunks"],
        )

        print(f"\nScenario: {scenario['name']}")
        print("-" * 50)
        print(f"  Faithfulness:       {score.faithfulness:.3f}")
        print(f"  Answer Relevancy:   {score.answer_relevancy:.3f}")
        print(f"  Context Precision:  {score.context_precision:.3f}")
        print(f"  Context Recall:     {score.context_recall:.3f}")
        print(f"  Overall (harmonic): {score.overall:.3f}")

    # Explanation
    print("\n\nMetric Definitions:")
    print("-" * 50)
    metrics = [
        ("Faithfulness", "Is the answer grounded in the retrieved context?"),
        ("Answer Relevancy", "Does the answer actually address the question?"),
        ("Context Precision", "Are the retrieved chunks relevant to the query?"),
        ("Context Recall", "Did we retrieve ALL the information needed?"),
    ]
    for name, desc in metrics:
        print(f"  {name:<22} {desc}")

    print()
    print("Good RAG scores high on all four metrics.")
    print("Hallucinated RAG scores low on faithfulness.")
    print("Irrelevant context scores low on precision and recall.")


if __name__ == "__main__":
    demo()
