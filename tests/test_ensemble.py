"""Tests for loopagi.arc.ensemble — ensemble scoring for candidate predictions."""

from __future__ import annotations

import pytest

from loopagi.arc.ensemble import (
    Candidate,
    EnsemblePool,
    _add_predictions,
    _grid_in_list,
    _grid_similarity,
    _grids_equal,
    _score_candidate,
    rank_candidates,
)


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

GRID_A = [[1, 2], [3, 4]]
GRID_B = [[5, 6], [7, 8]]
GRID_C = [[1, 2], [3, 9]]  # 3/4 match with GRID_A
GRID_ZERO = [[0, 0], [0, 0]]

TRAIN_PAIRS = [
    ([[0, 1], [2, 0]], [[1, 0], [0, 2]]),
    ([[0, 3], [1, 0]], [[3, 0], [0, 1]]),
]


# ---------------------------------------------------------------------------
# _grid_similarity
# ---------------------------------------------------------------------------


class TestGridSimilarity:
    def test_identical(self):
        assert _grid_similarity(GRID_A, GRID_A) == pytest.approx(1.0)

    def test_completely_different(self):
        assert _grid_similarity(GRID_A, GRID_B) == pytest.approx(0.0)

    def test_partial_match(self):
        assert _grid_similarity(GRID_A, GRID_C) == pytest.approx(0.75)

    def test_shape_mismatch(self):
        assert _grid_similarity([[1, 2]], [[1, 2], [3, 4]]) == pytest.approx(0.0)

    def test_empty(self):
        assert _grid_similarity([], []) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# _grids_equal / _grid_in_list
# ---------------------------------------------------------------------------


class TestGridEquality:
    def test_equal(self):
        assert _grids_equal(GRID_A, [[1, 2], [3, 4]])

    def test_not_equal(self):
        assert not _grids_equal(GRID_A, GRID_B)

    def test_different_size(self):
        assert not _grids_equal(GRID_A, [[1, 2]])

    def test_in_list(self):
        assert _grid_in_list(GRID_A, [GRID_B, GRID_A])

    def test_not_in_list(self):
        assert not _grid_in_list(GRID_A, [GRID_B, GRID_C])


# ---------------------------------------------------------------------------
# Candidate dataclass
# ---------------------------------------------------------------------------


class TestCandidate:
    def test_basic(self):
        c = Candidate(grid=GRID_A, source="test", score=0.5)
        assert c.source == "test"
        assert c.score == 0.5


# ---------------------------------------------------------------------------
# EnsemblePool
# ---------------------------------------------------------------------------


class TestEnsemblePool:
    def test_add_none_ignored(self):
        pool = EnsemblePool()
        pool.add(None, "test")
        assert pool.size == 0

    def test_add_empty_ignored(self):
        pool = EnsemblePool()
        pool.add([], "test")
        assert pool.size == 0

    def test_add_valid(self):
        pool = EnsemblePool()
        pool.add(GRID_A, "test")
        assert pool.size == 1

    def test_add_nested_grid_rejected(self):
        """Regression: list[Grid] must not be added as a candidate (unhashable list bug)."""
        pool = EnsemblePool()
        nested = [[[1, 2], [3, 4]]]  # list[Grid], not Grid
        pool.add(nested, "bad")
        assert pool.size == 0

    def test_add_proper_grid_accepted(self):
        pool = EnsemblePool()
        pool.add([[1, 2], [3, 4]], "good")
        assert pool.size == 1

    def test_add_many(self):
        pool = EnsemblePool()
        pool.add_many([GRID_A, GRID_B], "batch")
        assert pool.size == 2

    def test_best_empty(self):
        pool = EnsemblePool()
        assert pool.best() == []

    def test_best_returns_distinct(self):
        pool = EnsemblePool()
        pool.add(GRID_A, "src1")
        pool.add(GRID_A, "src2")  # Duplicate grid
        pool.add(GRID_B, "src3")
        result = pool.best(n=2, train_pairs=TRAIN_PAIRS, test_input=[[0, 1], [2, 0]])
        assert len(result) == 2
        # The two results should be different grids
        assert not _grids_equal(result[0].grid, result[1].grid)

    def test_best_respects_n(self):
        pool = EnsemblePool()
        pool.add(GRID_A, "src1")
        pool.add(GRID_B, "src2")
        pool.add(GRID_C, "src3")
        result = pool.best(n=1, train_pairs=TRAIN_PAIRS)
        assert len(result) == 1

    def test_best_scores_candidates(self):
        pool = EnsemblePool()
        pool.add(GRID_A, "src1")
        pool.add(GRID_B, "src2")
        result = pool.best(n=2, train_pairs=TRAIN_PAIRS, test_input=[[0, 1], [2, 0]])
        # All returned candidates should have scores > 0
        for c in result:
            assert c.score >= 0.0


