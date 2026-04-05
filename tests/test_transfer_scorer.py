"""Tests for loopagi.arc.transfer_scorer -- transfer score evaluation."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from loopagi.arc.transfer_scorer import (
    _parse_score,
    compute_transfer_score,
)


# ---------------------------------------------------------------------------
# _parse_score
# ---------------------------------------------------------------------------

class TestParseScore:
    """Tests for score parsing from LLM response."""

    def test_single_digit(self):
        assert _parse_score("7") == 0.7

    def test_number_with_text(self):
        assert _parse_score("I would rate this a 6 out of 10") == 0.6

    def test_ten(self):
        assert _parse_score("10") == 1.0

    def test_zero(self):
        assert _parse_score("0") == 0.0

    def test_float(self):
        assert _parse_score("7.5") == 0.75

    def test_no_number(self):
        assert _parse_score("I cannot rate this") == 0.5

    def test_empty(self):
        assert _parse_score("") == 0.5

    def test_clamped_high(self):
        assert _parse_score("15") == 1.0


# ---------------------------------------------------------------------------
# compute_transfer_score
# ---------------------------------------------------------------------------

class TestComputeTransferScore:
    """Tests for full transfer score computation."""

    def _make_task(self):
        task = MagicMock()
        train_pair = MagicMock()
        train_pair.input = [[1, 2], [3, 4]]
        train_pair.output = [[5, 6], [7, 8]]
        task.train = [train_pair]
        test_input = MagicMock()
        test_input.input = [[0, 1], [2, 3]]
        task.test = [test_input]
        return task

    def test_mock_bridge_returns_default(self):
        bridge = MagicMock()
        bridge.is_mock = True
        task = self._make_task()
        score = compute_transfer_score(bridge, "def transform(g): return g", task)
        assert score == 0.5

    def test_empty_code_returns_default(self):
        bridge = MagicMock()
        bridge.is_mock = False
        task = self._make_task()
        score = compute_transfer_score(bridge, "", task)
        assert score == 0.5

    def test_llm_returns_score(self):
        bridge = MagicMock()
        bridge.is_mock = False
        bridge.call = MagicMock(return_value="8")
        task = self._make_task()
        score = compute_transfer_score(bridge, "def transform(g): return g", task)
        assert score == 0.8

    def test_llm_exception_returns_default(self):
        bridge = MagicMock()
        bridge.is_mock = False
        bridge.call = MagicMock(side_effect=RuntimeError("fail"))
        task = self._make_task()
        score = compute_transfer_score(bridge, "def transform(g): return g", task)
        assert score == 0.5
