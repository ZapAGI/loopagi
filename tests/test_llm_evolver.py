"""Tests for loopagi.arc.llm_evolver -- LLM-guided code evolution."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from loopagi.arc.llm_evolver import (
    LLMEvolutionResult,
    _build_worst_diff,
    _grid_similarity,
    _verify_code,
    format_diff_visualization,
    llm_evolve,
    llm_mutate,
)


# ---------------------------------------------------------------------------
# format_diff_visualization
# ---------------------------------------------------------------------------


class TestFormatDiffVisualization:
    """Tests for differential cell visualization."""

    def test_identical_grids(self):
        grid = [[1, 2], [3, 4]]
        text = format_diff_visualization(grid, grid)
        assert "X" not in text
        assert "1 2" in text
        assert "3 4" in text

    def test_single_wrong_cell(self):
        expected = [[1, 2], [3, 4]]
        actual = [[1, 2], [3, 9]]
        text = format_diff_visualization(expected, actual)
        assert "X9->4" in text
        assert "1 2" in text

    def test_all_wrong(self):
        expected = [[1, 2]]
        actual = [[5, 6]]
        text = format_diff_visualization(expected, actual)
        assert "X5->1" in text
        assert "X6->2" in text

    def test_shape_mismatch(self):
        text = format_diff_visualization([[1, 2]], [[1]])
        assert "Shape mismatch" in text

    def test_empty_grids(self):
        text = format_diff_visualization([], [])
        assert "empty" in text.lower()


# ---------------------------------------------------------------------------
# _grid_similarity
# ---------------------------------------------------------------------------


class TestGridSimilarity:
    """Tests for grid similarity in llm_evolver."""

    def test_identical(self):
        assert _grid_similarity([[1, 2]], [[1, 2]]) == 1.0

    def test_all_different(self):
        assert _grid_similarity([[1]], [[0]]) == 0.0

    def test_half_correct(self):
        assert _grid_similarity([[1, 2]], [[1, 9]]) == 0.5

    def test_shape_mismatch(self):
        assert _grid_similarity([[1, 2]], [[1]]) == 0.0

    def test_empty(self):
        assert _grid_similarity([], []) == 0.0


# ---------------------------------------------------------------------------
# _verify_code
# ---------------------------------------------------------------------------


class TestVerifyCode:
    """Tests for code verification."""

    def test_valid_code(self):
        code = "def transform(grid): return [[v + 1 for v in row] for row in grid]"
        sim, outputs = _verify_code(code, [([[1, 2]], [[2, 3]])])
        assert sim == 1.0
        assert outputs == [[[2, 3]]]

    def test_wrong_result(self):
        code = "def transform(grid): return grid"
        sim, outputs = _verify_code(code, [([[1]], [[2]])])
        assert sim == 0.0
        assert outputs == [[[1]]]

    def test_syntax_error(self):
        sim, outputs = _verify_code("def broken(:", [([[1]], [[2]])])
        assert sim == 0.0
        assert outputs == []

    def test_runtime_error(self):
        code = "def transform(grid): return 1/0"
        sim, outputs = _verify_code(code, [([[1]], [[2]])])
        assert sim == 0.0
        assert outputs == []

    def test_no_transform(self):
        code = "def other(grid): return grid"
        sim, outputs = _verify_code(code, [([[1]], [[2]])])
        assert sim == 0.0
        assert outputs == []


# ---------------------------------------------------------------------------
# _build_worst_diff
# ---------------------------------------------------------------------------


class TestBuildWorstDiff:
    """Tests for worst-diff builder."""

    def test_picks_worst_pair(self):
        pairs = [([[1]], [[1]]), ([[1]], [[2]])]
        # First output is correct, second is wrong
        outputs = [[[1]], [[1]]]
        diff = _build_worst_diff(pairs, outputs)
        # Second pair has sim=0.0, should be picked
        assert "X" in diff

    def test_empty_outputs(self):
        diff = _build_worst_diff([([[1]], [[2]])], [])
        assert "no outputs" in diff.lower()

    def test_empty_pairs(self):
        diff = _build_worst_diff([], [])
        assert "no outputs" in diff.lower()


# ---------------------------------------------------------------------------
# llm_mutate
# ---------------------------------------------------------------------------


class TestLLMMutate:
    """Tests for LLM-guided mutation."""

    def _make_bridge(self, response: str):
        bridge = MagicMock()
        bridge.call = MagicMock(return_value=response)
        bridge.is_mock = False
        return bridge

    def test_valid_mutation(self):
        code = "```python\ndef transform(grid):\n    return [[v + 1 for v in row] for row in grid]\n```"
        bridge = self._make_bridge(code)
        result = llm_mutate(
            bridge, "def transform(g): return g",
            [([[1]], [[2]])], 0.5, "X1->2",
        )
        assert result is not None
        assert "def transform" in result

    def test_garbage_response(self):
        bridge = self._make_bridge("I can't fix this")
        result = llm_mutate(
            bridge, "def transform(g): return g",
            [([[1]], [[2]])], 0.5, "X1->2",
        )
        assert result is None

    def test_syntax_error_in_response(self):
        code = "```python\ndef transform(grid:\n    return grid\n```"
        bridge = self._make_bridge(code)
        result = llm_mutate(
            bridge, "def transform(g): return g",
            [([[1]], [[2]])], 0.5, "X1->2",
        )
        assert result is None

    def test_incremental_strength(self):
        code = "```python\ndef transform(grid):\n    return grid\n```"
        bridge = self._make_bridge(code)
        llm_mutate(
            bridge, "def transform(g): return g",
            [([[1]], [[2]])], 0.5, "X1->2",
            strength="incremental",
        )
        prompt = bridge.call.call_args[0][0]
        assert "small" in prompt.lower() or "targeted" in prompt.lower()

    def test_radical_strength(self):
        code = "```python\ndef transform(grid):\n    return grid\n```"
        bridge = self._make_bridge(code)
        llm_mutate(
            bridge, "def transform(g): return g",
            [([[1]], [[2]])], 0.5, "X1->2",
            strength="radical",
        )
        prompt = bridge.call.call_args[0][0]
        assert "reconsider" in prompt.lower() or "entirely" in prompt.lower()


# ---------------------------------------------------------------------------
# llm_evolve
# ---------------------------------------------------------------------------


class TestLLMEvolve:
    """Tests for the LLM evolution loop."""

    def _make_bridge(self, responses: list[str]):
        bridge = MagicMock()
        bridge.is_mock = False
        call_idx = {"i": 0}

        def _call(prompt: str, temperature: float | None = None) -> str:
            idx = call_idx["i"]
            call_idx["i"] += 1
            return responses[idx] if idx < len(responses) else ""

        bridge.call = MagicMock(side_effect=_call)
        return bridge

    def _make_task(self):
        task = MagicMock()
        task.task_id = "test_evo_001"
        return task

    def test_solves_on_first_gen(self):
        """LLM provides correct fix on first attempt."""
        fix_code = "```python\ndef transform(grid):\n    return [[v + 1 for v in row] for row in grid]\n```"
        bridge = self._make_bridge([fix_code])
        task = self._make_task()
        pairs = [([[1, 2]], [[2, 3]])]
        seed = "def transform(grid): return grid"

        result = llm_evolve(bridge, task, seed, pairs, max_generations=3, candidates_per_gen=1)
        assert result.solved is True
        assert result.best_similarity == 1.0

    def test_no_improvement(self):
        """LLM returns garbage every time, no improvement."""
        bridge = self._make_bridge(["garbage"] * 10)
        task = self._make_task()
        pairs = [([[1]], [[2]])]
        seed = "def transform(grid): return grid"

        result = llm_evolve(bridge, task, seed, pairs, max_generations=2, candidates_per_gen=2)
        assert result.solved is False
        assert result.best_similarity == 0.0

    def test_result_dataclass(self):
        r = LLMEvolutionResult(
            best_code="x", best_similarity=0.5,
            generations=2, total_mutations=4, solved=False,
        )
        assert r.best_code == "x"
        assert r.generations == 2
        assert r.history == []

    def test_history_populated(self):
        """History entries are created for each generation."""
        bridge = self._make_bridge(["garbage"] * 10)
        task = self._make_task()
        pairs = [([[1]], [[2]])]
        seed = "def transform(grid): return grid"

        result = llm_evolve(bridge, task, seed, pairs, max_generations=1, candidates_per_gen=2)
        assert len(result.history) == 1
        assert result.history[0]["generation"] == 0

    def test_population_mode_solves(self):
        """Population mode solves on first gen via mutation."""
        fix_code = (
            "```python\ndef transform(grid):\n"
            "    return [[v + 1 for v in row] for row in grid]\n```"
        )
        bridge = self._make_bridge([fix_code])
        task = self._make_task()
        pairs = [([[1, 2]], [[2, 3]])]
        seed = "def transform(grid): return grid"

        result = llm_evolve(
            bridge, task, seed, pairs,
            max_generations=3, candidates_per_gen=1,
            use_population=True, population_size=5,
        )
        assert result.solved is True
        assert result.best_similarity == 1.0

    def test_population_mode_no_improvement(self):
        """Population mode with garbage responses still terminates."""
        bridge = self._make_bridge(["garbage"] * 20)
        task = self._make_task()
        pairs = [([[1]], [[2]])]
        seed = "def transform(grid): return grid"

        result = llm_evolve(
            bridge, task, seed, pairs,
            max_generations=2, candidates_per_gen=2,
            use_population=True,
        )
        assert result.solved is False
        # Identity seed gets normalized fitness of 0.2 (Imbue-style)
        assert result.best_similarity <= 0.2

    def test_population_history_includes_summary(self):
        """History entries include population summary in population mode."""
        bridge = self._make_bridge(["garbage"] * 10)
        task = self._make_task()
        pairs = [([[1]], [[2]])]
        seed = "def transform(grid): return grid"

        result = llm_evolve(
            bridge, task, seed, pairs,
            max_generations=1, candidates_per_gen=1,
            use_population=True,
        )
        assert len(result.history) == 1
        assert result.history[0]["population"] is not None
        assert "Population" in result.history[0]["population"]

    def test_no_population_history_is_none(self):
        """History entries have population=None when population mode is off."""
        bridge = self._make_bridge(["garbage"] * 10)
        task = self._make_task()
        pairs = [([[1]], [[2]])]
        seed = "def transform(grid): return grid"

        result = llm_evolve(
            bridge, task, seed, pairs,
            max_generations=1, candidates_per_gen=1,
            use_population=False,
        )
        assert len(result.history) == 1
        assert result.history[0]["population"] is None

    def test_crossover_integration(self):
        """Population mode with enough organisms can attempt crossover."""
        # Provide enough responses for gen 0 mutations + gen 1 crossover attempt
        valid = "```python\ndef transform(grid):\n    return grid\n```"
        bridge = self._make_bridge([valid] * 20)
        task = self._make_task()
        pairs = [([[1]], [[1]])]  # identity, so valid code gets sim=1.0
        seed = "def transform(grid): return grid"

        # Gen 0: 3 mutation candidates fill population
        # Gen 1: crossover may be attempted (25% chance, but pop may have 3+)
        result = llm_evolve(
            bridge, task, seed, pairs,
            max_generations=3, candidates_per_gen=3,
            use_population=True, population_size=10, crossover_rate=1.0,
        )
        # Should solve via mutation since identity transform matches
        assert result.solved is True
