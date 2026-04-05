"""Tests for loopagi.arc.nl_evolver — NL instruction evolution."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from loopagi.arc.nl_evolver import (
    NLCandidate,
    NLEvolutionResult,
    _compact_grid,
    _grid_similarity,
    _parse_grid,
    apply_instruction_to_test,
    generate_instructions,
    nl_evolve,
    pool_instructions,
    revise_instruction,
    score_instruction,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TRAIN_PAIRS = [
    ([[1, 2], [3, 4]], [[2, 1], [4, 3]]),
]


def _make_bridge(responses: list[str] | None = None, is_mock: bool = False):
    bridge = MagicMock()
    bridge.is_mock = is_mock
    bridge.model = "mock"
    bridge.stats = MagicMock(return_value="mock stats")

    if responses is None:
        responses = ["Reverse each row"]

    idx = {"i": 0}

    def _call(prompt: str, temperature: float | None = None) -> str:
        i = idx["i"]
        idx["i"] += 1
        return responses[i % len(responses)] if responses else ""

    bridge.call = MagicMock(side_effect=_call)
    return bridge


def _make_task(task_id: str = "nl_test_001"):
    task = MagicMock()
    task.task_id = task_id
    pair = MagicMock()
    pair.input = [[1, 2], [3, 4]]
    pair.output = [[2, 1], [4, 3]]
    task.train = [pair]
    test_input = MagicMock()
    test_input.input = [[5, 6], [7, 8]]
    task.test = [test_input]
    return task


# ---------------------------------------------------------------------------
# _compact_grid
# ---------------------------------------------------------------------------


class TestCompactGrid:
    def test_simple(self):
        assert _compact_grid([[1, 2], [3, 4]]) == "[[1,2],[3,4]]"

    def test_single_cell(self):
        assert _compact_grid([[5]]) == "[[5]]"

    def test_single_row(self):
        assert _compact_grid([[1, 2, 3]]) == "[[1,2,3]]"


# ---------------------------------------------------------------------------
# _parse_grid
# ---------------------------------------------------------------------------


class TestParseGrid:
    def test_valid_json(self):
        assert _parse_grid("[[1,2],[3,4]]") == [[1, 2], [3, 4]]

    def test_with_surrounding_text(self):
        result = _parse_grid("Here is the grid: [[1,2],[3,4]] done.")
        assert result == [[1, 2], [3, 4]]

    def test_invalid_json(self):
        assert _parse_grid("not a grid at all") is None

    def test_flat_array(self):
        assert _parse_grid("[1,2,3]") is None

    def test_empty_response(self):
        assert _parse_grid("") is None


# ---------------------------------------------------------------------------
# _grid_similarity
# ---------------------------------------------------------------------------


class TestGridSimilarity:
    def test_identical(self):
        g = [[1, 2], [3, 4]]
        assert _grid_similarity(g, g) == pytest.approx(1.0)

    def test_all_different(self):
        assert _grid_similarity([[1]], [[2]]) == pytest.approx(0.0)

    def test_partial(self):
        g1 = [[1, 2], [3, 4]]
        g2 = [[1, 2], [3, 9]]
        assert _grid_similarity(g1, g2) == pytest.approx(0.75)

    def test_shape_mismatch(self):
        assert _grid_similarity([[1, 2]], [[1]]) == pytest.approx(0.0)

    def test_empty(self):
        assert _grid_similarity([], []) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# NLCandidate
# ---------------------------------------------------------------------------


class TestNLCandidate:
    def test_defaults(self):
        c = NLCandidate(instruction="Reverse rows")
        assert c.similarity == 0.0
        assert c.generation == 0
        assert c.source == "initial"


# ---------------------------------------------------------------------------
# NLEvolutionResult
# ---------------------------------------------------------------------------


class TestNLEvolutionResult:
    def test_dataclass(self):
        r = NLEvolutionResult(
            best_instruction="Reverse rows",
            best_similarity=0.95,
            predictions=[[[1]]],
            total_candidates=10,
            generations=3,
            solved=False,
        )
        assert r.best_instruction == "Reverse rows"
        assert r.total_candidates == 10
        assert not r.solved


# ---------------------------------------------------------------------------
# generate_instructions
# ---------------------------------------------------------------------------


class TestGenerateInstructions:
    def test_generates_n(self):
        bridge = _make_bridge(["Swap columns", "Reverse rows", "Rotate grid"])
        cands = generate_instructions(bridge, TRAIN_PAIRS, n=3)
        assert len(cands) == 3
        assert all(c.source == "initial" for c in cands)

    def test_empty_on_failure(self):
        bridge = _make_bridge([])
        bridge.call.side_effect = RuntimeError("fail")
        cands = generate_instructions(bridge, TRAIN_PAIRS, n=2)
        assert cands == []

    def test_truncates_long_instructions(self):
        bridge = _make_bridge(["x" * 600])
        cands = generate_instructions(bridge, TRAIN_PAIRS, n=1)
        assert len(cands) == 1
        assert len(cands[0].instruction) <= 500


# ---------------------------------------------------------------------------
# score_instruction
# ---------------------------------------------------------------------------


class TestScoreInstruction:
    def test_perfect_score(self):
        # Bridge returns the exact expected grid
        bridge = _make_bridge(["[[2,1],[4,3]]"])
        sim, errors = score_instruction(bridge, "Reverse each row", TRAIN_PAIRS)
        assert sim == pytest.approx(1.0)
        assert errors == []

    def test_wrong_answer(self):
        bridge = _make_bridge(["[[9,9],[9,9]]"])
        sim, errors = score_instruction(bridge, "Bad instruction", TRAIN_PAIRS)
        assert sim < 1.0
        assert len(errors) >= 1

    def test_unparseable_response(self):
        bridge = _make_bridge(["I don't know"])
        sim, errors = score_instruction(bridge, "Test", TRAIN_PAIRS)
        assert "could not parse" in errors[0]


# ---------------------------------------------------------------------------
# revise_instruction
# ---------------------------------------------------------------------------


class TestReviseInstruction:
    def test_produces_revision(self):
        bridge = _make_bridge(["Improved: reverse each row left-to-right"])
        rev = revise_instruction(bridge, "Reverse rows", ["Pair 1: 75%"], generation=1)
        assert rev is not None
        assert rev.source == "revised"
        assert rev.generation == 1

    def test_empty_errors_returns_none(self):
        bridge = _make_bridge(["Improved instruction"])
        rev = revise_instruction(bridge, "Reverse rows", [], generation=1)
        assert rev is None

    def test_empty_response_returns_none(self):
        bridge = _make_bridge([""])
        rev = revise_instruction(bridge, "Reverse rows", ["error"], generation=1)
        assert rev is None


# ---------------------------------------------------------------------------
# pool_instructions
# ---------------------------------------------------------------------------


class TestPoolInstructions:
    def test_pools_multiple(self):
        bridge = _make_bridge(["Combined: reverse each row and swap colors"])
        cands = [
            NLCandidate(instruction="Reverse rows", similarity=0.8),
            NLCandidate(instruction="Swap colors", similarity=0.7),
        ]
        pooled = pool_instructions(bridge, cands, generation=2)
        assert pooled is not None
        assert pooled.source == "pooled"
        assert pooled.generation == 2

    def test_single_candidate_returns_none(self):
        bridge = _make_bridge()
        pooled = pool_instructions(bridge, [NLCandidate(instruction="x")], generation=1)
        assert pooled is None


# ---------------------------------------------------------------------------
# apply_instruction_to_test
# ---------------------------------------------------------------------------


class TestApplyInstructionToTest:
    def test_returns_grid(self):
        bridge = _make_bridge(["[[6,5],[8,7]]"])
        result = apply_instruction_to_test(bridge, "Reverse each row", [[5, 6], [7, 8]])
        assert result == [[6, 5], [8, 7]]

    def test_unparseable_returns_none(self):
        bridge = _make_bridge(["I can't do this"])
        result = apply_instruction_to_test(bridge, "Test", [[1]])
        assert result is None


# ---------------------------------------------------------------------------
# nl_evolve (integration)
# ---------------------------------------------------------------------------


class TestNLEvolve:
    def test_mock_bridge_returns_empty(self):
        bridge = _make_bridge(is_mock=True)
        task = _make_task()
        result = nl_evolve(bridge, task, TRAIN_PAIRS)
        assert result.best_similarity == 0.0
        assert result.predictions == []
        assert not result.solved

    def test_returns_result(self):
        # Bridge returns correct grid for scoring + test prediction
        bridge = _make_bridge(["Reverse each row", "[[2,1],[4,3]]", "[[6,5],[8,7]]"])
        task = _make_task()
        result = nl_evolve(bridge, task, TRAIN_PAIRS, initial_candidates=1, top_k=1)
        assert isinstance(result, NLEvolutionResult)
        assert result.total_candidates >= 1
        assert result.generations >= 1

    def test_result_has_predictions(self):
        bridge = _make_bridge(["Reverse each row", "[[2,1],[4,3]]"])
        task = _make_task()
        result = nl_evolve(bridge, task, TRAIN_PAIRS, initial_candidates=1, top_k=1)
        assert len(result.predictions) == len(task.test)
