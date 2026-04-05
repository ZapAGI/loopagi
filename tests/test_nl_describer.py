"""Tests for loopagi.arc.nl_describer — NL transformation description."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from loopagi.arc.nl_describer import (
    _format_pairs,
    describe_transformation,
    format_nl_context,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bridge(response: str = "The grid is rotated 90 degrees.", is_mock: bool = False):
    bridge = MagicMock()
    bridge.is_mock = is_mock
    bridge.call = MagicMock(return_value=response)
    return bridge


TRAIN_PAIRS = [
    ([[1, 2], [3, 4]], [[3, 1], [4, 2]]),
    ([[5, 6], [7, 8]], [[7, 5], [8, 6]]),
]


# ---------------------------------------------------------------------------
# _format_pairs
# ---------------------------------------------------------------------------


class TestFormatPairs:
    def test_formats_single_pair(self):
        text = _format_pairs([([[1]], [[2]])])
        assert "Pair 1:" in text
        assert "Input:" in text
        assert "Output:" in text

    def test_formats_multiple_pairs(self):
        text = _format_pairs(TRAIN_PAIRS)
        assert "Pair 1:" in text
        assert "Pair 2:" in text

    def test_respects_max_pairs(self):
        text = _format_pairs(TRAIN_PAIRS, max_pairs=1)
        assert "Pair 1:" in text
        assert "Pair 2:" not in text

    def test_empty_pairs(self):
        text = _format_pairs([])
        assert text == ""


# ---------------------------------------------------------------------------
# describe_transformation
# ---------------------------------------------------------------------------


class TestDescribeTransformation:
    def test_returns_description(self):
        bridge = _make_bridge("Each row is reversed.")
        desc = describe_transformation(bridge, TRAIN_PAIRS)
        assert "reversed" in desc
        assert bridge.call.call_count == 1

    def test_mock_bridge_returns_empty(self):
        bridge = _make_bridge(is_mock=True)
        desc = describe_transformation(bridge, TRAIN_PAIRS)
        assert desc == ""

    def test_empty_pairs_returns_empty(self):
        bridge = _make_bridge()
        desc = describe_transformation(bridge, [])
        assert desc == ""

    def test_truncates_long_description(self):
        long_text = "x" * 600
        bridge = _make_bridge(long_text)
        desc = describe_transformation(bridge, TRAIN_PAIRS)
        assert len(desc) <= 500

    def test_handles_exception(self):
        bridge = _make_bridge()
        bridge.call.side_effect = RuntimeError("LLM error")
        desc = describe_transformation(bridge, TRAIN_PAIRS)
        assert desc == ""


# ---------------------------------------------------------------------------
# format_nl_context
# ---------------------------------------------------------------------------


class TestFormatNlContext:
    def test_empty_description(self):
        assert format_nl_context("") == ""

    def test_nonempty_description(self):
        ctx = format_nl_context("Rotate 90 degrees clockwise")
        assert "Transformation description:" in ctx
        assert "Rotate 90 degrees clockwise" in ctx

    def test_preserves_content(self):
        desc = "Replace all 3s with 5s"
        ctx = format_nl_context(desc)
        assert desc in ctx
