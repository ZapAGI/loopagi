"""Tests for loopagi.arc.fitness -- normalized fitness scoring."""

from __future__ import annotations

import pytest

from loopagi.arc.fitness import (
    is_identity_code,
    normalized_fitness,
    outputs_differ,
    simplicity_score,
)


# ---------------------------------------------------------------------------
# is_identity_code
# ---------------------------------------------------------------------------

class TestIsIdentityCode:
    """Tests for static identity detection."""

    def test_return_grid(self):
        assert is_identity_code("def transform(grid):\n    return grid\n") is True

    def test_return_g(self):
        assert is_identity_code("def transform(g):\n    return g\n") is True

    def test_return_copy(self):
        code = "def transform(grid):\n    return [row[:] for row in grid]\n"
        assert is_identity_code(code) is True

    def test_not_identity(self):
        code = "def transform(grid):\n    return [[v+1 for v in row] for row in grid]\n"
        assert is_identity_code(code) is False

    def test_empty(self):
        assert is_identity_code("") is False


# ---------------------------------------------------------------------------
# normalized_fitness
# ---------------------------------------------------------------------------

class TestNormalizedFitness:
    """Tests for Imbue-style normalized fitness."""

    def test_identity_scores_low(self):
        code = "def transform(grid):\n    return grid\n"
        score = normalized_fitness(0.97, code=code)
        assert score == pytest.approx(0.2)

    def test_perfect_scores_high(self):
        code = "def transform(grid):\n    return [[v+1 for v in row] for row in grid]\n"
        score = normalized_fitness(1.0, code=code)
        assert score > 0.95

    def test_zero_similarity_above_identity(self):
        code = "def transform(grid):\n    return [[0]]\n"
        score = normalized_fitness(0.0, code=code)
        # Non-identity at 0% should score ~0.2 (same as identity base)
        assert score >= 0.19

    def test_partial_similarity_beats_identity(self):
        code = "def transform(grid):\n    return [[v+1 for v in row] for row in grid]\n"
        score = normalized_fitness(0.5, code=code)
        identity_score = normalized_fitness(0.97, code="def transform(g): return g")
        assert score > identity_score

    def test_no_code_uses_raw_similarity(self):
        score = normalized_fitness(0.8)
        assert 0.5 < score < 0.9

    def test_simplicity_weight(self):
        simple = "def transform(g):\n    return [[v+1 for v in r] for r in g]\n"
        complex_code = "def transform(g):\n" + "".join(
            f"    x{i} = {i}\n" for i in range(20)
        ) + "    return g\n"
        s_simple = normalized_fitness(0.8, code=simple, simplicity_weight=0.1)
        s_complex = normalized_fitness(0.8, code=complex_code, simplicity_weight=0.1)
        assert s_simple > s_complex


# ---------------------------------------------------------------------------
# simplicity_score
# ---------------------------------------------------------------------------

class TestSimplicityScore:
    """Tests for code simplicity scoring."""

    def test_simple_code(self):
        code = "def transform(grid):\n    return [[v+1 for v in row] for row in grid]\n"
        score = simplicity_score(code)
        assert score > 0.5

    def test_complex_code_lower(self):
        code = "def transform(grid):\n"
        for i in range(20):
            code += f"    x{i} = {i}\n"
        code += "    return grid\n"
        score = simplicity_score(code)
        assert score < 0.5

    def test_many_color_constants(self):
        code = "def transform(g):\n    return [[0 if v==1 else 2 if v==3 else 4 if v==5 else 6 if v==7 else 8 if v==9 else v for v in r] for r in g]\n"
        score = simplicity_score(code)
        assert score < 0.7

    def test_empty_code(self):
        assert simplicity_score("") == 0.5

    def test_syntax_error_fallback(self):
        score = simplicity_score("def broken(:\n    123 456")
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# outputs_differ
# ---------------------------------------------------------------------------

class TestOutputsDiffer:
    """Tests for output diversity checking."""

    def test_same_outputs(self):
        code_a = "def transform(g): return g"
        code_b = "def transform(g): return [row[:] for row in g]"
        pairs = [([[1, 2]], [[3, 4]])]
        assert outputs_differ(code_a, code_b, pairs) is False

    def test_different_outputs(self):
        code_a = "def transform(g): return g"
        code_b = "def transform(g): return [[v+1 for v in r] for r in g]"
        pairs = [([[1, 2]], [[3, 4]])]
        assert outputs_differ(code_a, code_b, pairs) is True

    def test_error_counts_as_different(self):
        code_a = "def transform(g): return g"
        code_b = "def transform(g): return 1/0"
        pairs = [([[1]], [[2]])]
        assert outputs_differ(code_a, code_b, pairs) is True

    def test_empty_pairs(self):
        assert outputs_differ("a", "b", []) is True
