"""
Chapter 8: Memory, Context, and the Illusion of Continuity

Persistent vector memory with Qdrant. Memory is not storage.
It is reconstruction. Both for agents and for us.

Usage:
    from loopagi.knowledge.memory import MemoryStore

    store = MemoryStore()
    store.add("The user prefers functional programming style")
    store.add("Project uses FastAPI for the backend")

    results = store.search("What framework does the project use?")
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

logger = logging.getLogger(__name__)

DEFAULT_COLLECTION = "loopagi_memory"
DEFAULT_PATH = Path.home() / ".local" / "share" / "loopagi" / "memory"


@dataclass
class Memory:
    """A single memory entry."""

    id: str
    content: str
    timestamp: float
    metadata: dict = field(default_factory=dict)
    score: float = 0.0


class MemoryStore:
    """
    Persistent vector memory backed by Qdrant.

    Memories are embedded and stored in a vector database for
    semantic search. This gives agents the ability to recall
    relevant context from past interactions, not by exact match,
    but by meaning.

    The philosophical parallel: human memory is also reconstructed,
    not replayed. We do not store recordings. We store impressions,
    and reconstruct the rest from context.
    """

    def __init__(
        self,
        collection: str = DEFAULT_COLLECTION,
        path: Path | str | None = None,
        embedding_dim: int = 384,
    ) -> None:
        self.collection = collection
        self.embedding_dim = embedding_dim
        self._path = Path(path) if path else DEFAULT_PATH
        self._path.mkdir(parents=True, exist_ok=True)

        self.client = QdrantClient(path=str(self._path))
        self._embedding_model = None
        self._ensure_collection()
        logger.info("MemoryStore initialized at %s", self._path)

    def _ensure_collection(self) -> None:
        """Create the collection if it does not exist."""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection not in collections:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created collection '%s'", self.collection)

    def _get_embedding_model(self):
        """Lazy-load the embedding model."""
        if self._embedding_model is None:
            from fastembed import TextEmbedding

            self._embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            logger.info("Loaded embedding model: BAAI/bge-small-en-v1.5")
        return self._embedding_model

    def _embed(self, text: str) -> list[float]:
        """Generate embedding vector for text."""
        model = self._get_embedding_model()
        embeddings = list(model.embed([text]))
        return embeddings[0].tolist()

    def add(self, content: str, metadata: dict | None = None) -> str:
        """
        Add a memory to the store.

        Returns the memory ID.
        """
        memory_id = str(uuid.uuid4())
        vector = self._embed(content)

        point = PointStruct(
            id=memory_id,
            vector=vector,
            payload={
                "content": content,
                "timestamp": time.time(),
                **(metadata or {}),
            },
        )
        self.client.upsert(
            collection_name=self.collection,
            points=[point],
        )
        logger.info("Stored memory: %s (%d chars)", memory_id[:8], len(content))
        return memory_id

    def search(self, query: str, limit: int = 5, min_score: float = 0.3) -> list[Memory]:
        """
        Search memories by semantic similarity.

        Returns memories ranked by relevance score.
        """
        vector = self._embed(query)
        results = self.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=limit,
            score_threshold=min_score,
        )
        memories = [
            Memory(
                id=str(hit.id),
                content=hit.payload.get("content", ""),
                timestamp=hit.payload.get("timestamp", 0.0),
                metadata={
                    k: v for k, v in hit.payload.items()
                    if k not in ("content", "timestamp")
                },
                score=hit.score,
            )
            for hit in results
        ]
        logger.info("Search '%s' returned %d results", query[:50], len(memories))
        return memories

    def get_all(self, limit: int = 100) -> list[Memory]:
        """Retrieve all memories (most recent first)."""
        result = self.client.scroll(
            collection_name=self.collection,
            limit=limit,
        )
        points = result[0] if result else []
        memories = [
            Memory(
                id=str(p.id),
                content=p.payload.get("content", ""),
                timestamp=p.payload.get("timestamp", 0.0),
                metadata={
                    k: v for k, v in p.payload.items()
                    if k not in ("content", "timestamp")
                },
            )
            for p in points
        ]
        memories.sort(key=lambda m: m.timestamp, reverse=True)
        return memories

    def delete(self, memory_id: str) -> None:
        """Delete a memory by ID."""
        self.client.delete(
            collection_name=self.collection,
            points_selector=[memory_id],
        )
        logger.info("Deleted memory: %s", memory_id[:8])

    def clear(self) -> None:
        """Delete all memories in the collection."""
        self.client.delete_collection(self.collection)
        self._ensure_collection()
        logger.info("Cleared all memories in '%s'", self.collection)

    def count(self) -> int:
        """Return the number of memories stored."""
        info = self.client.get_collection(self.collection)
        return info.points_count

    def __repr__(self) -> str:
        return f"MemoryStore(collection='{self.collection}', count={self.count()})"
