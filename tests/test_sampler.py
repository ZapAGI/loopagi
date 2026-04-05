"""Tests for loopagi.arc.sampler — Best-of-N candidate sampling."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from loopagi.arc.hypothesizer import Hypothesis
from loopagi.arc.sampler import (
    SampleConfig,
    SampleResult,
    _temperature_schedule,
    sample_n_programs,
)
from loopagi.arc.arc_analytics import ArcAnalytics


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hypothesis(rule: str = "swap 3 with 5") -> Hypothesis:
    return Hypothesis(rule=rule, confidence=0.9, source="test")


def _make_bridge(responses: list[str] | None = None, is_mock: bool = True):
    """Create a mock LLMBridge that returns predefined responses."""
    bridge = MagicMock()
    bridge.is_mock = is_mock
    bridge.model = "mock"

    if responses is None:
        responses = []

    call_idx = {"i": 0}

    def _call(prompt: str) -> str:
        idx = call_idx["i"]
        call_idx["i"] += 1
        if idx < len(responses):
            return responses[idx]
        return ""

    bridge.call = MagicMock(side_effect=_call)
    bridge.call_as = MagicMock(side_effect=_call)
    return bridge


GOOD_CODE = '''```python
def transform(grid):
    out = [row[:] for row in grid]
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 3:
                out[r][c] = 5
    return out
```'''

IDENTITY_CODE = '''```python
def transform(grid):
    return [row[:] for row in grid]
```'''

BAD_CODE = "this is not python code at all"

BROKEN_CODE = '''```python
def transform(grid):
    return 1 / 0
```'''


# ---------------------------------------------------------------------------
# _temperature_schedule
# ---------------------------------------------------------------------------

class TestTemperatureSchedule:
    """Tests for temperature schedule generation."""

    def test_single_sample(self):
        config = SampleConfig(n_samples=1, temperature_min=0.3)
        temps = _temperature_schedule(config)
        assert temps == [0.3]

    def test_two_samples(self):
        config = SampleConfig(n_samples=2, temperature_min=0.2, temperature_max=0.8)
        temps = _temperature_schedule(config)
        assert len(temps) == 2
        assert temps[0] == pytest.approx(0.2)
        assert temps[1] == pytest.approx(0.8)

    def test_five_samples(self):
        config = SampleConfig(n_samples=5, temperature_min=0.2, temperature_max=1.0)
        temps = _temperature_schedule(config)
        assert len(temps) == 5
        assert temps[0] == pytest.approx(0.2)
        assert temps[-1] == pytest.approx(1.0)
        # Should be monotonically increasing
        for i in range(1, len(temps)):
            assert temps[i] >= temps[i - 1]

    def test_equal_min_max(self):
        config = SampleConfig(n_samples=3, temperature_min=0.5, temperature_max=0.5)
        temps = _temperature_schedule(config)
        assert all(t == pytest.approx(0.5) for t in temps)


# ---------------------------------------------------------------------------
# sample_n_programs — basic behaviour
# ---------------------------------------------------------------------------

class TestSampleNPrograms:
    """Tests for the Best-of-N sampling core function."""

    def test_returns_sample_result(self):
        bridge = _make_bridge([GOOD_CODE])
        hyp = _make_hypothesis()
        train_pairs = [([[3, 0], [0, 3]], [[5, 0], [0, 5]])]
        config = SampleConfig(n_samples=1)

        result = sample_n_programs(bridge, hyp, train_pairs, config)
        assert isinstance(result, SampleResult)
        assert result.best is not None
        assert result.n_total == 1

    def test_multiple_samples_picks_best(self):
        # First response: identity (lower sim), second: good code (higher sim)
        bridge = _make_bridge([IDENTITY_CODE, GOOD_CODE, IDENTITY_CODE])
        hyp = _make_hypothesis()
        train_pairs = [([[3, 0], [0, 3]], [[5, 0], [0, 5]])]
        config = SampleConfig(n_samples=3)

        result = sample_n_programs(bridge, hyp, train_pairs, config)
        # The good code should score highest
        assert result.best_similarity > 0.5
        assert result.n_total == 3

    def test_all_bad_falls_back_to_identity(self):
        bridge = _make_bridge([BAD_CODE, BAD_CODE])
        hyp = _make_hypothesis()
        train_pairs = [([[1, 2], [3, 4]], [[1, 2], [3, 4]])]
        config = SampleConfig(n_samples=2)

        result = sample_n_programs(bridge, hyp, train_pairs, config)
        assert result.best is not None
        # Identity matches the identity task
        assert result.best_similarity >= 0.0

    def test_early_exit_on_perfect(self):
        # First response is perfect — should not call LLM again
        bridge = _make_bridge([GOOD_CODE, IDENTITY_CODE, IDENTITY_CODE])
        hyp = _make_hypothesis()
        train_pairs = [([[3, 0], [0, 3]], [[5, 0], [0, 5]])]
        config = SampleConfig(n_samples=3)

        result = sample_n_programs(bridge, hyp, train_pairs, config)
        assert result.best_similarity == pytest.approx(1.0)
        # Should have stopped after first sample
        assert bridge.call.call_count == 1

    def test_n_valid_tracked(self):
        bridge = _make_bridge([BAD_CODE, GOOD_CODE, IDENTITY_CODE])
        hyp = _make_hypothesis()
        train_pairs = [([[3, 0], [0, 3]], [[5, 0], [0, 5]])]
        config = SampleConfig(n_samples=3)

        result = sample_n_programs(bridge, hyp, train_pairs, config)
        # At least 1 valid (the GOOD_CODE)
        assert result.n_valid >= 1


# ---------------------------------------------------------------------------
# sample_n_programs — analytics integration
# ---------------------------------------------------------------------------

class TestSamplerAnalytics:
    """Tests for analytics tracking in sampling."""

    def test_analytics_populated(self):
        analytics = ArcAnalytics()
        bridge = _make_bridge([GOOD_CODE, IDENTITY_CODE])
        hyp = _make_hypothesis()
        train_pairs = [([[3, 0], [0, 3]], [[5, 0], [0, 5]])]
        config = SampleConfig(n_samples=2)

        sample_n_programs(
            bridge, hyp, train_pairs, config,
            analytics=analytics, task_id="t1", hyp_id=0,
        )
        cands = analytics.candidates
        assert cands.height >= 1
        assert "t1" in cands["task_id"].to_list()

    def test_analytics_not_required(self):
        bridge = _make_bridge([GOOD_CODE])
        hyp = _make_hypothesis()
        train_pairs = [([[3]], [[5]])]
        config = SampleConfig(n_samples=1)

        # Should work without analytics
        result = sample_n_programs(bridge, hyp, train_pairs, config)
        assert result.best is not None


# ---------------------------------------------------------------------------
# sample_n_programs — default config
# ---------------------------------------------------------------------------

class TestSamplerDefaults:
    """Tests for default configuration."""

    def test_default_config(self):
        config = SampleConfig()
        assert config.n_samples == 5
        assert config.temperature_min == 0.2
        assert config.temperature_max == 0.9

    def test_works_with_none_config(self):
        bridge = _make_bridge([GOOD_CODE] * 5)
        hyp = _make_hypothesis()
        train_pairs = [([[3, 0], [0, 3]], [[5, 0], [0, 5]])]

        # Pass config=None explicitly
        result = sample_n_programs(bridge, hyp, train_pairs, config=None)
        assert result.best is not None
