"""Tests for loopagi.arc.solution_store -- cross-task solution transfer."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from loopagi.arc.solution_store import (
    SolutionExample,
    SolutionStore,
    StoredSolution,
)


class TestStoredSolution:
    """Tests for the StoredSolution dataclass."""

    def test_creation(self):
        sol = StoredSolution(task_id="t1", code="def transform(g): return g", similarity=1.0)
        assert sol.task_id == "t1"
        assert sol.method == ""


class TestSolutionStore:
    """Tests for the SolutionStore class."""

    def test_empty(self):
        store = SolutionStore()
        assert len(store) == 0
        assert "empty" in store.summary()

    def test_add_and_get(self):
        store = SolutionStore()
        store.add("t1", "def transform(g): return g", 1.0, method="transduced")
        assert len(store) == 1
        assert store.has("t1")
        sol = store.get("t1")
        assert sol is not None
        assert sol.code == "def transform(g): return g"

    def test_rejects_low_similarity(self):
        store = SolutionStore()
        store.add("t1", "code", 0.5)  # Below 0.9 threshold
        assert len(store) == 0

    def test_rejects_empty_code(self):
        store = SolutionStore()
        store.add("t1", "", 1.0)
        assert len(store) == 0

    def test_has_missing(self):
        store = SolutionStore()
        assert store.has("nonexistent") is False

    def test_get_missing(self):
        store = SolutionStore()
        assert store.get("nonexistent") is None

    def test_summary(self):
        store = SolutionStore()
        store.add("t1", "code1", 1.0, method="transduced")
        store.add("t2", "code2", 0.95, method="evolved")
        s = store.summary()
        assert "2 solutions" in s
        assert "transduced" in s

    def test_save_and_load(self):
        store = SolutionStore()
        store.add("t1", "def transform(g): return g", 1.0, method="transduced")
        store.add("t2", "def transform(g): return [[0]]", 0.95, method="evolved")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        store.save(path)
        assert Path(path).exists()

        store2 = SolutionStore()
        store2.load(path)
        assert len(store2) == 2
        assert store2.has("t1")
        assert store2.get("t2").method == "evolved"

        Path(path).unlink()

    def test_load_nonexistent(self):
        store = SolutionStore()
        store.load("/tmp/nonexistent_solution_store.json")
        assert len(store) == 0


class TestFormatForSynthesis:
    """Tests for formatting solutions into prompts."""

    def test_empty_examples(self):
        store = SolutionStore()
        assert store.format_for_synthesis([]) == ""

    def test_with_examples(self):
        store = SolutionStore()
        examples = [
            SolutionExample(task_id="t1", code="def transform(g): return g", relevance=0.9),
        ]
        text = store.format_for_synthesis(examples)
        assert "similar" in text.lower()
        assert "def transform" in text

    def test_multiple_examples(self):
        store = SolutionStore()
        examples = [
            SolutionExample(task_id="t1", code="code1", relevance=0.9),
            SolutionExample(task_id="t2", code="code2", relevance=0.8),
        ]
        text = store.format_for_synthesis(examples)
        assert "code1" in text
        assert "code2" in text
