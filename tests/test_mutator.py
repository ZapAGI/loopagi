"""Tests for loopagi.arc.mutator — program mutation / evolution engine."""

from __future__ import annotations

import pytest

from loopagi.arc.evolver import (
    EvolutionConfig,
    EvolutionResult,
    _grid_similarity,
    _verify_mutant,
    evolve_program,
)
from loopagi.arc.mutator import (
    Mutation,
    _find_integer_literals,
    generate_mutations,
    mutate_bounds,
    mutate_constants,
    mutate_negations,
    mutate_operators,
)


# ---------------------------------------------------------------------------
# Helper programs
# ---------------------------------------------------------------------------

SIMPLE_TRANSFORM = """\
def transform(grid):
    out = [row[:] for row in grid]
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 3:
                out[r][c] = 5
    return out
"""

IDENTITY_TRANSFORM = """\
def transform(grid):
    return [row[:] for row in grid]
"""

OFF_BY_ONE = """\
def transform(grid):
    rows = len(grid)
    cols = len(grid[0])
    out = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols - 1):
            out[r][c] = grid[r][c]
    return out
"""

COMPARISON_PROGRAM = """\
def transform(grid):
    out = [row[:] for row in grid]
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] > 5:
                out[r][c] = 1
    return out
"""

NEGATE_PROGRAM = """\
def transform(grid):
    out = [row[:] for row in grid]
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 0:
                out[r][c] = 1
    return out
"""


# ---------------------------------------------------------------------------
# _find_integer_literals
# ---------------------------------------------------------------------------

class TestFindIntegerLiterals:
    """Tests for AST integer literal finder."""

    def test_finds_small_integers(self):
        lits = _find_integer_literals("x = 3\ny = 5")
        vals = [v for _, _, v in lits]
        assert 3 in vals
        assert 5 in vals

    def test_skips_large_integers(self):
        lits = _find_integer_literals("x = 100")
        vals = [v for _, _, v in lits]
        assert 100 not in vals

    def test_skips_booleans(self):
        lits = _find_integer_literals("x = True\ny = False")
        assert len(lits) == 0

    def test_syntax_error_returns_empty(self):
        lits = _find_integer_literals("def broken(")
        assert lits == []

    def test_finds_in_function(self):
        lits = _find_integer_literals(SIMPLE_TRANSFORM)
        vals = [v for _, _, v in lits]
        assert 3 in vals
        assert 5 in vals


# ---------------------------------------------------------------------------
# mutate_constants
# ---------------------------------------------------------------------------

class TestMutateConstants:
    """Tests for constant mutation."""

    def test_produces_mutations(self):
        muts = mutate_constants(SIMPLE_TRANSFORM)
        assert len(muts) > 0
        assert all(m.mutation_type == "constant" for m in muts)

    def test_no_duplicates(self):
        muts = mutate_constants(SIMPLE_TRANSFORM)
        codes = [m.mutated_code for m in muts]
        assert len(codes) == len(set(codes))

    def test_target_describes_change(self):
        muts = mutate_constants(SIMPLE_TRANSFORM)
        assert any("→" in m.target for m in muts)

    def test_identity_has_no_constants(self):
        muts = mutate_constants(IDENTITY_TRANSFORM)
        assert len(muts) == 0


# ---------------------------------------------------------------------------
# mutate_operators
# ---------------------------------------------------------------------------

class TestMutateOperators:
    """Tests for operator mutation."""

    def test_finds_comparison(self):
        muts = mutate_operators(COMPARISON_PROGRAM)
        assert len(muts) > 0
        assert all(m.mutation_type == "operator" for m in muts)

    def test_flips_gt_to_gte(self):
        muts = mutate_operators(COMPARISON_PROGRAM)
        targets = [m.target for m in muts]
        assert any(">→>=" in t for t in targets)

    def test_no_operators_no_mutations(self):
        muts = mutate_operators(IDENTITY_TRANSFORM)
        assert len(muts) == 0

    def test_equality_in_simple(self):
        muts = mutate_operators(SIMPLE_TRANSFORM)
        assert len(muts) > 0
        targets = [m.target for m in muts]
        assert any("==→!=" in t for t in targets)


# ---------------------------------------------------------------------------
# mutate_bounds
# ---------------------------------------------------------------------------

class TestMutateBounds:
    """Tests for loop bound mutation."""

    def test_finds_range(self):
        muts = mutate_bounds(OFF_BY_ONE)
        assert len(muts) > 0
        assert all(m.mutation_type == "bound" for m in muts)

    def test_no_range_no_mutations(self):
        code = "def transform(grid):\n    return grid"
        muts = mutate_bounds(code)
        assert len(muts) == 0


# ---------------------------------------------------------------------------
# mutate_negations
# ---------------------------------------------------------------------------

class TestMutateNegations:
    """Tests for boolean negation mutation."""

    def test_adds_not(self):
        muts = mutate_negations(NEGATE_PROGRAM)
        assert len(muts) > 0
        assert any("add 'not'" in m.target for m in muts)

    def test_removes_not(self):
        code = "def f():\n    if not x:\n        pass"
        muts = mutate_negations(code)
        assert any("remove 'not'" in m.target for m in muts)

    def test_no_if_no_mutations(self):
        muts = mutate_negations(IDENTITY_TRANSFORM)
        assert len(muts) == 0


# ---------------------------------------------------------------------------
# generate_mutations (combined)
# ---------------------------------------------------------------------------

