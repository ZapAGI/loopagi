"""Tests for chapter-22/run_eval_improved.py -- retry-from and task selection."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure chapter-21 scripts are importable
sys.path.insert(0, str(Path(__file__).parent.parent / "chapter-21"))

from run_eval_improved import load_completed_tasks, load_retry_tasks


# ---------------------------------------------------------------------------
# load_retry_tasks
# ---------------------------------------------------------------------------


class TestLoadRetryTasks:
    """Tests for the retry-from feature."""

    def test_filters_unsolved_above_threshold(self, tmp_path):
        data = {
            "task_results": [
                {"task_id": "a", "solved": True, "similarity": 1.0},
                {"task_id": "b", "solved": False, "similarity": 0.95},
                {"task_id": "c", "solved": False, "similarity": 0.50},
                {"task_id": "d", "solved": False, "similarity": 0.80},
            ]
        }
        p = tmp_path / "prev.json"
        p.write_text(json.dumps(data))

        result = load_retry_tasks(str(p), min_similarity=0.80)
        assert "a" not in result  # solved
        assert "c" not in result  # below threshold
        assert "b" in result
        assert "d" in result

    def test_sorted_by_similarity_descending(self, tmp_path):
        data = {
            "task_results": [
                {"task_id": "low", "solved": False, "similarity": 0.80},
                {"task_id": "high", "solved": False, "similarity": 0.98},
                {"task_id": "mid", "solved": False, "similarity": 0.90},
            ]
        }
        p = tmp_path / "prev.json"
        p.write_text(json.dumps(data))

        result = load_retry_tasks(str(p), min_similarity=0.80)
        assert result == ["high", "mid", "low"]

    def test_empty_results(self, tmp_path):
        data = {"task_results": []}
        p = tmp_path / "prev.json"
        p.write_text(json.dumps(data))

        result = load_retry_tasks(str(p))
        assert result == []

    def test_missing_file(self, tmp_path):
        result = load_retry_tasks(str(tmp_path / "nonexistent.json"))
        assert result == []

    def test_all_solved(self, tmp_path):
        data = {
            "task_results": [
                {"task_id": "a", "solved": True, "similarity": 1.0},
                {"task_id": "b", "solved": True, "similarity": 1.0},
            ]
        }
        p = tmp_path / "prev.json"
        p.write_text(json.dumps(data))

        result = load_retry_tasks(str(p), min_similarity=0.80)
        assert result == []

    def test_custom_threshold(self, tmp_path):
        data = {
            "task_results": [
                {"task_id": "a", "solved": False, "similarity": 0.89},
                {"task_id": "b", "solved": False, "similarity": 0.90},
            ]
        }
        p = tmp_path / "prev.json"
        p.write_text(json.dumps(data))

        result = load_retry_tasks(str(p), min_similarity=0.90)
        assert result == ["b"]


# ---------------------------------------------------------------------------
# load_completed_tasks
# ---------------------------------------------------------------------------


class TestLoadCompletedTasks:
    """Tests for JSONL resume loading."""

    def test_loads_task_ids(self, tmp_path):
        p = tmp_path / "results.jsonl"
        p.write_text(
            '{"task_id": "a", "solved": true}\n'
            '{"task_id": "b", "solved": false}\n'
        )
        result = load_completed_tasks(str(p))
        assert result == {"a", "b"}

    def test_missing_file(self, tmp_path):
        result = load_completed_tasks(str(tmp_path / "none.jsonl"))
        assert result == set()

    def test_handles_malformed_lines(self, tmp_path):
        p = tmp_path / "results.jsonl"
        p.write_text(
            '{"task_id": "a"}\n'
            'BAD LINE\n'
            '{"task_id": "c"}\n'
        )
        result = load_completed_tasks(str(p))
        assert "a" in result
        assert "c" in result
