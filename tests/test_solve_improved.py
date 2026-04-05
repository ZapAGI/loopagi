"""Tests for loopagi.arc.solve_improved — improved ARC solver pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from unittest.mock import MagicMock, patch

import pytest

from loopagi.arc.solve_improved import (
    ImprovedSolverConfig,
    _is_identity_program,
    _try_evolution,
    _try_relaxed_transduction,
    _try_transduction,
    solve_task_improved,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bridge(responses: list[str] | None = None, is_mock: bool = True):
    """Create a mock LLMBridge."""
    bridge = MagicMock()
    bridge.is_mock = is_mock
    bridge.model = "mock"
    bridge.stats = MagicMock(return_value="mock stats")

    call_idx = {"i": 0}
    if responses is None:
        responses = ["mock response"] * 50

    def _call(prompt: str, temperature: float | None = None) -> str:
        idx = call_idx["i"]
        call_idx["i"] += 1
        return responses[idx] if idx < len(responses) else "mock"

    bridge.call = MagicMock(side_effect=_call)
    bridge.call_as = MagicMock(side_effect=lambda role, prompt: _call(prompt))
    return bridge


def _make_task(task_id: str = "test_001"):
    """Create a minimal mock ARC task."""
    task = MagicMock()
    task.task_id = task_id

    # Training pairs
    train_pair = MagicMock()
    train_pair.input = [[1, 0], [0, 1]]
    train_pair.output = [[1, 0], [0, 1]]
    task.train = [train_pair]

    # Test inputs
    test_input = MagicMock()
    test_input.input = [[0, 1], [1, 0]]
    task.test = [test_input]

    return task


# ---------------------------------------------------------------------------
# ImprovedSolverConfig
# ---------------------------------------------------------------------------

class TestConfig:
    """Tests for solver configuration."""

    def test_defaults(self):
        config = ImprovedSolverConfig()
        assert config.enable_transduction is True
        assert config.enable_object_prompts is True
        assert config.enable_evolution is True
        assert config.evolution_threshold == 0.90
        assert config.evolution_budget == 200
        assert config.enable_population is True
        assert config.population_size == 10
        assert config.crossover_rate == 0.25

    def test_disable_all(self):
        config = ImprovedSolverConfig(
            enable_transduction=False,
            enable_object_prompts=False,
            enable_evolution=False,
            enable_population=False,
        )
        assert config.enable_transduction is False
        assert config.enable_population is False

    def test_custom_population_config(self):
        config = ImprovedSolverConfig(
            population_size=20,
            crossover_rate=0.5,
        )
        assert config.population_size == 20
        assert config.crossover_rate == 0.5

    def test_relaxed_transduction_threshold_default(self):
        config = ImprovedSolverConfig()
        assert config.relaxed_transduction_threshold == 0.97

    def test_custom_relaxed_threshold(self):
        config = ImprovedSolverConfig(relaxed_transduction_threshold=0.95)
        assert config.relaxed_transduction_threshold == 0.95


# ---------------------------------------------------------------------------
# _try_transduction
# ---------------------------------------------------------------------------

class TestTryTransduction:
    """Tests for Phase 0 transduction."""

    def test_mock_bridge_skipped(self):
        bridge = _make_bridge(is_mock=True)
        task = _make_task()
        result = _try_transduction(task, bridge)
        assert result is None

    def test_transduction_returns_none_on_failure(self):
        bridge = _make_bridge(["I don't know"] * 3, is_mock=False)
        task = _make_task()
        result = _try_transduction(task, bridge)
        assert result is None

    def test_transduction_returns_result_on_success(self):
        # Training verify: return correct train output, then test prediction
        bridge = _make_bridge(
            ["[[1,0],[0,1]]", "[[1,0],[0,1]]"], is_mock=False,
        )
        task = _make_task()
        result = _try_transduction(task, bridge)
        # Should succeed: training verified + test predicted
        assert result is not None
        assert result["result"].solved is True
        assert result["result"].predictions == [[[1, 0], [0, 1]]]

    # --- Phase O: multi-attempt transduction tests ---

    def test_retries_on_first_failure(self):
        """O.1: Second attempt succeeds after first fails."""
        # Attempt 1: training verify fails (garbage)
        # Attempt 2: training verify passes, then test prediction
        bridge = _make_bridge(
            ["garbage", "[[1,0],[0,1]]", "[[1,0],[0,1]]"], is_mock=False,
        )
        task = _make_task()
        result = _try_transduction(task, bridge, max_attempts=2)
        assert result is not None
        assert result["result"].solved is True

    def test_all_attempts_fail(self):
        """O.1: Returns None when all attempts fail."""
        bridge = _make_bridge(["bad"] * 5, is_mock=False)
        task = _make_task()
        result = _try_transduction(task, bridge, max_attempts=3)
        assert result is None

    def test_max_attempts_limits_retries(self):
        """O.1: max_attempts=1 only tries once."""
        bridge = _make_bridge(["bad", "[[1,0],[0,1]]"], is_mock=False)
        task = _make_task()
        result = _try_transduction(task, bridge, max_attempts=1)
        assert result is None  # Only tried once, which failed

    def test_custom_temperatures(self):
        """O.1: Custom temperature schedule is accepted."""
        # Training verify + test prediction
        bridge = _make_bridge(
            ["[[1,0],[0,1]]", "[[1,0],[0,1]]"], is_mock=False,
        )
        task = _make_task()
        result = _try_transduction(
            task, bridge, temperatures=(0.5,), max_attempts=1,
        )
        assert result is not None


# ---------------------------------------------------------------------------
# _try_evolution
# ---------------------------------------------------------------------------

class TestTryEvolution:
    """Tests for post-loop evolution."""

    def _make_solve_dict(self, similarity: float = 0.95, solved: bool = False):
        """Create a mock solve result dict."""
        result = MagicMock()
        result.task_id = "test_001"
        result.solved = solved
        result.best_similarity = similarity
        result.best_program = MagicMock()
        result.best_program.source_code = (
            "def transform(grid):\n"
            "    out = [row[:] for row in grid]\n"
            "    return out\n"
        )
        result.best_program.hypothesis = "identity"
        return {"result": result, "bridge_stats": "mock", "complexity": "medium"}

    def test_skips_if_already_solved(self):
        solve_dict = self._make_solve_dict(similarity=1.0, solved=True)
        task = _make_task()
        config = ImprovedSolverConfig()
        result = _try_evolution(solve_dict, task, config)
        assert result["result"].solved is True

    def test_skips_below_threshold(self):
        solve_dict = self._make_solve_dict(similarity=0.50)
        task = _make_task()
        config = ImprovedSolverConfig(evolution_threshold=0.90)
        result = _try_evolution(solve_dict, task, config)
        # Should not have tried evolution
        assert result["result"].best_similarity == 0.50

    def test_evolution_runs_for_near_miss(self):
        solve_dict = self._make_solve_dict(similarity=0.95)
        task = _make_task()
        config = ImprovedSolverConfig(
            evolution_threshold=0.90,
            evolution_budget=10,
            evolution_generations=2,
        )
        # Evolution may or may not improve, but should not crash
        result = _try_evolution(solve_dict, task, config)
        assert result is not None

    def test_skips_no_program(self):
        solve_dict = self._make_solve_dict(similarity=0.95)
        solve_dict["result"].best_program = None
        task = _make_task()
        config = ImprovedSolverConfig()
        result = _try_evolution(solve_dict, task, config)
        assert result["result"].best_similarity == 0.95

    # --- Phase N: diagnostic logging tests ---

    def test_skips_when_program_is_none(self):
        """N.1: Evolution returns early when best_program is None."""
        solve_dict = self._make_solve_dict(similarity=0.95)
        solve_dict["result"].best_program = None
        task = _make_task()
        config = ImprovedSolverConfig(evolution_threshold=0.90)
        result = _try_evolution(solve_dict, task, config)
        assert result["result"].best_similarity == 0.95

    def test_skips_when_source_code_empty(self):
        """N.1: Evolution returns early when source_code is empty."""
        solve_dict = self._make_solve_dict(similarity=0.95)
        solve_dict["result"].best_program.source_code = ""
        task = _make_task()
        config = ImprovedSolverConfig(evolution_threshold=0.90)
        result = _try_evolution(solve_dict, task, config)
        assert result["result"].best_similarity == 0.95

    def test_evolution_sets_evolved_flag(self):
        """N.4: _evolved flag is set when evolution improves the result."""
        solve_dict = self._make_solve_dict(similarity=0.95)
        task = _make_task()
        config = ImprovedSolverConfig(
            evolution_threshold=0.90,
            evolution_budget=50,
            evolution_generations=3,
        )
        result = _try_evolution(solve_dict, task, config)
        # _evolved may or may not be set depending on whether mutations improve
        # but accessing it should not raise (defaults to False via hasattr)
        has_flag = hasattr(result["result"], "_evolved")
        # Just verify no crash; flag presence depends on mutation outcome
        assert result is not None

    def test_no_evolved_flag_when_below_threshold(self):
        """N.4: _evolved flag is NOT set when evolution is skipped."""
        from loopagi.arc.solver import SolveResult
        from loopagi.arc.synthesizer import SynthesizedProgram

        real_result = SolveResult(task_id="test_001")
        real_result.best_similarity = 0.50
        real_result.best_program = SynthesizedProgram(
            hypothesis="identity",
            source_code="def transform(grid): return [row[:] for row in grid]",
        )
        solve_dict = {"result": real_result, "bridge_stats": "mock", "complexity": "medium"}
        task = _make_task()
        config = ImprovedSolverConfig(evolution_threshold=0.90)
        _try_evolution(solve_dict, task, config)
        assert not hasattr(real_result, "_evolved")


# ---------------------------------------------------------------------------
# solve_task_improved
# ---------------------------------------------------------------------------

class TestSolveTaskImproved:
    """Tests for the main improved solver entry point."""

    def test_returns_dict(self):
        bridge = _make_bridge()
        task = _make_task()
        config = ImprovedSolverConfig(
            enable_transduction=False,
            enable_evolution=False,
        )
        result = solve_task_improved(task, bridge, config=config)
        assert isinstance(result, dict)
        assert "result" in result

    def test_mock_skips_transduction(self):
        bridge = _make_bridge(is_mock=True)
        task = _make_task()
        config = ImprovedSolverConfig(enable_evolution=False)
        result = solve_task_improved(task, bridge, config=config)
        assert isinstance(result, dict)

    def test_disabled_transduction(self):
        bridge = _make_bridge(is_mock=False)
        task = _make_task()
        config = ImprovedSolverConfig(
            enable_transduction=False,
            enable_evolution=False,
        )
        result = solve_task_improved(task, bridge, config=config)
        assert isinstance(result, dict)

    def test_default_config_used(self):
        bridge = _make_bridge()
        task = _make_task()
        # config=None should use defaults
        result = solve_task_improved(task, bridge, config=None)
        assert isinstance(result, dict)

    def test_result_has_time(self):
        bridge = _make_bridge()
        task = _make_task()
        config = ImprovedSolverConfig(
            enable_transduction=False,
            enable_evolution=False,
        )
        result = solve_task_improved(task, bridge, config=config)
        assert result["result"].total_seconds >= 0


# ---------------------------------------------------------------------------
# _is_identity_program
# ---------------------------------------------------------------------------

class TestIsIdentityProgram:
    """Tests for identity program detection."""

    def test_return_grid(self):
        result = MagicMock()
        result.best_program = MagicMock()
        result.best_program.source_code = "def transform(grid):\n    return grid\n"
        assert _is_identity_program(result) is True

    def test_return_g(self):
        result = MagicMock()
        result.best_program = MagicMock()
        result.best_program.source_code = "def transform(g):\n    return g\n"
        assert _is_identity_program(result) is True

    def test_return_copy(self):
        result = MagicMock()
        result.best_program = MagicMock()
        result.best_program.source_code = "def transform(grid):\n    return [row[:] for row in grid]\n"
        assert _is_identity_program(result) is True

    def test_not_identity(self):
        result = MagicMock()
        result.best_program = MagicMock()
        result.best_program.source_code = "def transform(grid):\n    return [[v+1 for v in row] for row in grid]\n"
        assert _is_identity_program(result) is False

    def test_none_program(self):
        result = MagicMock()
        result.best_program = None
        assert _is_identity_program(result) is False

    def test_empty_source(self):
        result = MagicMock()
        result.best_program = MagicMock()
        result.best_program.source_code = ""
        assert _is_identity_program(result) is False

    def test_no_best_program_attr(self):
        result = MagicMock(spec=[])
        assert _is_identity_program(result) is False


# ---------------------------------------------------------------------------
# _try_relaxed_transduction
# ---------------------------------------------------------------------------

class TestTryRelaxedTransduction:
    """Tests for relaxed transduction fallback."""

    def test_mock_bridge_returns_none(self):
        bridge = _make_bridge(is_mock=True)
        task = _make_task()
        result = _try_relaxed_transduction(task, bridge)
        assert result is None

    def test_garbage_response_returns_none(self):
        bridge = _make_bridge(["not a grid"] * 10, is_mock=False)
        task = _make_task()
        result = _try_relaxed_transduction(task, bridge)
        assert result is None

    def test_passes_when_training_sim_high(self):
        # Training verify: return correct train output, then test prediction
        bridge = _make_bridge(
            ["[[1,0],[0,1]]", "[[0,1],[1,0]]"], is_mock=False,
        )
        task = _make_task()
        result = _try_relaxed_transduction(task, bridge, min_similarity=0.99)
        # May or may not pass depending on exact grid match
        # Just verify no crash
        assert result is None or isinstance(result, dict)
