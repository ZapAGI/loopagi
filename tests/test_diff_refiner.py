"""Tests for diff_refiner — diff-based iterative refinement."""

from __future__ import annotations

import pytest

from loopagi.arc.diff_refiner import (
    DiffCell,
    GridDiff,
    RefineResult,
    compute_grid_diff,
    format_ascii_diff,
    format_wrong_cells_summary,
)

# Type alias
Grid = list[list[int]]


# ---------------------------------------------------------------------------
# compute_grid_diff
# ---------------------------------------------------------------------------


class TestComputeGridDiff:
    """Tests for compute_grid_diff."""

    def test_identical_grids(self) -> None:
        g: Grid = [[1, 2], [3, 4]]
        diff = compute_grid_diff(g, g)
        assert diff.n_wrong == 0
        assert diff.similarity == 1.0
        assert diff.total_cells == 4

    def test_one_wrong_cell(self) -> None:
        expected: Grid = [[1, 2], [3, 4]]
        actual: Grid = [[1, 2], [3, 9]]
        diff = compute_grid_diff(expected, actual)
        assert diff.n_wrong == 1
        assert diff.total_cells == 4
        assert diff.similarity == 0.75
        assert diff.wrong_cells[0].row == 1
        assert diff.wrong_cells[0].col == 1
        assert diff.wrong_cells[0].expected == 4
        assert diff.wrong_cells[0].actual == 9

    def test_all_wrong(self) -> None:
        expected: Grid = [[0, 0], [0, 0]]
        actual: Grid = [[1, 1], [1, 1]]
        diff = compute_grid_diff(expected, actual)
        assert diff.n_wrong == 4
        assert diff.similarity == 0.0

    def test_empty_grids(self) -> None:
        diff = compute_grid_diff([], [])
        assert diff.n_wrong == 0
        assert diff.total_cells == 0

    def test_shape_mismatch_rows(self) -> None:
        diff = compute_grid_diff([[1, 2]], [[1, 2], [3, 4]])
        assert diff.n_wrong == 0
        assert diff.total_cells == 0

    def test_shape_mismatch_cols(self) -> None:
        diff = compute_grid_diff([[1, 2]], [[1, 2, 3]])
        assert diff.n_wrong == 0
        assert diff.total_cells == 0

    def test_single_cell_grid(self) -> None:
        diff = compute_grid_diff([[5]], [[5]])
        assert diff.n_wrong == 0
        assert diff.similarity == 1.0
        assert diff.total_cells == 1

    def test_single_cell_wrong(self) -> None:
        diff = compute_grid_diff([[5]], [[3]])
        assert diff.n_wrong == 1
        assert diff.similarity == 0.0

    def test_large_grid(self) -> None:
        expected: Grid = [[i * 10 + j for j in range(10)] for i in range(10)]
        actual: Grid = [[i * 10 + j for j in range(10)] for i in range(10)]
        actual[5][5] = 999
        diff = compute_grid_diff(expected, actual)
        assert diff.n_wrong == 1
        assert diff.total_cells == 100
        assert diff.similarity == 0.99

    def test_n_correct_property(self) -> None:
        diff = compute_grid_diff([[1, 2], [3, 4]], [[1, 9], [3, 4]])
        assert diff.n_correct == 3
        assert diff.n_wrong == 1


# ---------------------------------------------------------------------------
# format_ascii_diff
# ---------------------------------------------------------------------------


class TestFormatAsciiDiff:
    """Tests for format_ascii_diff."""

    def test_identical_grids(self) -> None:
        g: Grid = [[1, 2], [3, 4]]
        result = format_ascii_diff(g, g)
        assert "X" not in result
        assert "." in result

    def test_one_wrong_cell(self) -> None:
        expected: Grid = [[1, 2], [3, 4]]
        actual: Grid = [[1, 2], [3, 9]]
        result = format_ascii_diff(expected, actual)
        assert "X" in result
        assert "got 9" in result
        assert "expected 4" in result

    def test_empty_grids(self) -> None:
        result = format_ascii_diff([], [])
        assert "empty" in result.lower()

    def test_shape_mismatch(self) -> None:
        result = format_ascii_diff([[1]], [[1, 2]])
        assert "mismatch" in result.lower()

    def test_row_mismatch(self) -> None:
        result = format_ascii_diff([[1], [2]], [[1]])
        assert "mismatch" in result.lower()

    def test_multiple_wrong_in_row(self) -> None:
        expected: Grid = [[0, 0, 0]]
        actual: Grid = [[1, 0, 2]]
        result = format_ascii_diff(expected, actual)
        lines = result.strip().split("\n")
        assert len(lines) == 1
        assert lines[0].count("X") == 2


# ---------------------------------------------------------------------------
# format_wrong_cells_summary
# ---------------------------------------------------------------------------


class TestFormatWrongCellsSummary:
    """Tests for format_wrong_cells_summary."""

    def test_no_wrong_cells(self) -> None:
        diff = GridDiff(wrong_cells=[], total_cells=4, similarity=1.0)
        result = format_wrong_cells_summary(diff)
        assert "correct" in result.lower()

    def test_some_wrong_cells(self) -> None:
        diff = GridDiff(
            wrong_cells=[DiffCell(0, 1, 5, 3), DiffCell(1, 0, 2, 7)],
            total_cells=4,
            similarity=0.5,
        )
        result = format_wrong_cells_summary(diff)
        assert "2 wrong" in result
        assert "row 0, col 1" in result
        assert "row 1, col 0" in result

    def test_truncation_at_20(self) -> None:
        cells = [DiffCell(r, 0, 0, 1) for r in range(25)]
        diff = GridDiff(wrong_cells=cells, total_cells=25, similarity=0.0)
        result = format_wrong_cells_summary(diff)
        assert "... and 5 more" in result


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class TestDataStructures:
    """Tests for diff_refiner data structures."""

    def test_diff_cell(self) -> None:
        cell = DiffCell(row=2, col=3, expected=5, actual=7)
        assert cell.row == 2
        assert cell.col == 3
        assert cell.expected == 5
        assert cell.actual == 7

    def test_grid_diff_defaults(self) -> None:
        diff = GridDiff()
        assert diff.n_wrong == 0
        assert diff.total_cells == 0
        assert diff.similarity == 0.0

    def test_refine_result(self) -> None:
        result = RefineResult(
            grid=[[1, 2]], similarity=0.9,
            rounds_used=2, improved=True,
        )
        assert result.grid == [[1, 2]]
        assert result.method == "diff_refine"
        assert result.improved is True
