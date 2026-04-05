"""Tests for pass_at_k — multi-strategy diversified candidate voting."""

from __future__ import annotations

import pytest

from loopagi.arc.pass_at_k import (
    CandidateInfo,
    MultiVoteResult,
    _compute_agreement,
    _majority_vote,
)

# Type alias
Grid = list[list[int]]


# ---------------------------------------------------------------------------
# _majority_vote
# ---------------------------------------------------------------------------


class TestMajorityVote:
    """Tests for cell-wise majority voting."""

    def test_single_grid(self) -> None:
        g: Grid = [[1, 2], [3, 4]]
        result = _majority_vote([g])
        assert result == [[1, 2], [3, 4]]

    def test_unanimous(self) -> None:
        g: Grid = [[1, 2], [3, 4]]
        result = _majority_vote([g, g, g])
        assert result == [[1, 2], [3, 4]]

    def test_majority_wins(self) -> None:
        g1: Grid = [[1, 2], [3, 4]]
        g2: Grid = [[1, 2], [3, 4]]
        g3: Grid = [[9, 9], [9, 9]]
        result = _majority_vote([g1, g2, g3])
        assert result == [[1, 2], [3, 4]]

    def test_cell_level_voting(self) -> None:
        g1: Grid = [[1, 0], [0, 1]]
        g2: Grid = [[1, 0], [0, 0]]
        g3: Grid = [[1, 0], [0, 1]]
        result = _majority_vote([g1, g2, g3])
        # (0,0)=1, (0,1)=0, (1,0)=0, (1,1)=1 wins 2:1
        assert result == [[1, 0], [0, 1]]

    def test_empty_list(self) -> None:
        assert _majority_vote([]) is None

    def test_mixed_shapes_uses_most_common(self) -> None:
        g1: Grid = [[1, 2], [3, 4]]
        g2: Grid = [[1, 2], [3, 4]]
        g3: Grid = [[1, 2, 3]]  # Different shape
        result = _majority_vote([g1, g2, g3])
        assert result == [[1, 2], [3, 4]]

    def test_tie_breaking(self) -> None:
        g1: Grid = [[0]]
        g2: Grid = [[1]]
        # With 2 grids, Counter.most_common picks one deterministically
        result = _majority_vote([g1, g2])
        assert result is not None
        assert result[0][0] in (0, 1)

    def test_large_grid(self) -> None:
        g: Grid = [[i * 5 + j for j in range(5)] for i in range(5)]
        result = _majority_vote([g, g, g, g, g])
        assert result == g


# ---------------------------------------------------------------------------
# _compute_agreement
# ---------------------------------------------------------------------------


class TestComputeAgreement:
    """Tests for agreement computation."""

    def test_single_grid(self) -> None:
        assert _compute_agreement([[[1, 2]]]) == 1.0

    def test_identical_grids(self) -> None:
        g: Grid = [[1, 2], [3, 4]]
        assert _compute_agreement([g, g, g]) == 1.0

    def test_complete_disagreement(self) -> None:
        g1: Grid = [[0, 0]]
        g2: Grid = [[1, 1]]
        assert _compute_agreement([g1, g2]) == 0.0

    def test_partial_agreement(self) -> None:
        g1: Grid = [[1, 2], [3, 4]]
        g2: Grid = [[1, 2], [3, 9]]
        result = _compute_agreement([g1, g2])
        assert result == 0.75  # 3 out of 4 agree

    def test_mixed_shapes_filtered(self) -> None:
        g1: Grid = [[1, 2]]
        g2: Grid = [[1, 2, 3]]
        # Different shapes — matching < 2
        result = _compute_agreement([g1, g2])
        assert result == 0.0

    def test_empty_grid(self) -> None:
        assert _compute_agreement([]) == 1.0

    def test_three_grids_partial(self) -> None:
        g1: Grid = [[1, 2]]
        g2: Grid = [[1, 3]]
        g3: Grid = [[1, 2]]
        # col 0: all agree (1), col 1: 2 agree, 1 differs
        result = _compute_agreement([g1, g2, g3])
        assert result == 0.5  # Only col 0 has unanimous agreement


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class TestDataStructures:
    """Tests for pass_at_k data structures."""

    def test_candidate_info(self) -> None:
        ci = CandidateInfo(
            grid=[[1, 2]], strategy="d4_identity",
            temperature=0.0, filtered=False,
        )
        assert ci.grid == [[1, 2]]
        assert ci.strategy == "d4_identity"
        assert ci.filtered is False

    def test_multi_vote_result_defaults(self) -> None:
        result = MultiVoteResult(
            grid=None, agreement=0.0,
            n_candidates=0, n_valid=0,
        )
        assert result.method == "multi_strategy_vote"
        assert result.strategy_breakdown == {}

    def test_multi_vote_result_with_data(self) -> None:
        result = MultiVoteResult(
            grid=[[1, 2]], agreement=0.85,
            n_candidates=20, n_valid=16,
            strategy_breakdown={"d4_t0": 8, "temp_sweep": 4, "d4_retry": 8},
        )
        assert result.n_candidates == 20
        assert result.n_valid == 16
        assert result.agreement == 0.85
        assert len(result.strategy_breakdown) == 3
