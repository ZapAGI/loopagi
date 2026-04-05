"""Tests for loopagi.arc.grid_traversal — multi-traversal grid representations."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from loopagi.arc.grid_traversal import (
    TRAVERSAL_METHODS,
    TraversalTransductionResult,
    format_traversal_grid,
    format_traversal_prompt,
    multi_traversal_transduce,
    reconstruct,
    reconstruct_column,
    reconstruct_diagonal,
    reconstruct_row,
    reconstruct_snake,
    reconstruct_spiral,
    traverse,
    traverse_column,
    traverse_diagonal,
    traverse_row,
    traverse_snake,
    traverse_spiral,
    _parse_traversal_response,
)


# ---------------------------------------------------------------------------
# Test grids
# ---------------------------------------------------------------------------

GRID_2X3 = [[1, 2, 3], [4, 5, 6]]
GRID_3X3 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
GRID_1X1 = [[7]]
GRID_4X4 = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]


# ---------------------------------------------------------------------------
# traverse_row
# ---------------------------------------------------------------------------


class TestTraverseRow:
    def test_basic(self):
        assert traverse_row(GRID_2X3) == [1, 2, 3, 4, 5, 6]

    def test_3x3(self):
        assert traverse_row(GRID_3X3) == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    def test_1x1(self):
        assert traverse_row(GRID_1X1) == [7]

    def test_empty(self):
        assert traverse_row([]) == []


# ---------------------------------------------------------------------------
# traverse_column
# ---------------------------------------------------------------------------


class TestTraverseColumn:
    def test_basic(self):
        # Column-wise: col0=[1,4], col1=[2,5], col2=[3,6]
        assert traverse_column(GRID_2X3) == [1, 4, 2, 5, 3, 6]

    def test_3x3(self):
        # col0=[1,4,7], col1=[2,5,8], col2=[3,6,9]
        assert traverse_column(GRID_3X3) == [1, 4, 7, 2, 5, 8, 3, 6, 9]

    def test_1x1(self):
        assert traverse_column(GRID_1X1) == [7]

    def test_empty(self):
        assert traverse_column([]) == []


# ---------------------------------------------------------------------------
# traverse_snake
# ---------------------------------------------------------------------------


class TestTraverseSnake:
    def test_basic(self):
        # Row 0 (even) L->R: [1,2,3], Row 1 (odd) R->L: [6,5,4]
        assert traverse_snake(GRID_2X3) == [1, 2, 3, 6, 5, 4]

    def test_3x3(self):
        # Row 0: [1,2,3], Row 1: [6,5,4], Row 2: [7,8,9]
        assert traverse_snake(GRID_3X3) == [1, 2, 3, 6, 5, 4, 7, 8, 9]

    def test_1x1(self):
        assert traverse_snake(GRID_1X1) == [7]


# ---------------------------------------------------------------------------
# traverse_diagonal
# ---------------------------------------------------------------------------


class TestTraverseDiagonal:
    def test_basic(self):
        # d=0: (0,0)=1; d=1: (0,1)=2,(1,0)=4; d=2: (0,2)=3,(1,1)=5;
        # d=3: (1,2)=6
        assert traverse_diagonal(GRID_2X3) == [1, 2, 4, 3, 5, 6]

    def test_3x3(self):
        # d=0:[1] d=1:[2,4] d=2:[3,5,7] d=3:[6,8] d=4:[9]
        assert traverse_diagonal(GRID_3X3) == [1, 2, 4, 3, 5, 7, 6, 8, 9]

    def test_1x1(self):
        assert traverse_diagonal(GRID_1X1) == [7]

    def test_empty(self):
        assert traverse_diagonal([]) == []


# ---------------------------------------------------------------------------
# traverse_spiral
# ---------------------------------------------------------------------------


class TestTraverseSpiral:
    def test_basic(self):
        # Top: [1,2,3], Right down: [6], Bottom left: [5,4]
        assert traverse_spiral(GRID_2X3) == [1, 2, 3, 6, 5, 4]

    def test_3x3(self):
        # Top: [1,2,3], Right: [6,9], Bottom: [8,7], Left: [4], Center: [5]
        assert traverse_spiral(GRID_3X3) == [1, 2, 3, 6, 9, 8, 7, 4, 5]

    def test_4x4(self):
        expected = [1, 2, 3, 4, 8, 12, 16, 15, 14, 13, 9, 5, 6, 7, 11, 10]
        assert traverse_spiral(GRID_4X4) == expected

    def test_1x1(self):
        assert traverse_spiral(GRID_1X1) == [7]

    def test_empty(self):
        assert traverse_spiral([]) == []


# ---------------------------------------------------------------------------
# Roundtrip: traverse -> reconstruct
# ---------------------------------------------------------------------------


class TestRoundtrip:
    """Every traversal+reconstruct pair must roundtrip to the original grid."""

    @pytest.mark.parametrize("method", TRAVERSAL_METHODS)
    def test_2x3_roundtrip(self, method):
        tokens = traverse(GRID_2X3, method)
        result = reconstruct(tokens, 2, 3, method)
        assert result == GRID_2X3, f"Roundtrip failed for {method}"

    @pytest.mark.parametrize("method", TRAVERSAL_METHODS)
    def test_3x3_roundtrip(self, method):
        tokens = traverse(GRID_3X3, method)
        result = reconstruct(tokens, 3, 3, method)
        assert result == GRID_3X3, f"Roundtrip failed for {method}"

    @pytest.mark.parametrize("method", TRAVERSAL_METHODS)
    def test_4x4_roundtrip(self, method):
        tokens = traverse(GRID_4X4, method)
        result = reconstruct(tokens, 4, 4, method)
        assert result == GRID_4X4, f"Roundtrip failed for {method}"

    @pytest.mark.parametrize("method", TRAVERSAL_METHODS)
    def test_1x1_roundtrip(self, method):
        tokens = traverse(GRID_1X1, method)
        result = reconstruct(tokens, 1, 1, method)
        assert result == GRID_1X1, f"Roundtrip failed for {method}"

    @pytest.mark.parametrize("method", TRAVERSAL_METHODS)
    def test_single_row_roundtrip(self, method):
        grid = [[1, 2, 3, 4, 5]]
        tokens = traverse(grid, method)
        result = reconstruct(tokens, 1, 5, method)
        assert result == grid, f"Roundtrip failed for {method}"

    @pytest.mark.parametrize("method", TRAVERSAL_METHODS)
    def test_single_column_roundtrip(self, method):
        grid = [[1], [2], [3], [4]]
        tokens = traverse(grid, method)
        result = reconstruct(tokens, 4, 1, method)
        assert result == grid, f"Roundtrip failed for {method}"


# ---------------------------------------------------------------------------
# dispatch: traverse() / reconstruct()
# ---------------------------------------------------------------------------


class TestDispatch:
    def test_traverse_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown traversal"):
            traverse(GRID_3X3, "invalid")

    def test_reconstruct_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown traversal"):
            reconstruct([1, 2, 3, 4], 2, 2, "invalid")

    def test_reconstruct_token_count_mismatch(self):
        with pytest.raises(ValueError, match="Token count"):
            reconstruct([1, 2, 3], 2, 2, "row")

    def test_all_methods_available(self):
        assert set(TRAVERSAL_METHODS) == {"row", "column", "snake", "diagonal", "spiral"}


# ---------------------------------------------------------------------------
# format_traversal_grid
# ---------------------------------------------------------------------------


class TestFormatTraversalGrid:
    def test_row_format_is_compact_json(self):
        result = format_traversal_grid(GRID_2X3, "row")
        assert result == "[[1,2,3],[4,5,6]]"

    def test_column_format_has_prefix(self):
        result = format_traversal_grid(GRID_2X3, "column")
        assert result.startswith("[column 2x3]")
        assert "[1,4,2,5,3,6]" in result

    def test_snake_format_has_prefix(self):
        result = format_traversal_grid(GRID_2X3, "snake")
        assert result.startswith("[snake 2x3]")


# ---------------------------------------------------------------------------
# format_traversal_prompt
# ---------------------------------------------------------------------------


class TestFormatTraversalPrompt:
    def test_row_prompt_standard(self):
        pairs = [(GRID_2X3, GRID_1X1)]
        prompt = format_traversal_prompt(pairs, GRID_2X3, "row")
        assert "ARC-AGI puzzle" in prompt
        assert "JSON array of arrays" in prompt

    def test_column_prompt_has_traversal_header(self):
        pairs = [(GRID_2X3, GRID_1X1)]
        prompt = format_traversal_prompt(pairs, GRID_2X3, "column")
        assert "column traversal" in prompt
        assert "flat JSON array" in prompt

    def test_includes_all_pairs(self):
        pairs = [(GRID_2X3, GRID_1X1), (GRID_3X3, GRID_2X3)]
        prompt = format_traversal_prompt(pairs, GRID_2X3, "row")
        assert "Pair 1:" in prompt
        assert "Pair 2:" in prompt


# ---------------------------------------------------------------------------
# _parse_traversal_response
# ---------------------------------------------------------------------------


class TestParseTraversalResponse:
    def test_row_delegates_to_standard(self):
        result = _parse_traversal_response("[[1,2],[3,4]]", "row", 2, 2)
        assert result == [[1, 2], [3, 4]]

    def test_column_flat_array(self):
        # Column traversal of [[1,2],[3,4]] is [1,3,2,4]
        result = _parse_traversal_response("[1,3,2,4]", "column", 2, 2)
        assert result == [[1, 2], [3, 4]]

    def test_snake_flat_array(self):
        # Snake of [[1,2],[3,4]] is [1,2,4,3]
        result = _parse_traversal_response("[1,2,4,3]", "snake", 2, 2)
        assert result == [[1, 2], [3, 4]]

    def test_handles_prefix_echo(self):
        # LLM might echo the prefix
        result = _parse_traversal_response(
            "[column 2x2] [1,3,2,4]", "column", 2, 2
        )
        assert result == [[1, 2], [3, 4]]

    def test_handles_markdown_fences(self):
        result = _parse_traversal_response(
            "```json\n[1,3,2,4]\n```", "column", 2, 2
        )
        assert result == [[1, 2], [3, 4]]

    def test_fallback_to_grid_parser(self):
        # LLM ignores format and returns 2D array anyway
        result = _parse_traversal_response("[[1,2],[3,4]]", "column", 2, 2)
        assert result is not None

    def test_none_on_garbage(self):
        result = _parse_traversal_response("I don't know", "column", 2, 2)
        assert result is None


# ---------------------------------------------------------------------------
# TraversalTransductionResult
# ---------------------------------------------------------------------------


class TestTraversalTransductionResult:
    def test_dataclass(self):
        r = TraversalTransductionResult(
            grid=[[1]], agreement=0.9, n_valid=3, n_total=5,
        )
        assert r.grid == [[1]]
        assert r.method == "traversal_vote"
        assert r.n_valid == 3


# ---------------------------------------------------------------------------
# multi_traversal_transduce
# ---------------------------------------------------------------------------


class TestMultiTraversalTransduce:
    def test_empty_train_pairs(self):
        bridge = MagicMock()
        result = multi_traversal_transduce(bridge, [], [[1]])
        assert result.grid is None
        assert result.n_valid == 0

    def test_all_traversals_produce_same_grid(self):
        """If bridge always returns the same correct grid, voting should agree."""
        import json
        bridge = MagicMock()
        bridge.call = MagicMock(return_value=json.dumps([[5, 6], [7, 8]]))

        pairs = [([[1, 2], [3, 4]], [[5, 6], [7, 8]])]
        result = multi_traversal_transduce(
            bridge, pairs, [[1, 2], [3, 4]], methods=("row",),
        )
        assert result.n_valid >= 1
        assert result.grid is not None

    def test_subset_methods(self):
        """Can pass a subset of traversal methods."""
        import json
        bridge = MagicMock()
        bridge.call = MagicMock(return_value=json.dumps([[1]]))

        pairs = [([[0]], [[1]])]
        result = multi_traversal_transduce(
            bridge, pairs, [[0]], methods=("row", "column"),
        )
        assert result.n_total == 2


# ---------------------------------------------------------------------------
# Token length preservation
# ---------------------------------------------------------------------------


class TestTokenLength:
    """All traversals must produce exactly rows*cols tokens."""

    @pytest.mark.parametrize("method", TRAVERSAL_METHODS)
    def test_token_count_2x3(self, method):
        tokens = traverse(GRID_2X3, method)
        assert len(tokens) == 2 * 3

    @pytest.mark.parametrize("method", TRAVERSAL_METHODS)
    def test_token_count_3x3(self, method):
        tokens = traverse(GRID_3X3, method)
        assert len(tokens) == 3 * 3

    @pytest.mark.parametrize("method", TRAVERSAL_METHODS)
    def test_token_count_4x4(self, method):
        tokens = traverse(GRID_4X4, method)
        assert len(tokens) == 4 * 4

    @pytest.mark.parametrize("method", TRAVERSAL_METHODS)
    def test_all_values_preserved(self, method):
        """Traversal must visit every cell exactly once (same multiset of values)."""
        tokens = traverse(GRID_3X3, method)
        flat_original = [v for row in GRID_3X3 for v in row]
        assert sorted(tokens) == sorted(flat_original)
