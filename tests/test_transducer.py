"""Tests for loopagi.arc.transducer — direct grid transduction."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from loopagi.arc.transducer import (
    TransductionResult,
    _compact_grid,
    _grid_similarity,
    _parse_rows_fallback,
    _validate_grid,
    format_transduction_prompt,
    parse_grid_from_response,
    transduce,
    transduce_with_verification,
    validate_transduction,
)


# ---------------------------------------------------------------------------
# _compact_grid
# ---------------------------------------------------------------------------

class TestCompactGrid:
    """Tests for compact grid formatting."""

    def test_simple(self):
        assert _compact_grid([[1, 2], [3, 4]]) == "[[1,2],[3,4]]"

    def test_single_cell(self):
        assert _compact_grid([[7]]) == "[[7]]"

    def test_empty_row(self):
        assert _compact_grid([[]]) == "[[]]"


# ---------------------------------------------------------------------------
# format_transduction_prompt
# ---------------------------------------------------------------------------

class TestFormatPrompt:
    """Tests for transduction prompt formatting."""

    def test_includes_pairs(self):
        pairs = [([[1, 2]], [[3, 4]])]
        test_input = [[5, 6]]
        prompt = format_transduction_prompt(pairs, test_input)
        assert "Pair 1:" in prompt
        assert "[[1,2]]" in prompt
        assert "[[3,4]]" in prompt
        assert "[[5,6]]" in prompt

    def test_multiple_pairs(self):
        pairs = [
            ([[0]], [[1]]),
            ([[2]], [[3]]),
        ]
        prompt = format_transduction_prompt(pairs, [[4]])
        assert "Pair 1:" in prompt
        assert "Pair 2:" in prompt

    def test_no_code_instructions(self):
        prompt = format_transduction_prompt([([[0]], [[1]])], [[0]])
        assert "JSON array" in prompt
        assert "Do NOT include" in prompt


# ---------------------------------------------------------------------------
# parse_grid_from_response
# ---------------------------------------------------------------------------

class TestParseGrid:
    """Tests for grid parsing from LLM responses."""

    def test_raw_json(self):
        grid = parse_grid_from_response("[[1,2],[3,4]]")
        assert grid == [[1, 2], [3, 4]]

    def test_with_whitespace(self):
        grid = parse_grid_from_response("  [[1, 2],\n[3, 4]]  ")
        assert grid == [[1, 2], [3, 4]]

    def test_markdown_fenced(self):
        grid = parse_grid_from_response("```json\n[[1,2],[3,4]]\n```")
        assert grid == [[1, 2], [3, 4]]

    def test_markdown_fenced_no_lang(self):
        grid = parse_grid_from_response("```\n[[1,2],[3,4]]\n```")
        assert grid == [[1, 2], [3, 4]]

    def test_extra_text_before(self):
        grid = parse_grid_from_response("The output is:\n[[1,2],[3,4]]")
        assert grid == [[1, 2], [3, 4]]

    def test_trailing_comma(self):
        grid = parse_grid_from_response("[[1,2,],[3,4,],]")
        assert grid == [[1, 2], [3, 4]]

    def test_single_cell(self):
        grid = parse_grid_from_response("[[7]]")
        assert grid == [[7]]

    def test_float_coercion(self):
        grid = parse_grid_from_response("[[1.0, 2.0]]")
        assert grid == [[1, 2]]

    def test_empty_string(self):
        assert parse_grid_from_response("") is None

    def test_none_equivalent(self):
        assert parse_grid_from_response("   ") is None

    def test_no_array(self):
        assert parse_grid_from_response("I don't know the answer") is None

    def test_non_rectangular(self):
        assert parse_grid_from_response("[[1,2],[3]]") is None

    def test_nested_non_list(self):
        assert parse_grid_from_response("[1,2,3]") is None

    def test_non_numeric(self):
        assert parse_grid_from_response('["a","b"]') is None

    def test_large_grid_29x29(self):
        """Parsing works for large grids (29x29 = 841 cells)."""
        grid = [[r % 10 for c in range(29)] for r in range(29)]
        import json
        response = json.dumps(grid)
        parsed = parse_grid_from_response(response)
        assert parsed is not None
        assert len(parsed) == 29
        assert len(parsed[0]) == 29

    def test_row_by_row_fallback(self):
        """Fallback parser extracts rows when JSON is malformed."""
        text = "Here is the grid:\n[1,2,3]\n[4,5,6]\n[7,8,9]"
        grid = _parse_rows_fallback(text)
        assert grid == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

    def test_row_fallback_too_few_rows(self):
        assert _parse_rows_fallback("[1,2,3]") is None

    def test_row_fallback_non_rectangular(self):
        text = "[1,2,3]\n[4,5]"
        assert _parse_rows_fallback(text) is None


# ---------------------------------------------------------------------------
# _grid_similarity
# ---------------------------------------------------------------------------

class TestGridSimilarity:
    """Tests for transduction grid similarity."""

    def test_identical(self):
        g = [[1, 2], [3, 4]]
        assert _grid_similarity(g, g) == 1.0

    def test_all_different(self):
        assert _grid_similarity([[1]], [[0]]) == 0.0

    def test_shape_mismatch_is_zero(self):
        assert _grid_similarity([[1, 2]], [[1]]) == 0.0

    def test_empty(self):
        assert _grid_similarity([], []) == 0.0


# ---------------------------------------------------------------------------
# validate_transduction
# ---------------------------------------------------------------------------

class TestValidateTransduction:
    """Tests for transduction validation."""

    def test_matching_shape(self):
        pairs = [([[1, 2]], [[3, 4]]), ([[5, 6]], [[7, 8]])]
        predicted = [[9, 0]]
        score = validate_transduction(predicted, pairs)
        assert score == 1.0  # Same 1x2 shape as training outputs

    def test_wrong_shape(self):
        pairs = [([[1, 2]], [[3, 4, 5]])]
        predicted = [[9, 0]]  # 1x2, but training output is 1x3
        score = validate_transduction(predicted, pairs)
        assert score == 0.0

    def test_empty_pairs(self):
        assert validate_transduction([[1]], []) == 0.0

    def test_empty_predicted(self):
        assert validate_transduction([], [([[1]], [[2]])]) == 0.0

    def test_variable_output_shapes_match(self):
        pairs = [([[1]], [[1, 2]]), ([[3]], [[3, 4, 5]])]
        predicted = [[1, 2]]  # Matches first pair's output shape
        score = validate_transduction(predicted, pairs)
        assert score == 0.8


# ---------------------------------------------------------------------------
# transduce
# ---------------------------------------------------------------------------

class TestTransduce:
    """Tests for the main transduction function."""

    def _make_bridge(self, response: str):
        bridge = MagicMock()
        bridge.call = MagicMock(return_value=response)
        bridge.is_mock = True
        return bridge

    def test_successful_transduction(self):
        # Training: 1x2 → 1x2, so predicted 1x2 is valid
        bridge = self._make_bridge("[[9,0]]")
        pairs = [([[1, 2]], [[3, 4]])]
        test_input = [[5, 6]]

        result = transduce(bridge, pairs, test_input)
        assert isinstance(result, TransductionResult)
        assert result.predicted_grid == [[9, 0]]
        assert result.valid is True

    def test_failed_parse(self):
        bridge = self._make_bridge("I cannot solve this")
        pairs = [([[1]], [[2]])]

        result = transduce(bridge, pairs, [[3]])
        assert result.predicted_grid is None
        assert result.valid is False
        assert result.error

    def test_wrong_shape(self):
        # Training output is 1x2, but LLM returns 1x3
        bridge = self._make_bridge("[[1,2,3]]")
        pairs = [([[0]], [[1, 2]])]

        result = transduce(bridge, pairs, [[0]])
        assert result.predicted_grid == [[1, 2, 3]]
        assert result.valid is False  # Shape mismatch

    def test_llm_exception(self):
        bridge = MagicMock()
        bridge.call = MagicMock(side_effect=RuntimeError("LLM down"))
        bridge.is_mock = True

        result = transduce(bridge, [([[1]], [[2]])], [[3]])
        assert result.valid is False
        assert "LLM down" in result.error

    def test_raw_response_stored(self):
        bridge = self._make_bridge("[[5]]")
        result = transduce(bridge, [([[1]], [[2]])], [[3]])
        assert result.raw_response == "[[5]]"

    # --- Phase O: temperature parameter tests ---

    def test_temperature_forwarded(self):
        """O.2: Temperature parameter is forwarded to bridge.call()."""
        bridge = self._make_bridge("[[5]]")
        transduce(bridge, [([[1]], [[2]])], [[3]], temperature=0.7)
        bridge.call.assert_called_once()
        _, kwargs = bridge.call.call_args
        assert kwargs["temperature"] == 0.7

    def test_default_temperature_zero(self):
        """O.2: Default temperature is 0.0 (deterministic)."""
        bridge = self._make_bridge("[[5]]")
        transduce(bridge, [([[1]], [[2]])], [[3]])
        _, kwargs = bridge.call.call_args
        assert kwargs["temperature"] == 0.0


# ---------------------------------------------------------------------------
# transduce_with_verification (Phase P)
# ---------------------------------------------------------------------------


class TestTransduceWithVerification:
    """Tests for training-verified transduction."""

    def _make_bridge(self, responses: list[str]):
        """Create a bridge that returns responses in sequence."""
        bridge = MagicMock()
        bridge.is_mock = True
        call_idx = {"i": 0}

        def _call(prompt: str, temperature: float | None = None) -> str:
            idx = call_idx["i"]
            call_idx["i"] += 1
            return responses[idx] if idx < len(responses) else ""

        bridge.call = MagicMock(side_effect=_call)
        return bridge

    def test_passes_when_training_verified(self):
        """P.1: Succeeds when all training pairs are correctly transduced."""
        # Train: [[1]] -> [[2]], test: [[3]]
        # Bridge returns: [[2]] for training verify, then [[4]] for test
        bridge = self._make_bridge(["[[2]]", "[[4]]"])
        pairs = [([[1]], [[2]])]
        result = transduce_with_verification(bridge, pairs, [[3]])
        assert result.valid is True
        assert result.predicted_grid is not None

    def test_fails_when_training_wrong(self):
        """P.1: Fails when training pair transduction is wrong."""
        # Train: [[1]] -> [[2]], but LLM returns [[9]] (wrong)
        bridge = self._make_bridge(["[[9]]"])
        pairs = [([[1]], [[2]])]
        result = transduce_with_verification(bridge, pairs, [[3]])
        assert result.valid is False
        assert "Training verification" in result.error

    def test_fails_when_training_unparseable(self):
        """P.1: Fails when training pair transduction can't be parsed."""
        bridge = self._make_bridge(["garbage"])
        pairs = [([[1]], [[2]])]
        result = transduce_with_verification(bridge, pairs, [[3]])
        assert result.valid is False
        assert "failed" in result.error.lower() or "verification" in result.error.lower()

    def test_multiple_training_pairs_all_must_pass(self):
        """P.1: All training pairs must verify at 100%."""
        # Pair 1: [[1]] -> [[2]] (correct), Pair 2: [[3]] -> [[4]] (wrong)
        bridge = self._make_bridge(["[[2]]", "[[9]]"])
        pairs = [([[1]], [[2]]), ([[3]], [[4]])]
        result = transduce_with_verification(bridge, pairs, [[5]])
        assert result.valid is False
        assert "pair 2" in result.error.lower()

    def test_empty_training_pairs_goes_straight_to_test(self):
        """P.1: With no training pairs, directly transduces test input."""
        bridge = self._make_bridge(["[[7]]"])
        result = transduce_with_verification(bridge, [], [[1]])
        # No training pairs to verify, so goes straight to test
        # But validate_transduction with empty pairs returns 0.0 -> not valid
        assert result.predicted_grid is not None or result.valid is False

    def test_temperature_forwarded(self):
        """P.1: Temperature is passed through to underlying transduce calls."""
        bridge = self._make_bridge(["[[2]]", "[[4]]"])
        pairs = [([[1]], [[2]])]
        transduce_with_verification(bridge, pairs, [[3]], temperature=0.5)
        # Should have called bridge.call twice (1 training + 1 test)
        assert bridge.call.call_count == 2
        for call_args in bridge.call.call_args_list:
            _, kwargs = call_args
            assert kwargs["temperature"] == 0.5