# ---------------------------------------------------------------------------
# _score_candidate
# ---------------------------------------------------------------------------


class TestScoreCandidate:
    def test_empty_grid_zero(self):
        assert _score_candidate([], None, None) == pytest.approx(0.0)

    def test_no_train_pairs_partial(self):
        score = _score_candidate(GRID_A, None, None)
        assert score > 0.0  # Should get some partial credit

    def test_correct_size_scores_higher(self):
        # Training outputs are 2x2
        pairs = [([[1, 2], [3, 4]], [[5, 6], [7, 8]])]
        good = _score_candidate([[1, 2], [3, 4]], pairs, [[0, 0], [0, 0]])
        bad = _score_candidate([[1, 2, 3]], pairs, [[0, 0], [0, 0]])
        assert good > bad

    def test_correct_colors_score_higher(self):
        pairs = [([[0, 1], [2, 0]], [[1, 0], [0, 2]])]
        # Grid using only task colors
        good = _score_candidate([[0, 1], [2, 0]], pairs, [[0, 1], [2, 0]])
        # Grid using colors outside task palette
        bad = _score_candidate([[7, 8], [9, 7]], pairs, [[0, 1], [2, 0]])
        assert good > bad

    def test_nontrivial_scores_higher(self):
        pairs = [([[0, 1], [2, 0]], [[1, 0], [0, 2]])]
        diverse = _score_candidate([[1, 2], [0, 1]], pairs, [[0, 1], [2, 0]])
        uniform = _score_candidate([[0, 0], [0, 0]], pairs, [[0, 1], [2, 0]])
        assert diverse > uniform

    def test_score_capped_at_1(self):
        pairs = [([[0, 1], [2, 0]], [[1, 0], [0, 2]])]
        score = _score_candidate([[1, 0], [0, 2]], pairs, [[0, 1], [2, 0]])
        assert score <= 1.0


# ---------------------------------------------------------------------------
# rank_candidates (convenience function)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# _add_predictions (regression: unhashable list bug)
# ---------------------------------------------------------------------------


class TestAddPredictions:
    def test_flat_grids_added(self):
        """Transduction-style predictions: flat list[Grid]."""
        pool = EnsemblePool()
        preds = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]  # two Grids
        _add_predictions(pool, preds, "transduction")
        assert pool.size == 2

    def test_nested_grids_unwrapped(self):
        """Synthesis-style predictions: list[list[Grid]] (attempts per test)."""
        pool = EnsemblePool()
        preds = [[[[1, 2], [3, 4]]]]  # one test output with one attempt
        _add_predictions(pool, preds, "synthesis")
        assert pool.size == 1
        assert pool.candidates[0].grid == [[1, 2], [3, 4]]

    def test_mixed_formats(self):
        """Mixed: some flat Grids, some nested."""
        pool = EnsemblePool()
        flat_grid = [[1, 2], [3, 4]]
        nested = [[[5, 6], [7, 8]]]  # list[Grid]
        _add_predictions(pool, [flat_grid, nested], "mixed")
        assert pool.size == 2

    def test_empty_predictions_safe(self):
        pool = EnsemblePool()
        _add_predictions(pool, [], "empty")
        assert pool.size == 0

    def test_none_in_predictions_safe(self):
        pool = EnsemblePool()
        _add_predictions(pool, [None, [], [[1, 2]]], "partial")
        assert pool.size == 1

    def test_no_unhashable_error(self):
        """Regression: this must NOT raise 'unhashable type: list'."""
        pool = EnsemblePool()
        # Simulate synthesis predictions: list[list[Grid]]
        preds = [[[[0, 1], [2, 0]]], [[[3, 0], [0, 1]]]]
        _add_predictions(pool, preds, "synthesis")
        # Should not crash, and grids should be unwrapped
        assert pool.size == 2
        # Scoring should also work without error
        result = pool.best(n=1, train_pairs=TRAIN_PAIRS, test_input=[[0, 1], [2, 0]])
        assert len(result) >= 1


# ---------------------------------------------------------------------------
# rank_candidates (convenience function)
# ---------------------------------------------------------------------------


class TestRankCandidates:
    def test_basic(self):
        result = rank_candidates(
            candidates=[GRID_A, GRID_B, GRID_C],
            sources=["s1", "s2", "s3"],
            train_pairs=TRAIN_PAIRS,
            test_input=[[0, 1], [2, 0]],
            n=2,
        )
        assert len(result) <= 2
        assert all(isinstance(c, Candidate) for c in result)

    def test_empty(self):
        result = rank_candidates([], [], TRAIN_PAIRS, [[0]], n=2)
        assert result == []

    def test_sources_preserved(self):
        result = rank_candidates(
            candidates=[GRID_A],
            sources=["my_source"],
            train_pairs=TRAIN_PAIRS,
            test_input=[[0, 1], [2, 0]],
            n=1,
        )
        assert result[0].source == "my_source"
