"""Tests for loopagi.arc.cell_fixer -- targeted cell-fix refinement."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from loopagi.arc.cell_fixer import (
    CellFixResult,
    WrongCell,
    fix_cells,
    format_cell_fix_prompt,
    format_wrong_cells_text,
    identify_wrong_cells,
)


# ---------------------------------------------------------------------------
# identify_wrong_cells
# ---------------------------------------------------------------------------


class TestIdentifyWrongCells:
    """Tests for wrong cell identification."""

    def test_identical_grids(self):
        grid = [[1, 2], [3, 4]]
        assert identify_wrong_cells(grid, grid) == []

    def test_single_wrong_cell(self):
        expected = [[1, 2], [3, 4]]
        actual = [[1, 2], [3, 9]]
        wrong = identify_wrong_cells(expected, actual)
        assert len(wrong) == 1
        assert wrong[0].row == 1
        assert wrong[0].col == 1
        assert wrong[0].expected == 4
        assert wrong[0].actual == 9

    def test_multiple_wrong_cells(self):
        expected = [[1, 2], [3, 4]]
        actual = [[0, 2], [3, 0]]
        wrong = identify_wrong_cells(expected, actual)
        assert len(wrong) == 2

    def test_all_wrong(self):
        expected = [[1, 2], [3, 4]]
        actual = [[5, 6], [7, 8]]
        wrong = identify_wrong_cells(expected, actual)
        assert len(wrong) == 4

    def test_shape_mismatch_rows(self):
        expected = [[1, 2], [3, 4]]
        actual = [[1, 2]]
        assert identify_wrong_cells(expected, actual) == []

    def test_shape_mismatch_cols(self):
        expected = [[1, 2]]
        actual = [[1, 2, 3]]
        assert identify_wrong_cells(expected, actual) == []

    def test_empty_grids(self):
        assert identify_wrong_cells([], []) == []

    def test_empty_expected(self):
        assert identify_wrong_cells([], [[1]]) == []


# ---------------------------------------------------------------------------
# format_wrong_cells_text
# ---------------------------------------------------------------------------


class TestFormatWrongCellsText:
    """Tests for wrong cells text formatting."""

    def test_no_wrong_cells(self):
        assert format_wrong_cells_text([]) == "No wrong cells."

    def test_single_wrong_cell(self):
        wrong = [WrongCell(row=1, col=2, expected=5, actual=3)]
        text = format_wrong_cells_text(wrong)
        assert "1 wrong cell" in text
        assert "(1,2)" in text
        assert "got 3" in text
        assert "expected 5" in text

    def test_multiple_wrong_cells(self):
        wrong = [
            WrongCell(row=0, col=0, expected=1, actual=0),
            WrongCell(row=1, col=1, expected=4, actual=9),
        ]
        text = format_wrong_cells_text(wrong)
        assert "2 wrong cell" in text


# ---------------------------------------------------------------------------
# format_cell_fix_prompt
# ---------------------------------------------------------------------------


class TestFormatCellFixPrompt:
    """Tests for cell-fix prompt formatting."""

    def test_includes_training_pairs(self):
        pairs = [([[1]], [[2]])]
        wrong = [WrongCell(row=0, col=0, expected=2, actual=9)]
        prompt = format_cell_fix_prompt(
            pairs, "def transform(g): return g",
            wrong, [[9]], [[2]],
        )
        assert "Pair 1:" in prompt
        assert "[[1]]" in prompt
        assert "[[2]]" in prompt

    def test_includes_wrong_cells(self):
        pairs = [([[1]], [[2]])]
        wrong = [WrongCell(row=0, col=0, expected=2, actual=9)]
        prompt = format_cell_fix_prompt(
            pairs, "def transform(g): return g",
            wrong, [[9]], [[2]],
        )
        assert "wrong cell" in prompt
        assert "(0,0)" in prompt

    def test_includes_current_code(self):
        code = "def transform(grid): return grid"
        prompt = format_cell_fix_prompt(
            [([[1]], [[2]])],
            code,
            [WrongCell(row=0, col=0, expected=2, actual=1)],
            [[1]], [[2]],
        )
        assert code in prompt

    def test_includes_grids(self):
        prompt = format_cell_fix_prompt(
            [([[1]], [[2]])],
            "def transform(g): return g",
            [WrongCell(row=0, col=0, expected=2, actual=1)],
            [[1]], [[2]],
        )
        assert "Current output:" in prompt
        assert "Expected output:" in prompt


# ---------------------------------------------------------------------------
# fix_cells
# ---------------------------------------------------------------------------


class TestFixCells:
    """Tests for the main fix_cells function."""

    def _make_bridge(self, response: str):
        bridge = MagicMock()
        bridge.call = MagicMock(return_value=response)
        bridge.is_mock = False
        return bridge

    def _make_task(self):
        task = MagicMock()
        task.task_id = "test_fix_001"
        return task

    def _make_program(self, code: str = "def transform(grid): return grid"):
        from loopagi.arc.synthesizer import SynthesizedProgram
        return SynthesizedProgram(
            hypothesis="identity", source_code=code, is_valid=True,
        )

    def test_no_source_code(self):
        bridge = self._make_bridge("")
        task = self._make_task()
        prog = self._make_program(code="")
        result = fix_cells(bridge, task, prog, [([[1]], [[2]])])
        assert result.similarity == 0.0
        assert "No source code" in result.error

    def test_perfect_program_no_fix(self):
        """Program already correct on training pairs returns no improvement."""
        bridge = self._make_bridge("")
        task = self._make_task()
        # Identity program with identity training pair
        prog = self._make_program("def transform(grid): return [row[:] for row in grid]")
        result = fix_cells(bridge, task, prog, [([[1, 2]], [[1, 2]])])
        # No wrong cells found
        assert result.similarity == 1.0

    def test_fix_attempt_with_valid_response(self):
        """LLM returns valid fix code."""
        bridge = self._make_bridge(
            "```python\ndef transform(grid):\n    return [[v + 1 for v in row] for row in grid]\n```"
        )
        task = self._make_task()
        # Program returns identity but expected is +1
        prog = self._make_program("def transform(grid): return [row[:] for row in grid]")
        pairs = [([[1, 2]], [[2, 3]])]
        result = fix_cells(bridge, task, prog, pairs)
        assert result.method == "code_fix"
        # The fixed code should correctly add 1
        assert result.similarity == 1.0

    def test_fix_attempt_with_garbage_response(self):
        """LLM returns garbage, no code extracted."""
        bridge = self._make_bridge("I can't fix this")
        task = self._make_task()
        prog = self._make_program("def transform(grid): return [row[:] for row in grid]")
        pairs = [([[1]], [[2]])]
        result = fix_cells(bridge, task, prog, pairs)
        assert "No code" in result.error

    def test_result_dataclass(self):
        result = CellFixResult(fixed_grid=[[1]], similarity=0.95, method="code_fix")
        assert result.fixed_grid == [[1]]
        assert result.similarity == 0.95
        assert result.method == "code_fix"
        assert result.error == ""
