"""Tests for loopagi.arc.augmentation_voter — D4 augmentation voting."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from loopagi.arc.augmentation_voter import (
    Augmentation,
    VoteResult,
    _compute_agreement,
    _get_augmentations,
    _identity,
    _majority_vote_grid,
    try_augmented_transduction,
    vote_transduction,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bridge(predicted_grid=None, is_mock=False):
    """Create a mock bridge that returns a fixed transduction result."""
    bridge = MagicMock()
    bridge.is_mock = is_mock
    bridge.stats = MagicMock(return_value="mock stats")
    return bridge


# ---------------------------------------------------------------------------
# _identity
# ---------------------------------------------------------------------------


class TestIdentity:
    def test_copies_grid(self):
        grid = [[1, 2], [3, 4]]
        result = _identity(grid)
        assert result == grid
        assert result is not grid  # deep copy

    def test_empty_grid(self):
        assert _identity([]) == []


# ---------------------------------------------------------------------------
# _get_augmentations
# ---------------------------------------------------------------------------


class TestGetAugmentations:
    def test_returns_eight(self):
        augs = _get_augmentations()
        assert len(augs) == 8

    def test_all_have_names(self):
        augs = _get_augmentations()
        names = [a.name for a in augs]
        assert "identity" in names
        assert "rot90" in names
        assert "rot180" in names

    def test_forward_reverse_roundtrip(self):
        """Applying forward then reverse should return the original grid."""
        grid = [[1, 2, 3], [4, 5, 6]]
        for aug in _get_augmentations():
            result = aug.reverse(aug.forward(grid))
            assert result == grid, f"Roundtrip failed for {aug.name}"


# ---------------------------------------------------------------------------
# _majority_vote_grid
# ---------------------------------------------------------------------------


class TestMajorityVoteGrid:
    def test_single_grid(self):
        grid = [[1, 2], [3, 4]]
        result = _majority_vote_grid([grid])
        assert result == grid

    def test_unanimous_agreement(self):
        grid = [[1, 2], [3, 4]]
        result = _majority_vote_grid([grid, grid, grid])
        assert result == grid

    def test_majority_wins(self):
        g1 = [[1, 2], [3, 4]]
        g2 = [[1, 2], [3, 4]]
        g3 = [[9, 2], [3, 4]]  # cell (0,0) differs
        result = _majority_vote_grid([g1, g2, g3])
        assert result[0][0] == 1  # majority wins

    def test_empty_list(self):
        assert _majority_vote_grid([]) is None

    def test_mismatched_shapes_uses_majority_shape(self):
        g1 = [[1, 2], [3, 4]]
        g2 = [[1, 2], [3, 4]]
        g3 = [[1, 2, 3]]  # different shape
        result = _majority_vote_grid([g1, g2, g3])
        # Should use the 2x2 shape (majority)
        assert len(result) == 2
        assert len(result[0]) == 2


# ---------------------------------------------------------------------------
# _compute_agreement
# ---------------------------------------------------------------------------


class TestComputeAgreement:
    def test_identical_grids(self):
        grid = [[1, 2], [3, 4]]
        assert _compute_agreement([grid, grid]) == pytest.approx(1.0)

    def test_completely_different(self):
        g1 = [[1, 1], [1, 1]]
        g2 = [[2, 2], [2, 2]]
        assert _compute_agreement([g1, g2]) == pytest.approx(0.0)

    def test_partial_agreement(self):
        g1 = [[1, 2], [3, 4]]
        g2 = [[1, 2], [3, 9]]  # 3/4 cells agree
        assert _compute_agreement([g1, g2]) == pytest.approx(0.75)

    def test_single_grid(self):
        assert _compute_agreement([[[1]]]) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# VoteResult
# ---------------------------------------------------------------------------


class TestVoteResult:
    def test_dataclass(self):
        vr = VoteResult(grid=[[1]], agreement=0.9, n_valid=4, n_total=8)
        assert vr.grid == [[1]]
        assert vr.agreement == 0.9
        assert vr.method == "augmentation_vote"


# ---------------------------------------------------------------------------
# try_augmented_transduction
# ---------------------------------------------------------------------------


class TestTryAugmentedTransduction:
    def test_mock_bridge_returns_none(self):
        bridge = _make_bridge(is_mock=True)
        task = MagicMock()
        assert try_augmented_transduction(task, bridge) is None
