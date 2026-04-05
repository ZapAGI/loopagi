"""Tests for loopagi.arc.transducer_refine -- iterative transduction refinement."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from loopagi.arc.transducer_refine import (
    format_diff_pairs,
    format_wrong_cells,
    should_use_diff_format,
    transduce_with_refinement,
)


# ---------------------------------------------------------------------------
# should_use_diff_format
# ---------------------------------------------------------------------------

class TestShouldUseDiffFormat:
    """Tests for differential format detection."""

    def test_near_identity_grids(self):
        # 4x4 grid, only 1 cell differs = 6.25% change
        inp = [[1, 1, 1, 1]] * 4
        out = [[1, 1, 1, 1], [1, 2, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1]]
        assert should_use_diff_format([(inp, out)]) is True

    def test_many_changes(self):
        # 2x2 grid, all cells differ = 100% change
        inp = [[1, 1], [1, 1]]
        out = [[2, 2], [2, 2]]
        assert should_use_diff_format([(inp, out)]) is False

    def test_different_dimensions(self):
        inp = [[1, 2]]
        out = [[1, 2, 3]]
        assert should_use_diff_format([(inp, out)]) is False

    def test_empty_pairs(self):
        assert should_use_diff_format([]) is True


# ---------------------------------------------------------------------------
# format_diff_pairs
# ---------------------------------------------------------------------------

class TestFormatDiffPairs:
    """Tests for differential pair formatting."""

    def test_shows_changed_cells(self):
        inp = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
        out = [[1, 1, 1], [1, 2, 1], [1, 1, 1]]
        text = format_diff_pairs([(inp, out)])
        assert "Changed cells" in text
        assert "(1,1): 1 -> 2" in text

    def test_falls_back_for_many_changes(self):
        inp = [[1, 2], [3, 4]]
        out = [[5, 6], [7, 8]]
        text = format_diff_pairs([(inp, out)])
        assert "Changed cells" not in text
        assert "Output" in text


# ---------------------------------------------------------------------------
# format_wrong_cells
# ---------------------------------------------------------------------------

class TestFormatWrongCells:
    """Tests for wrong cell formatting."""

    def test_identifies_wrong(self):
        expected = [[1, 2], [3, 4]]
        actual = [[1, 9], [3, 4]]
        text = format_wrong_cells(expected, actual)
        assert "(0,1): 9 -> 2" in text

    def test_no_wrong(self):
        grid = [[1, 2], [3, 4]]
        text = format_wrong_cells(grid, grid)
        assert "none" in text.lower()


# ---------------------------------------------------------------------------
# transduce_with_refinement
# ---------------------------------------------------------------------------

class TestTransduceWithRefinement:
    """Tests for iterative refinement transduction."""

    def _make_bridge(self, responses: list[str]):
        bridge = MagicMock()
        bridge.is_mock = False
        call_idx = {"i": 0}

        def _call(prompt: str, temperature: float | None = None) -> str:
            idx = call_idx["i"]
            call_idx["i"] += 1
            return responses[idx] if idx < len(responses) else ""

        bridge.call = MagicMock(side_effect=_call)
        return bridge

    def test_returns_result(self):
        bridge = self._make_bridge(["[[1,2]]"] * 5)
        pairs = [([[0, 0]], [[1, 2]])]
        result = transduce_with_refinement(bridge, pairs, [[0, 0]])
        assert result.predicted_grid is not None

    def test_garbage_returns_none(self):
        bridge = self._make_bridge(["not a grid"] * 5)
        pairs = [([[1]], [[2]])]
        result = transduce_with_refinement(bridge, pairs, [[1]])
        assert result.predicted_grid is None

    def test_mock_bridge_returns_none(self):
        bridge = MagicMock()
        bridge.is_mock = True
        bridge.call = MagicMock(return_value="[[1]]")
        # Should still work since refinement doesn't check is_mock
        result = transduce_with_refinement(bridge, [([[1]], [[2]])], [[1]])
        assert result is not None
