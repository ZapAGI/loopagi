"""
Chapter 9: RAG Strategy Decision Matrix

Interactive tool to choose the right RAG strategy based on
your requirements. Based on the Ragpedia decision framework.

The decision matrix considers:
- Query complexity (simple, moderate, complex, multi-hop)
- Corpus size (small, medium, large)
- Latency requirements (real-time, near-real-time, batch)
- Accuracy requirements (good enough, high, critical)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RAGStrategyProfile:
    """Profile of a RAG strategy with trade-offs."""

    name: str
    complexity: str
    latency: str
    accuracy: str
    best_for: str
    implementation_effort: str
    description: str


STRATEGIES: list[RAGStrategyProfile] = [
    RAGStrategyProfile(
        name="Naive RAG",
        complexity="low",
        latency="fast",
        accuracy="good",
        best_for="Simple factual queries, small corpora",
        implementation_effort="1 hour",
        description="Retrieve top-k chunks, stuff into prompt. The foundation.",
    ),
    RAGStrategyProfile(
        name="Sentence Window RAG",
        complexity="low",
        latency="fast",
        accuracy="better",
        best_for="When retrieved chunks lack surrounding context",
        implementation_effort="2 hours",
        description="Expand context around matched sentences for coherence.",
    ),
    RAGStrategyProfile(
        name="Parent-Child RAG",
        complexity="medium",
        latency="medium",
        accuracy="better",
        best_for="Hierarchical documents with sections and subsections",
        implementation_effort="4 hours",
        description="Match on child chunks, retrieve parent for full context.",
    ),
    RAGStrategyProfile(
        name="Fusion RAG",
        complexity="medium",
        latency="medium",
        accuracy="high",
        best_for="Ambiguous queries that benefit from multiple perspectives",
        implementation_effort="4 hours",
        description="Generate query variants, retrieve for each, merge results.",
    ),
    RAGStrategyProfile(
        name="HyDE RAG",
        complexity="medium",
        latency="slow",
        accuracy="high",
        best_for="Abstract or conceptual queries",
        implementation_effort="3 hours",
        description="Generate hypothetical answer, use it as the search query.",
    ),
    RAGStrategyProfile(
        name="Reranking RAG",
        complexity="medium",
        latency="medium",
        accuracy="high",
        best_for="When precision matters more than recall",
        implementation_effort="3 hours",
        description="Broad retrieval then LLM-based reranking for precision.",
    ),
    RAGStrategyProfile(
        name="Contextual Compression",
        complexity="medium",
        latency="medium",
        accuracy="high",
        best_for="Long chunks where only a portion is relevant",
        implementation_effort="3 hours",
        description="Compress retrieved chunks to extract only relevant parts.",
    ),
    RAGStrategyProfile(
        name="Agentic RAG",
        complexity="high",
        latency="slow",
        accuracy="very high",
        best_for="Complex tasks requiring iterative retrieval decisions",
        implementation_effort="8 hours",
        description="Agent decides what to retrieve, when, and how many times.",
    ),
    RAGStrategyProfile(
        name="Corrective RAG (CRAG)",
        complexity="high",
        latency="slow",
        accuracy="very high",
        best_for="When retrieval quality varies and web fallback is needed",
        implementation_effort="6 hours",
        description="Self-validate retrieval. If low quality, fall back to web.",
    ),
    RAGStrategyProfile(
        name="Graph RAG",
        complexity="high",
        latency="slow",
        accuracy="very high",
        best_for="Multi-hop reasoning across connected entities",
        implementation_effort="12 hours",
        description="Knowledge graphs for multi-hop reasoning chains.",
    ),
    RAGStrategyProfile(
        name="Self-RAG",
        complexity="high",
        latency="slow",
        accuracy="very high",
        best_for="When the model should evaluate its own retrieval quality",
        implementation_effort="8 hours",
        description="Model grades its own retrieval and regenerates if needed.",
    ),
    RAGStrategyProfile(
        name="Adaptive RAG",
        complexity="very high",
        latency="varies",
        accuracy="optimal",
        best_for="Production systems handling diverse query types",
        implementation_effort="16 hours",
        description="Dynamically selects strategy based on query complexity.",
    ),
]


def recommend_strategy(
    query_complexity: str = "moderate",
    corpus_size: str = "medium",
    latency_requirement: str = "near-real-time",
    accuracy_requirement: str = "high",
) -> list[RAGStrategyProfile]:
    """
    Recommend RAG strategies based on requirements.

    Returns strategies sorted by fit, best first.
    """
    def score(s: RAGStrategyProfile) -> int:
        points = 0

        # Complexity match
        complexity_map = {"low": 1, "medium": 2, "high": 3, "very high": 4}
        query_map = {"simple": 1, "moderate": 2, "complex": 3, "multi-hop": 4}
        s_complexity = complexity_map.get(s.complexity, 2)
        q_complexity = query_map.get(query_complexity, 2)
        if abs(s_complexity - q_complexity) <= 1:
            points += 3

        # Latency match
        latency_map = {"fast": 1, "medium": 2, "slow": 3, "varies": 2}
        req_map = {"real-time": 1, "near-real-time": 2, "batch": 3}
        if latency_map.get(s.latency, 2) <= req_map.get(latency_requirement, 2):
            points += 2

        # Accuracy match
        accuracy_map = {"good": 1, "better": 2, "high": 3, "very high": 4, "optimal": 5}
        req_accuracy = {"good enough": 1, "high": 3, "critical": 4}
        if accuracy_map.get(s.accuracy, 2) >= req_accuracy.get(accuracy_requirement, 2):
            points += 3

        return points

    scored = [(score(s), s) for s in STRATEGIES]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored]


def demo() -> None:
    """Interactive RAG strategy recommendation."""
    print("RAG Strategy Decision Matrix")
    print("=" * 60)
    print()

    # Show all strategies
    print(f"{'Strategy':<25} {'Complexity':<12} {'Latency':<10} {'Accuracy':<12} {'Effort'}")
    print("-" * 75)
    for s in STRATEGIES:
        print(
            f"{s.name:<25} {s.complexity:<12} {s.latency:<10}"
            f" {s.accuracy:<12} {s.implementation_effort}"
        )

    # Example recommendations
    scenarios = [
        {
            "name": "Simple Q&A Bot",
            "query_complexity": "simple",
            "corpus_size": "small",
            "latency_requirement": "real-time",
            "accuracy_requirement": "good enough",
        },
        {
            "name": "Code Documentation Search",
            "query_complexity": "moderate",
            "corpus_size": "medium",
            "latency_requirement": "near-real-time",
            "accuracy_requirement": "high",
        },
        {
            "name": "Legal Document Analysis",
            "query_complexity": "complex",
            "corpus_size": "large",
            "latency_requirement": "batch",
            "accuracy_requirement": "critical",
        },
    ]

    print("\n\nRecommendations by Scenario:")
    print("=" * 60)

    for scenario in scenarios:
        name = scenario.pop("name")
        recommendations = recommend_strategy(**scenario)
        print(f"\n  Scenario: {name}")
        print(f"  Requirements: {scenario}")
        print("  Top 3 recommendations:")
        for i, s in enumerate(recommendations[:3], 1):
            print(f"    {i}. {s.name} - {s.description}")
        scenario["name"] = name  # restore


if __name__ == "__main__":
    demo()
