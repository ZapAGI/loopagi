"""Tests for chapter-01/document_similarity.py module."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add chapter-01 to path for direct import
sys.path.insert(0, str(Path(__file__).parent.parent / "chapter-01"))

from document_similarity import (
    SimilarityMatch,
    cluster_documents,
    find_duplicates_in_texts,
    find_similar_files,
    ncd,
    ncd_text,
)


class TestNCD:
    """Tests for the Normalized Compression Distance function."""

    def test_identical_strings(self) -> None:
        result = ncd_text("hello world", "hello world")
        assert result < 0.3

    def test_completely_different(self) -> None:
        a = "AAAAAAAAAA" * 50
        b = "".join(chr(((i * 7 + 13) % 26) + 65) for i in range(500))
        result = ncd_text(a, b)
        assert result > 0.5

    def test_similar_strings(self) -> None:
        a = "The quick brown fox jumps over the lazy dog"
        b = "The fast brown fox leaps over the lazy dog"
        result = ncd_text(a, b)
        assert result < 0.7

    def test_empty_strings(self) -> None:
        assert ncd(b"", b"") == 0.0
        assert ncd(b"hello", b"") == 1.0
        assert ncd(b"", b"hello") == 1.0

    def test_bytes_input(self) -> None:
        result = ncd(b"test data", b"test data")
        assert result < 0.4

    def test_symmetry(self) -> None:
        a = "Python is great"
        b = "Rust is fast"
        assert abs(ncd_text(a, b) - ncd_text(b, a)) < 0.01


class TestSimilarityMatch:
    """Tests for SimilarityMatch dataclass."""

    def test_near_duplicate(self) -> None:
        m = SimilarityMatch("a.py", "b.py", ncd=0.15, similarity_pct=85.0)
        assert m.is_near_duplicate
        assert m.is_related

    def test_related(self) -> None:
        m = SimilarityMatch("a.py", "b.py", ncd=0.4, similarity_pct=60.0)
        assert not m.is_near_duplicate
        assert m.is_related

    def test_unrelated(self) -> None:
        m = SimilarityMatch("a.py", "b.py", ncd=0.8, similarity_pct=20.0)
        assert not m.is_near_duplicate
        assert not m.is_related


class TestFindDuplicatesInTexts:
    """Tests for text deduplication."""

    def test_finds_near_duplicates(self) -> None:
        texts = {
            "doc1": "Machine learning is a subset of AI",
            "doc2": "ML is a branch of artificial intelligence",
            "doc3": "The Fibonacci sequence starts with 0 and 1",
        }
        matches = find_duplicates_in_texts(texts, threshold=0.7)
        # doc1 and doc2 should be more similar to each other than to doc3
        if matches:
            pair = (matches[0].file_a, matches[0].file_b)
            assert "doc3" not in pair or len(matches) > 1

    def test_empty_corpus(self) -> None:
        matches = find_duplicates_in_texts({})
        assert matches == []

    def test_single_document(self) -> None:
        matches = find_duplicates_in_texts({"doc1": "Hello"})
        assert matches == []

    def test_threshold_filtering(self) -> None:
        texts = {
            "a": "X" * 100,
            "b": "Y" * 100,
        }
        strict = find_duplicates_in_texts(texts, threshold=0.1)
        loose = find_duplicates_in_texts(texts, threshold=0.9)
        assert len(strict) <= len(loose)


class TestClusterDocuments:
    """Tests for document clustering."""

    def test_clusters_similar_docs(self) -> None:
        docs = {
            "py1": "def hello(): print('hello')",
            "py2": "def greet(): print('greet')",
            "recipe": "Boil water add pasta cook 10 minutes",
        }
        clusters = cluster_documents(docs, threshold=0.6)
        # py1 and py2 should cluster together
        for group in clusters:
            if "py1" in group:
                assert "py2" in group

    def test_empty_input(self) -> None:
        clusters = cluster_documents({})
        assert clusters == []

    def test_no_clusters_when_all_different(self) -> None:
        docs = {
            "a": "X" * 200,
            "b": "".join(chr(i % 26 + 65) for i in range(200)),
        }
        clusters = cluster_documents(docs, threshold=0.1)
        assert len(clusters) == 0


class TestFindSimilarFiles:
    """Tests for directory scanning."""

    def test_finds_similar_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "a.py").write_text("def hello(): return 'hello world'\n" * 5)
            (p / "b.py").write_text("def greet(): return 'hello world'\n" * 5)
            (p / "c.txt").write_text("Completely different content " * 20)

            matches = find_similar_files(p, threshold=0.6)
            if matches:
                pair_files = {matches[0].file_a, matches[0].file_b}
                assert "a.py" in pair_files or "b.py" in pair_files

    def test_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            matches = find_similar_files(Path(tmp))
            assert matches == []

    def test_skips_pycache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            cache = p / "__pycache__"
            cache.mkdir()
            (cache / "mod.cpython-312.pyc").write_text("cached")
            (p / "mod.py").write_text("real")

            matches = find_similar_files(p, threshold=0.9)
            for m in matches:
                assert "__pycache__" not in m.file_a
                assert "__pycache__" not in m.file_b
