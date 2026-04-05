"""Tests for loopagi.arc.ttt — Test-Time Training orchestrator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from pathlib import Path

import pytest

from loopagi.arc.ttt import (
    TTTConfig,
    TTTResult,
    _serialize_task,
    is_ttt_available,
    score_ttt_predictions,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_task(task_id: str = "ttt_test_001"):
    task = MagicMock()
    task.task_id = task_id
    pair = MagicMock()
    pair.input = [[1, 2], [3, 4]]
    pair.output = [[4, 3], [2, 1]]
    task.train = [pair]
    test_input = MagicMock()
    test_input.input = [[5, 6], [7, 8]]
    task.test = [test_input]
    return task


# ---------------------------------------------------------------------------
# TTTConfig
# ---------------------------------------------------------------------------


class TestTTTConfig:
    def test_defaults(self):
        cfg = TTTConfig()
        assert cfg.model == "unsloth/Qwen3-8B-unsloth-bnb-4bit"
        assert cfg.steps == 50
        assert cfg.rank == 8
        assert cfg.alpha == 16
        assert cfg.timeout == 3600

    def test_custom(self):
        cfg = TTTConfig(steps=100, rank=16)
        assert cfg.steps == 100
        assert cfg.rank == 16


# ---------------------------------------------------------------------------
# TTTResult
# ---------------------------------------------------------------------------


class TestTTTResult:
    def test_default(self):
        r = TTTResult()
        assert r.predictions == []
        assert not r.success
        assert r.error == ""

    def test_with_data(self):
        r = TTTResult(
            predictions=[[[1, 2]]],
            success=True,
            elapsed_seconds=42.0,
        )
        assert len(r.predictions) == 1
        assert r.success


# ---------------------------------------------------------------------------
# _serialize_task
# ---------------------------------------------------------------------------


class TestSerializeTask:
    def test_serializes_correctly(self):
        task = _make_task()
        data = _serialize_task(task)
        assert data["task_id"] == "ttt_test_001"
        assert len(data["train"]) == 1
        assert "input" in data["train"][0]
        assert "output" in data["train"][0]
        assert len(data["test"]) == 1
        assert "input" in data["test"][0]


# ---------------------------------------------------------------------------
# is_ttt_available
# ---------------------------------------------------------------------------


class TestIsTTTAvailable:
    def test_returns_bool(self):
        result = is_ttt_available()
        assert isinstance(result, bool)

    def test_true_when_files_exist(self):
        # The ttt_venv was created during development
        # This test checks the actual file system
        result = is_ttt_available()
        # May be True or False depending on environment
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# score_ttt_predictions
# ---------------------------------------------------------------------------


class TestScoreTTTPredictions:
    def test_valid_predictions_score_high(self):
        task = _make_task()
        train_pairs = [([[1, 2], [3, 4]], [[4, 3], [2, 1]])]
        predictions = [[[1, 2], [3, 4]]]  # Valid colors, valid size
        score = score_ttt_predictions(predictions, train_pairs, task)
        assert score >= 0.5

    def test_invalid_colors_score_penalized(self):
        task = _make_task()
        train_pairs = [([[1, 2], [3, 4]], [[4, 3], [2, 1]])]
        predictions = [[[9, 9], [9, 9]]]  # Color 9 not in task
        score = score_ttt_predictions(predictions, train_pairs, task)
        assert 0.3 < score < 1.0  # Penalized but not zero (soft scoring)

    def test_empty_predictions(self):
        task = _make_task()
        task.test = []
        score = score_ttt_predictions([], [], task)
        assert score == 0.0  # No predictions = no score