class TestGenerateMutations:
    """Tests for the combined mutation generator."""

    def test_combines_all_types(self):
        muts = generate_mutations(SIMPLE_TRANSFORM)
        types = {m.mutation_type for m in muts}
        # Should have at least constants and operators (== in the code)
        assert "constant" in types
        assert "operator" in types

    def test_all_have_required_fields(self):
        muts = generate_mutations(SIMPLE_TRANSFORM)
        for m in muts:
            assert m.original_code == SIMPLE_TRANSFORM
            assert m.mutated_code != SIMPLE_TRANSFORM
            assert m.mutation_type in ("constant", "operator", "bound", "negate")
            assert m.target


# ---------------------------------------------------------------------------
# _grid_similarity
# ---------------------------------------------------------------------------

class TestGridSimilarity:
    """Tests for grid similarity computation."""

    def test_identical(self):
        g = [[1, 2], [3, 4]]
        assert _grid_similarity(g, g) == 1.0

    def test_all_different(self):
        a = [[1, 1], [1, 1]]
        b = [[0, 0], [0, 0]]
        assert _grid_similarity(a, b) == 0.0

    def test_half_match(self):
        a = [[1, 2], [3, 4]]
        b = [[1, 2], [0, 0]]
        assert _grid_similarity(a, b) == 0.5

    def test_shape_mismatch(self):
        a = [[1, 2, 3]]
        b = [[1, 2]]
        sim = _grid_similarity(a, b)
        assert 0.0 < sim < 1.0

    def test_empty_grids(self):
        assert _grid_similarity([], []) == 0.0


# ---------------------------------------------------------------------------
# _verify_mutant
# ---------------------------------------------------------------------------

class TestVerifyMutant:
    """Tests for fast mutant verification."""

    def test_identity_perfect(self):
        pairs = [([[1, 2], [3, 4]], [[1, 2], [3, 4]])]
        sim = _verify_mutant(IDENTITY_TRANSFORM, pairs)
        assert sim == 1.0

    def test_wrong_code_returns_zero(self):
        sim = _verify_mutant("not valid python!!!", [([[1]], [[1]])])
        assert sim == 0.0

    def test_no_transform_returns_zero(self):
        sim = _verify_mutant("x = 1", [([[1]], [[1]])])
        assert sim == 0.0

    def test_runtime_error_returns_zero(self):
        code = "def transform(grid):\n    return 1 / 0"
        sim = _verify_mutant(code, [([[1]], [[1]])])
        assert sim == 0.0

    def test_color_swap_program(self):
        # Program swaps 3→5
        pairs = [
            ([[3, 0], [0, 3]], [[5, 0], [0, 5]]),
        ]
        sim = _verify_mutant(SIMPLE_TRANSFORM, pairs)
        assert sim == 1.0

    def test_partial_match(self):
        # Program swaps 3→5 but expected 3→7
        pairs = [
            ([[3, 0], [0, 3]], [[7, 0], [0, 7]]),
        ]
        sim = _verify_mutant(SIMPLE_TRANSFORM, pairs)
        assert 0.0 < sim < 1.0


# ---------------------------------------------------------------------------
# evolve_program
# ---------------------------------------------------------------------------

class TestEvolveProgram:
    """Tests for the evolution loop."""

    def test_already_perfect(self):
        pairs = [([[1, 2], [3, 4]], [[1, 2], [3, 4]])]
        result = evolve_program(IDENTITY_TRANSFORM, pairs)
        assert isinstance(result, EvolutionResult)
        # Identity already solves identity task
        assert result.best_similarity == 1.0

    def test_mutation_improves(self):
        # Program swaps 3→5, but we want 3→7
        # Mutation should find the constant swap 5→7
        pairs = [
            ([[3, 0], [0, 3]], [[7, 0], [0, 7]]),
            ([[3, 3], [0, 0]], [[7, 7], [0, 0]]),
        ]
        config = EvolutionConfig(
            min_similarity=0.0,
            max_generations=5,
            mutations_per_generation=50,
            max_total_mutations=500,
        )
        result = evolve_program(SIMPLE_TRANSFORM, pairs, config)
        assert result.best_similarity > 0.5
        # Should solve: just need to change 5→7 and 3→3 stays
        # Actually need both: ==3 stays, out=7
        # The constant mutation should find 5→7
        assert result.solved

    def test_budget_respected(self):
        pairs = [([[1]], [[9]])]
        config = EvolutionConfig(
            max_total_mutations=5,
            max_generations=100,
        )
        result = evolve_program(SIMPLE_TRANSFORM, pairs, config)
        assert result.total_mutations <= 5

    def test_stops_when_no_improvement(self):
        # Unsolvable by mutation (identity can't become color swap)
        pairs = [([[1, 2], [3, 4]], [[9, 9], [9, 9]])]
        config = EvolutionConfig(
            max_generations=20,
            max_total_mutations=1000,
        )
        result = evolve_program(IDENTITY_TRANSFORM, pairs, config)
        # Should stop early, not run all 20 generations
        assert result.generations < 20

    def test_result_has_history(self):
        pairs = [([[3]], [[5]])]
        config = EvolutionConfig(max_generations=3, max_total_mutations=100)
        result = evolve_program(SIMPLE_TRANSFORM, pairs, config)
        assert isinstance(result.history, list)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge case tests."""

    def test_empty_program(self):
        muts = generate_mutations("")
        assert len(muts) == 0

    def test_program_with_no_mutables(self):
        code = "def transform(grid):\n    return grid"
        muts = generate_mutations(code)
        # Might have some operator or bound mutations, but likely few
        # The important thing is it doesn't crash
        assert isinstance(muts, list)

    def test_evolve_empty_pairs(self):
        result = evolve_program(IDENTITY_TRANSFORM, [])
        assert result.best_similarity == 0.0
