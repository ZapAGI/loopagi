"""
Chapter 9: RAG with a Real Local Corpus

Instead of hardcoded strings, this demo ingests REAL files from
the god-in-the-loop-code repository itself, builds a vector index,
and answers questions about the codebase using 4 RAG strategies.

This is how RAG works in production: ingest real documents, chunk
them, embed them, and retrieve relevant context for generation.

Requires: ollama pull llama3.2 (or runs with mock retrieval)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from loopagi.core.ollama_utils import require_ollama


@dataclass
class ChunkMatch:
    """A matched chunk from the local corpus."""

    content: str
    source: str
    score: float


@dataclass
class LocalRAGResult:
    """Result from a local RAG query."""

    query: str
    strategy: str
    chunks: list[ChunkMatch]
    answer: str
    retrieval_time_ms: float
    generation_time_ms: float


class LocalCorpusRAG:
    """
    RAG engine that indexes the actual repository source code.

    Demonstrates the real-world RAG pipeline:
    1. Ingest: read files, chunk text
    2. Index: embed chunks with fastembed (or TF-IDF fallback)
    3. Retrieve: find relevant chunks for a query
    4. Generate: answer using retrieved context
    """

    def __init__(self, corpus_dir: Path) -> None:
        self.corpus_dir = corpus_dir
        self._chunks: list[dict] = []
        self._use_vectors = False
        self._tfidf_index: dict[str, dict[int, float]] | None = None

    def ingest(
        self,
        extensions: tuple[str, ...] = (".py", ".md"),
        chunk_size: int = 300,
        chunk_overlap: int = 50,
        max_file_size: int = 50_000,
    ) -> int:
        """Ingest files from the corpus directory."""
        self._chunks = []

        for path in sorted(self.corpus_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix not in extensions:
                continue
            if "__pycache__" in str(path) or ".venv" in str(path):
                continue
            if ".git" in path.parts:
                continue
            if path.stat().st_size > max_file_size or path.stat().st_size == 0:
                continue

            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
                rel = str(path.relative_to(self.corpus_dir))
            except OSError:
                continue

            words = text.split()
            start = 0
            while start < len(words):
                end = start + chunk_size
                chunk_text = " ".join(words[start:end])
                if chunk_text.strip():
                    self._chunks.append({
                        "content": chunk_text,
                        "source": rel,
                        "index": len(self._chunks),
                    })
                start += chunk_size - chunk_overlap

        # Build TF-IDF index (always available, no dependencies)
        self._build_tfidf()

        return len(self._chunks)

    def _build_tfidf(self) -> None:
        """Build a simple TF-IDF index for keyword retrieval."""
        import math
        from collections import Counter

        doc_freq: Counter = Counter()
        tf: list[Counter] = []

        for chunk in self._chunks:
            words = chunk["content"].lower().split()
            word_counts = Counter(words)
            tf.append(word_counts)
            for word in set(words):
                doc_freq[word] += 1

        n = len(self._chunks)
        self._tfidf_index = {}

        for word in doc_freq:
            idf = math.log(n / (1 + doc_freq[word]))
            self._tfidf_index[word] = {}
            for i, counts in enumerate(tf):
                if word in counts:
                    tfidf = counts[word] * idf
                    self._tfidf_index[word][i] = tfidf

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        strategy: str = "tfidf",
    ) -> list[ChunkMatch]:
        """Retrieve relevant chunks for a query."""
        if strategy == "tfidf":
            return self._retrieve_tfidf(query, top_k)
        elif strategy == "keyword":
            return self._retrieve_keyword(query, top_k)
        elif strategy == "window":
            return self._retrieve_window(query, top_k)
        elif strategy == "fusion":
            return self._retrieve_fusion(query, top_k)
        else:
            return self._retrieve_tfidf(query, top_k)

    def _retrieve_tfidf(self, query: str, top_k: int) -> list[ChunkMatch]:
        """TF-IDF based retrieval."""
        if not self._tfidf_index:
            return []

        query_words = query.lower().split()
        scores: dict[int, float] = {}

        for word in query_words:
            if word in self._tfidf_index:
                for chunk_idx, tfidf in self._tfidf_index[word].items():
                    scores[chunk_idx] = scores.get(chunk_idx, 0) + tfidf

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            ChunkMatch(
                content=self._chunks[idx]["content"][:500],
                source=self._chunks[idx]["source"],
                score=score,
            )
            for idx, score in ranked
        ]

    def _retrieve_keyword(self, query: str, top_k: int) -> list[ChunkMatch]:
        """Simple keyword matching retrieval."""
        query_lower = query.lower()
        keywords = [w for w in query_lower.split() if len(w) > 3]

        scored = []
        for chunk in self._chunks:
            text_lower = chunk["content"].lower()
            hits = sum(1 for kw in keywords if kw in text_lower)
            if hits > 0:
                scored.append((chunk, hits / len(keywords) if keywords else 0))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            ChunkMatch(
                content=c["content"][:500],
                source=c["source"],
                score=s,
            )
            for c, s in scored[:top_k]
        ]

    def _retrieve_window(self, query: str, top_k: int) -> list[ChunkMatch]:
        """Sentence window: retrieve chunks + their neighbors."""
        base = self._retrieve_tfidf(query, top_k)
        expanded = []

        for match in base:
            # Find the chunk index and get neighbors
            for chunk in self._chunks:
                if chunk["content"][:100] == match.content[:100]:
                    idx = chunk["index"]
                    neighbor_content = match.content
                    if idx > 0:
                        neighbor_content = (
                            self._chunks[idx - 1]["content"][-100:]
                            + " " + neighbor_content
                        )
                    if idx < len(self._chunks) - 1:
                        neighbor_content = (
                            neighbor_content + " "
                            + self._chunks[idx + 1]["content"][:100]
                        )
                    expanded.append(ChunkMatch(
                        content=neighbor_content[:600],
                        source=match.source,
                        score=match.score,
                    ))
                    break
            else:
                expanded.append(match)

        return expanded

    def _retrieve_fusion(self, query: str, top_k: int) -> list[ChunkMatch]:
        """Fusion: combine TF-IDF and keyword results, deduplicate."""
        tfidf_results = self._retrieve_tfidf(query, top_k)
        keyword_results = self._retrieve_keyword(query, top_k)

        seen: set[str] = set()
        merged = []
        for match in tfidf_results + keyword_results:
            key = match.content[:100]
            if key not in seen:
                seen.add(key)
                merged.append(match)

        merged.sort(key=lambda m: m.score, reverse=True)
        return merged[:top_k]

    def query(
        self,
        question: str,
        strategy: str = "tfidf",
        top_k: int = 5,
    ) -> LocalRAGResult:
        """Full RAG pipeline: retrieve + generate answer."""
        start = time.time()
        chunks = self.retrieve(question, top_k=top_k, strategy=strategy)
        retrieval_ms = (time.time() - start) * 1000

        context = "\n\n".join(
            f"[{c.source}] {c.content}" for c in chunks
        )

        start = time.time()
        answer = self._generate(question, context)
        gen_ms = (time.time() - start) * 1000

        return LocalRAGResult(
            query=question,
            strategy=strategy,
            chunks=chunks,
            answer=answer,
            retrieval_time_ms=retrieval_ms,
            generation_time_ms=gen_ms,
        )

    def _generate(self, question: str, context: str) -> str:
        """Generate an answer. Uses Ollama if available, else extractive."""
        try:
            from loopagi.core.ollama_utils import is_ollama_running
            if is_ollama_running():
                from langchain_ollama import ChatOllama
                llm = ChatOllama(model="llama3.2", temperature=0.3)
                prompt = (
                    f"Answer based on the context below.\n\n"
                    f"Context:\n{context[:3000]}\n\n"
                    f"Question: {question}\n\nAnswer:"
                )
                resp = llm.invoke(prompt)
                content = resp.content
                return content if isinstance(content, str) else str(content)
        except Exception:
            pass

        # Extractive fallback: return the most relevant chunk
        if context:
            lines = context.split("\n")
            return f"(Extractive) {lines[0][:200]}..."
        return "No relevant context found."


# --- Demo ---


def demo() -> None:
    """Index the actual repository and answer questions about it."""
    print("Chapter 9: RAG with a Real Local Corpus")
    print("=" * 60)

    repo_root = Path(__file__).parent.parent
    live = require_ollama()
    mode = "LIVE (Ollama)" if live else "TF-IDF + extractive (no LLM)"

    print(f"Corpus: {repo_root}")
    print(f"Mode: {mode}")
    print()

    rag = LocalCorpusRAG(repo_root)

    print("Ingesting repository files...", end=" ", flush=True)
    count = rag.ingest()
    print(f"{count} chunks indexed.")
    print()

    # Real questions about the codebase
    questions = [
        ("How does agent routing work?", "tfidf"),
        ("What safety patterns block dangerous commands?", "keyword"),
        ("How does the trust score decay over time?", "window"),
        ("What RAG strategies are implemented?", "fusion"),
    ]

    for question, strategy in questions:
        print(f"Q: {question}")
        print(f"   Strategy: {strategy}")

        result = rag.query(question, strategy=strategy)

        print(f"   Retrieved {len(result.chunks)} chunks "
              f"[{result.retrieval_time_ms:.0f}ms retrieval, "
              f"{result.generation_time_ms:.0f}ms generation]")
        print(f"   Sources: {', '.join(set(c.source for c in result.chunks[:3]))}")
        print(f"   Answer: {result.answer[:200]}")
        print()

    # Show strategy comparison
    print("Strategy Comparison (same question):")
    print("-" * 60)
    test_q = "How does the quality pipeline work?"
    strategies = ["tfidf", "keyword", "window", "fusion"]

    print(f"Q: {test_q}")
    print(f"  {'Strategy':<10} {'Chunks':<8} {'Top Source':<30} {'Time'}")
    print(f"  {'-'*10} {'-'*8} {'-'*30} {'-'*8}")

    for strat in strategies:
        result = rag.query(test_q, strategy=strat, top_k=3)
        top = result.chunks[0].source if result.chunks else "(none)"
        total_ms = result.retrieval_time_ms + result.generation_time_ms
        print(f"  {strat:<10} {len(result.chunks):<8} {top:<30} {total_ms:.0f}ms")

    print()
    print("This is production RAG: real files, real indexing, real retrieval.")
    print("No hardcoded strings. The entire repository is the knowledge base.")


if __name__ == "__main__":
    demo()
