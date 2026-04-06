"""
Chapter 9: Ragonomics - The Science of Retrieval-Augmented Generation

RAG-powered knowledge retrieval. Retrieval is the bridge between
what a model knows and what the world contains.

Implements multiple RAG strategies from the Ragpedia encyclopedia:
- Naive RAG: simple retrieve-and-generate
- Sentence Window RAG: expanded context around matches
- Fusion RAG: multi-query expansion
- Reranking RAG: two-stage retrieval with reranking

Usage:
    from loopagi.knowledge.rag import RAGEngine, RAGStrategy

    engine = RAGEngine()
    engine.ingest("path/to/documents/")
    answer = engine.query("How does agent routing work?", strategy=RAGStrategy.NAIVE)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from langchain_ollama import ChatOllama
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

logger = logging.getLogger(__name__)

DEFAULT_RAG_PATH = Path.home() / ".local" / "share" / "loopagi" / "rag"


class RAGStrategy(str, Enum):
    """Available RAG strategies, ordered by complexity."""

    NAIVE = "naive"
    SENTENCE_WINDOW = "sentence_window"
    FUSION = "fusion"
    RERANKING = "reranking"


@dataclass
class RetrievedChunk:
    """A chunk of text retrieved from the knowledge base."""

    content: str
    source: str
    score: float
    metadata: dict = field(default_factory=dict)


@dataclass
class RAGResult:
    """Complete result from a RAG query."""

    query: str
    strategy: RAGStrategy
    answer: str
    chunks: list[RetrievedChunk] = field(default_factory=list)
    num_chunks_retrieved: int = 0


class RAGEngine:
    """
    Multi-strategy RAG engine for knowledge retrieval.

    How does a system know what it does not know? Once it discovers
    its own knowledge gaps, how does it decide where to look?

    This engine implements four strategies from the Ragpedia:
    1. Naive RAG: retrieve top-k chunks, stuff into prompt
    2. Sentence Window: expand context around matched sentences
    3. Fusion RAG: generate multiple query variants, merge results
    4. Reranking RAG: retrieve broadly, then rerank for precision
    """

    def __init__(
        self,
        collection: str = "loopagi_knowledge",
        path: Path | str | None = None,
        model: str = "llama3.2",
        embedding_dim: int = 384,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        self.collection = collection
        self.model = model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_dim = embedding_dim
        self._path = Path(path) if path else DEFAULT_RAG_PATH
        self._path.mkdir(parents=True, exist_ok=True)

        self.client = QdrantClient(path=str(self._path))
        self.llm = ChatOllama(model=model, temperature=0.3)
        self._embedding_model = None
        self._ensure_collection()
        logger.info("RAGEngine initialized (strategy support: %s)", [s.value for s in RAGStrategy])

    def _ensure_collection(self) -> None:
        """Create collection if it does not exist."""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection not in collections:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE,
                ),
            )

    def _get_embedding_model(self):
        """Lazy-load embedding model."""
        if self._embedding_model is None:
            from fastembed import TextEmbedding

            self._embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        return self._embedding_model

    def _embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        model = self._get_embedding_model()
        return list(model.embed([text]))[0].tolist()

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        model = self._get_embedding_model()
        return [e.tolist() for e in model.embed(texts)]

    # --- Ingestion ---

    def ingest_text(self, text: str, source: str = "manual") -> int:
        """Ingest a text string by chunking and embedding it."""
        chunks = self._chunk_text(text)
        return self._store_chunks(chunks, source)

    def ingest_file(self, file_path: Path | str) -> int:
        """Ingest a text file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        text = path.read_text(encoding="utf-8")
        return self.ingest_text(text, source=str(path))

    def ingest_directory(self, dir_path: Path | str, pattern: str = "*.txt") -> int:
        """Ingest all matching files in a directory."""
        path = Path(dir_path)
        total = 0
        for file in sorted(path.glob(pattern)):
            if file.is_file():
                count = self.ingest_file(file)
                total += count
                logger.info("Ingested %s (%d chunks)", file.name, count)
        logger.info("Ingested %d total chunks from %s", total, dir_path)
        return total

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + self.chunk_size
            chunk = " ".join(words[start:end])
            if chunk.strip():
                chunks.append(chunk)
            start += self.chunk_size - self.chunk_overlap
        return chunks

    def _store_chunks(self, chunks: list[str], source: str) -> int:
        """Embed and store chunks in Qdrant."""
        if not chunks:
            return 0

        embeddings = self._embed_batch(chunks)
        import uuid

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=emb,
                payload={
                    "content": chunk,
                    "source": source,
                    "chunk_index": i,
                },
            )
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]
        self.client.upsert(collection_name=self.collection, points=points)
        return len(points)

    # --- Retrieval Strategies ---

    def query(
        self,
        question: str,
        strategy: RAGStrategy = RAGStrategy.NAIVE,
        top_k: int = 5,
    ) -> RAGResult:
        """
        Query the knowledge base using the specified RAG strategy.
        """
        match strategy:
            case RAGStrategy.NAIVE:
                return self._naive_rag(question, top_k)
            case RAGStrategy.SENTENCE_WINDOW:
                return self._sentence_window_rag(question, top_k)
            case RAGStrategy.FUSION:
                return self._fusion_rag(question, top_k)
            case RAGStrategy.RERANKING:
                return self._reranking_rag(question, top_k)

    def _naive_rag(self, question: str, top_k: int) -> RAGResult:
        """
        Naive RAG: retrieve top-k chunks, stuff into prompt.
        The foundation everyone starts with.
        """
        chunks = self._retrieve(question, top_k)
        context = "\n\n".join(c.content for c in chunks)
        answer = self._generate(question, context)
        return RAGResult(
            query=question,
            strategy=RAGStrategy.NAIVE,
            answer=answer,
            chunks=chunks,
            num_chunks_retrieved=len(chunks),
        )

    def _sentence_window_rag(self, question: str, top_k: int) -> RAGResult:
        """
        Sentence Window RAG: retrieve chunks, then expand context
        by including neighboring chunks for better coherence.
        """
        chunks = self._retrieve(question, top_k)
        # Expand each chunk by retrieving its neighbors
        expanded_chunks = []
        for chunk in chunks:
            idx = chunk.metadata.get("chunk_index", 0)
            # Retrieve the chunk before and after
            neighbors = self._retrieve_by_index(chunk.source, idx - 1, idx + 1)
            expanded = " ".join([n.content for n in neighbors if n.content] + [chunk.content])
            expanded_chunks.append(RetrievedChunk(
                content=expanded,
                source=chunk.source,
                score=chunk.score,
                metadata=chunk.metadata,
            ))

        context = "\n\n".join(c.content for c in expanded_chunks)
        answer = self._generate(question, context)
        return RAGResult(
            query=question,
            strategy=RAGStrategy.SENTENCE_WINDOW,
            answer=answer,
            chunks=expanded_chunks,
            num_chunks_retrieved=len(expanded_chunks),
        )

    def _fusion_rag(self, question: str, top_k: int) -> RAGResult:
        """
        Fusion RAG: generate multiple query variants, retrieve for each,
        then merge and deduplicate results. Query expansion for recall.
        """
        # Generate query variants using the LLM
        variants = self._generate_query_variants(question, num_variants=3)
        all_chunks: dict[str, RetrievedChunk] = {}

        for variant in [question] + variants:
            chunks = self._retrieve(variant, top_k)
            for chunk in chunks:
                key = chunk.content[:100]
                if key not in all_chunks or chunk.score > all_chunks[key].score:
                    all_chunks[key] = chunk

        # Sort by score and take top_k
        merged = sorted(all_chunks.values(), key=lambda c: c.score, reverse=True)[:top_k]
        context = "\n\n".join(c.content for c in merged)
        answer = self._generate(question, context)
        return RAGResult(
            query=question,
            strategy=RAGStrategy.FUSION,
            answer=answer,
            chunks=merged,
            num_chunks_retrieved=len(merged),
        )

    def _reranking_rag(self, question: str, top_k: int) -> RAGResult:
        """
        Reranking RAG: retrieve broadly (3x top_k), then use the LLM
        to rerank for precision. Two-stage retrieval.
        """
        # Stage 1: Broad retrieval
        broad_chunks = self._retrieve(question, top_k * 3)

        # Stage 2: LLM-based reranking
        reranked = self._rerank(question, broad_chunks, top_k)
        context = "\n\n".join(c.content for c in reranked)
        answer = self._generate(question, context)
        return RAGResult(
            query=question,
            strategy=RAGStrategy.RERANKING,
            answer=answer,
            chunks=reranked,
            num_chunks_retrieved=len(reranked),
        )

    # --- Helpers ---

    def _retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        """Retrieve top-k chunks by vector similarity."""
        vector = self._embed(query)
        results = self.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=top_k,
        )
        return [
            RetrievedChunk(
                content=hit.payload.get("content", ""),
                source=hit.payload.get("source", ""),
                score=hit.score,
                metadata={
                    k: v for k, v in hit.payload.items()
                    if k not in ("content", "source")
                },
            )
            for hit in results
        ]

    def _retrieve_by_index(self, source: str, start_idx: int, end_idx: int) -> list[RetrievedChunk]:
        """Retrieve chunks by source and index range (for sentence window)."""
        from qdrant_client.models import FieldCondition, Filter, MatchValue, Range

        try:
            results = self.client.scroll(
                collection_name=self.collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="source", match=MatchValue(value=source)),
                        FieldCondition(
                            key="chunk_index",
                            range=Range(gte=max(0, start_idx), lte=end_idx),
                        ),
                    ]
                ),
                limit=10,
            )
            points = results[0] if results else []
            return [
                RetrievedChunk(
                    content=p.payload.get("content", ""),
                    source=source,
                    score=1.0,
                )
                for p in points
            ]
        except Exception:
            return []

    def _generate(self, question: str, context: str) -> str:
        """Generate an answer using the LLM with retrieved context."""
        prompt = (
            f"Answer the question based on the following context.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            f"Answer:"
        )
        response = self.llm.invoke(prompt)
        return response.content if isinstance(response.content, str) else str(response.content)

    def _generate_query_variants(self, question: str, num_variants: int = 3) -> list[str]:
        """Generate query variants for Fusion RAG."""
        prompt = (
            f"Generate {num_variants} alternative phrasings of this question. "
            f"Each variant should approach the question from a different angle.\n\n"
            f"Question: {question}\n\n"
            f"Output each variant on a separate line, numbered 1-{num_variants}."
        )
        response = self.llm.invoke(prompt)
        content = response.content if isinstance(response.content, str) else str(response.content)
        # Parse numbered lines
        variants = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if line and line[0].isdigit():
                # Remove numbering prefix
                cleaned = line.lstrip("0123456789.)-: ")
                if cleaned:
                    variants.append(cleaned)
        return variants[:num_variants]

    def _rerank(
        self, question: str, chunks: list[RetrievedChunk], top_k: int
    ) -> list[RetrievedChunk]:
        """LLM-based reranking of retrieved chunks."""
        if len(chunks) <= top_k:
            return chunks

        chunk_texts = "\n".join(
            f"[{i}] {c.content[:200]}" for i, c in enumerate(chunks)
        )
        prompt = (
            f"Given the question, rank these text passages by relevance. "
            f"Return ONLY the passage numbers in order of relevance, "
            f"separated by commas.\n\n"
            f"Question: {question}\n\n"
            f"Passages:\n{chunk_texts}\n\n"
            f"Most relevant first (numbers only):"
        )
        response = self.llm.invoke(prompt)
        content = response.content if isinstance(response.content, str) else str(response.content)

        # Parse indices from response
        import re

        indices = [int(x) for x in re.findall(r"\d+", content) if int(x) < len(chunks)]
        seen = set()
        unique_indices = []
        for idx in indices:
            if idx not in seen:
                seen.add(idx)
                unique_indices.append(idx)

        reranked = [chunks[i] for i in unique_indices[:top_k]]
        # Fill remaining slots if LLM did not return enough
        if len(reranked) < top_k:
            for chunk in chunks:
                if chunk not in reranked:
                    reranked.append(chunk)
                if len(reranked) >= top_k:
                    break

        return reranked

    def __repr__(self) -> str:
        info = self.client.get_collection(self.collection)
        return f"RAGEngine(collection='{self.collection}', chunks={info.points_count})"
