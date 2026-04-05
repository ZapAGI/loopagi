"""Tests for loopagi.arc.llm_solver — extracted solve_task_with_llm."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from loopagi.arc.llm_bridge import LLMBridge, create_llm_bridge
from loopagi.arc.llm_solver import solve_task_with_llm
from loopagi.arc.sampler import SampleConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_bridge() -> LLMBridge:
    """Create a mock LLM bridge for testing."""
    return create_llm_bridge(model="mock")


def _make_task(task_id: str = "test_001"):
    """Create a minimal mock ARC task."""
    task = MagicMock()
    task.task_id = task_id

    pair = MagicMock()
    pair.input = [[1, 2], [3, 4]]
    pair.output = [[4, 3], [2, 1]]
    task.train = [pair]

    test_input = MagicMock()
    test_input.input = [[5, 6], [7, 8]]
    task.test = [test_input]

    return task


# ---------------------------------------------------------------------------
# Basic solve_task_with_llm
# ---------------------------------------------------------------------------


class TestSolveTaskWithLLM:
    """Tests for the extracted solve function."""

    def test_returns_dict_with_result(self):
        bridge = _make_mock_bridge()
        task = _make_task()
        output = solve_task_with_llm(task, bridge)
        assert "result" in output
        assert "bridge_stats" in output
        assert "complexity" in output

    def test_result_has_task_id(self):
        bridge = _make_mock_bridge()
        task = _make_task("abc123")
        output = solve_task_with_llm(task, bridge)
        assert output["result"].task_id == "abc123"

    def test_result_has_time(self):
        bridge = _make_mock_bridge()
        task = _make_task()
        output = solve_task_with_llm(task, bridge)
        assert output["result"].total_seconds >= 0.0

    def test_bridge_stats_included(self):
        bridge = _make_mock_bridge()
        task = _make_task()
        output = solve_task_with_llm(task, bridge)
        assert isinstance(output["bridge_stats"], str)

    def test_complexity_is_string(self):
        bridge = _make_mock_bridge()
        task = _make_task()
        output = solve_task_with_llm(task, bridge)
        assert isinstance(output["complexity"], str)


# ---------------------------------------------------------------------------
# Best-of-N sampling integration
# ---------------------------------------------------------------------------


class TestSolveWithSampling:
    """Tests for Best-of-N sampling wired into solve loop."""

    def test_sample_config_accepted(self):
        """solve_task_with_llm accepts sample_config without error."""
        bridge = _make_mock_bridge()
        task = _make_task()
        config = SampleConfig(n_samples=3)
        output = solve_task_with_llm(task, bridge, sample_config=config)
        assert "result" in output

    def test_none_sample_config_uses_single_synthesis(self):
        """When sample_config=None, falls back to single synthesis."""
        bridge = _make_mock_bridge()
        task = _make_task()
        output = solve_task_with_llm(task, bridge, sample_config=None)
        assert "result" in output

    def test_sample_config_with_custom_temps(self):
        """Custom temperature range is accepted."""
        bridge = _make_mock_bridge()
        task = _make_task()
        config = SampleConfig(
            n_samples=2,
            temperature_min=0.1,
            temperature_max=0.5,
        )
        output = solve_task_with_llm(task, bridge, sample_config=config)
        assert "result" in output


# ---------------------------------------------------------------------------
# Backward compatibility (re-export from llm_bridge)
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    """Verify solve_task_with_llm is still importable from llm_bridge."""

    def test_importable_from_llm_bridge(self):
        from loopagi.arc.llm_bridge import solve_task_with_llm as fn
        assert callable(fn)

    def test_same_function(self):
        from loopagi.arc.llm_bridge import solve_task_with_llm as fn1
        from loopagi.arc.llm_solver import solve_task_with_llm as fn2
        assert fn1 is fn2
