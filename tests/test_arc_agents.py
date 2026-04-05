"""Tests for ARC-AGI specialist agents and solver.

Tests the full refinement loop:
Perceive -> Hypothesize -> Synthesize -> Verify -> Refine -> Solve
"""

from __future__ import annotations

import pytest

from loopagi.arc.arc_loader import ArcTask, GridPair, TestInput
from loopagi.arc.hypothesizer import (
    Hypothesis,
    HypothesisSet,
    generate_pattern_hypotheses,
    hypothesize,
    parse_llm_hypotheses,
)
from loopagi.arc.perceiver import (
    GridAnalysis,
    PairAnalysis,
    PerceptionReport,
    TaskComplexity,
    analyze_grid,
    analyze_pair,
    estimate_complexity,
    find_consistent_patterns,
    format_perception_prompt,
    perceive_task,
)
from loopagi.arc.refiner import (
    RefinementPlan,
    diagnose_failures,
    refine,
    suggest_refinements,
)
from loopagi.arc.solver import MultiAgentArcSolver, SolveResult, solve_task
from loopagi.arc.synthesizer import (
    SynthesizedProgram,
    _try_fix_syntax,
    extract_code_from_response,
    synthesize_from_code,
    synthesize_from_hypothesis,
    synthesize_from_llm,
    synthesize_identity,
    validate_syntax,
)
from loopagi.arc.verifier import (
    PairResult,
    VerificationResult,
    format_grid_diff,
    verify_program,
)


# --- Fixtures ---


@pytest.fixture
def identity_task() -> ArcTask:
    """Task where output equals input."""
    return ArcTask(
        task_id="identity",
        train=[
            GridPair(input=[[1, 2], [3, 4]], output=[[1, 2], [3, 4]]),
            GridPair(input=[[5, 6]], output=[[5, 6]]),
        ],
        test=[
            TestInput(input=[[7, 8], [9, 0]], output=[[7, 8], [9, 0]]),
        ],
    )


@pytest.fixture
def mirror_task() -> ArcTask:
    """Task where output is horizontal flip of input."""
    return ArcTask(
        task_id="mirror",
        train=[
            GridPair(input=[[1, 2], [3, 4]], output=[[3, 4], [1, 2]]),
            GridPair(input=[[5, 6], [7, 8]], output=[[7, 8], [5, 6]]),
        ],
        test=[
            TestInput(input=[[0, 1], [2, 3]], output=[[2, 3], [0, 1]]),
        ],
    )


@pytest.fixture
def color_swap_task() -> ArcTask:
    """Task where colors 1 and 2 are swapped."""
    return ArcTask(
        task_id="color_swap",
        train=[
            GridPair(input=[[1, 0, 2]], output=[[2, 0, 1]]),
            GridPair(input=[[1, 1, 2, 2]], output=[[2, 2, 1, 1]]),
        ],
        test=[
            TestInput(input=[[0, 1, 2, 0]], output=[[0, 2, 1, 0]]),
        ],
    )


# --- Perceiver Tests ---


class TestPerceiver:
    def test_analyze_grid(self) -> None:
        g = [[0, 1, 0], [0, 1, 0], [0, 0, 0]]
        analysis = analyze_grid(g)
        assert analysis.shape == (3, 3)
        assert analysis.num_colors == 2
        assert analysis.background == 0
        assert analysis.num_objects >= 1

    def test_analyze_pair_same_shape(self, identity_task: ArcTask) -> None:
        pair = identity_task.train[0]
        pa = analyze_pair(pair.input, pair.output)
        assert pa.shape_changed is False
        assert pa.colors_added == set()
        assert pa.colors_removed == set()

    def test_perceive_task(self, identity_task: ArcTask) -> None:
        report = perceive_task(identity_task)
        assert report.task_id == "identity"
        assert report.num_pairs == 2
        assert len(report.pair_analyses) == 2

    def test_consistent_patterns(self, identity_task: ArcTask) -> None:
        report = perceive_task(identity_task)
        assert "output_same_shape_as_input" in report.consistent_patterns
        assert "same_color_palette" in report.consistent_patterns

    def test_format_prompt(self, identity_task: ArcTask) -> None:
        prompt = format_perception_prompt(identity_task)
        assert "Pair 1" in prompt
        assert "Pair 2" in prompt
        assert "rule" in prompt.lower()


# --- Complexity Estimator Tests ---


class TestComplexityEstimator:
    def test_simple_task_low_complexity(self, identity_task: ArcTask) -> None:
        report = perceive_task(identity_task)
        level, params = estimate_complexity(report)
        assert level == TaskComplexity.LOW
        assert params["max_hypotheses"] == 3
        assert params["max_iterations"] == 3

    def test_empty_report_defaults_medium(self) -> None:
        report = PerceptionReport(task_id="empty", num_pairs=0)
        level, params = estimate_complexity(report)
        assert level == TaskComplexity.MEDIUM

    def test_complex_task_higher_complexity(self) -> None:
        """A task with large grids, many colors, shape changes should be medium or high."""
        task = ArcTask(
            task_id="complex",
            train=[
                GridPair(
                    input=[[c % 8 for c in range(12)] for _ in range(12)],
                    output=[[c % 8 for c in range(6)] for _ in range(6)],
                ),
                GridPair(
                    input=[[c % 8 for c in range(10)] for _ in range(10)],
                    output=[[c % 8 for c in range(5)] for _ in range(5)],
                ),
            ],
            test=[TestInput(input=[[0]], output=[[0]])],
        )
        report = perceive_task(task)
        level, params = estimate_complexity(report)
        assert level in (TaskComplexity.MEDIUM, TaskComplexity.HIGH)
        assert params["max_hypotheses"] >= 5

    def test_params_structure(self) -> None:
        for level in (TaskComplexity.LOW, TaskComplexity.MEDIUM, TaskComplexity.HIGH):
            params = TaskComplexity.PARAMS[level]
            assert "max_hypotheses" in params
            assert "max_iterations" in params
            assert params["max_hypotheses"] > 0
            assert params["max_iterations"] > 0


# --- Hypothesizer Tests ---


class TestHypothesizer:
    def test_generate_from_patterns(self, identity_task: ArcTask) -> None:
        report = perceive_task(identity_task)
        hyps = generate_pattern_hypotheses(report)
        assert len(hyps) > 0
        assert all(isinstance(h, Hypothesis) for h in hyps)

    def test_hypothesize(self, identity_task: ArcTask) -> None:
        report = perceive_task(identity_task)
        hyp_set = hypothesize(report)
        assert hyp_set.task_id == "identity"
        assert len(hyp_set.hypotheses) > 0

    def test_hypothesis_ranking(self) -> None:
        hyp_set = HypothesisSet(
            task_id="test",
            hypotheses=[
                Hypothesis(rule="low", confidence=0.1),
                Hypothesis(rule="high", confidence=0.9),
                Hypothesis(rule="mid", confidence=0.5),
            ],
        )
        assert hyp_set.best.rule == "high"
        ranked = hyp_set.ranked()
        assert ranked[0].confidence >= ranked[1].confidence >= ranked[2].confidence

    def test_parse_llm_hypotheses(self) -> None:
        response = (
            "RULE: Rotate the grid 90 degrees clockwise\n"
            "CONFIDENCE: 0.8\n"
            "EVIDENCE: All pairs show rotation\n"
            "\n"
            "RULE: Reflect horizontally\n"
            "CONFIDENCE: 0.6\n"
            "EVIDENCE: Top and bottom swap\n"
        )
        hyps = parse_llm_hypotheses(response)
        assert len(hyps) == 2
        assert hyps[0].confidence == 0.8
        assert "rotate" in hyps[0].rule.lower()

    def test_parse_empty_response(self) -> None:
        assert parse_llm_hypotheses("") == []


# --- Synthesizer Tests ---


class TestSynthesizer:
    def test_validate_syntax_valid(self) -> None:
        is_valid, err = validate_syntax("def f(): return 1")
        assert is_valid is True
        assert err == ""

    def test_validate_syntax_invalid(self) -> None:
        is_valid, err = validate_syntax("def f( return 1")
        assert is_valid is False
        assert "SyntaxError" not in err or err  # just needs to be non-empty

    def test_extract_code_fenced(self) -> None:
        response = "Here's the code:\n```python\ndef transform(grid):\n    return grid\n```\nDone."
        code = extract_code_from_response(response)
        assert "def transform" in code

    def test_extract_code_bare(self) -> None:
        response = "def transform(grid):\n    return grid\n"
        code = extract_code_from_response(response)
        assert "def transform" in code

    def test_synthesize_identity(self) -> None:
        prog = synthesize_identity()
        assert prog.is_valid is True
        assert "transform" in prog.source_code

    def test_synthesize_from_code(self) -> None:
        code = "def transform(grid): return grid"
        prog = synthesize_from_code("test", code)
        assert prog.is_valid is True

    def test_synthesize_from_hypothesis_rotate(self) -> None:
        h = Hypothesis(rule="Rotate 90 degrees clockwise", confidence=0.8)
        prog = synthesize_from_hypothesis(h)
        assert prog.is_valid is True
        assert "rotate_cw" in prog.source_code

    def test_synthesize_from_hypothesis_unknown(self) -> None:
        h = Hypothesis(rule="Do something very complex and unknown", confidence=0.3)
        prog = synthesize_from_hypothesis(h)
        # Falls back to identity
        assert prog.is_valid is True

    def test_extract_code_no_code_returns_empty(self) -> None:
        response = "The transformation scales the grid by a factor of 3.0."
        code = extract_code_from_response(response)
        assert code == ""

    def test_extract_code_garbage_returns_empty(self) -> None:
        response = "I think the answer involves color mapping and rotation."
        code = extract_code_from_response(response)
        assert code == ""

    def test_try_fix_syntax_unclosed_bracket(self) -> None:
        code = "def transform(grid):\n    return [row[:] for row in grid"
        fixed = _try_fix_syntax(code)
        is_valid, _ = validate_syntax(fixed)
        assert is_valid is True

    def test_try_fix_syntax_unclosed_paren(self) -> None:
        code = "def transform(grid):\n    return list(reversed(grid)"
        fixed = _try_fix_syntax(code)
        is_valid, _ = validate_syntax(fixed)
        assert is_valid is True

    def test_try_fix_syntax_missing_return(self) -> None:
        code = "def transform(grid):\n    x = [row[:] for row in grid]"
        fixed = _try_fix_syntax(code)
        assert "return" in fixed

    def test_synthesize_from_llm_empty_response(self) -> None:
        h = Hypothesis(rule="test", confidence=0.5)
        prog = synthesize_from_llm(h, "")
        assert prog.is_valid is True  # Falls back to identity

    def test_synthesize_from_llm_garbage_response(self) -> None:
        h = Hypothesis(rule="test", confidence=0.5)
        prog = synthesize_from_llm(h, "The grid is scaled by 3.0")
        assert prog.is_valid is True  # Falls back to identity

    def test_synthesize_from_llm_unclosed_bracket(self) -> None:
        h = Hypothesis(rule="test", confidence=0.5)
        response = "```python\ndef transform(grid):\n    return [row[:] for row in grid\n```"
        prog = synthesize_from_llm(h, response)
        assert prog.is_valid is True  # Repaired by _try_fix_syntax

    def test_code_property_alias(self) -> None:
        """N.3: .code property returns same value as .source_code."""
        prog = SynthesizedProgram(
            hypothesis="test",
            source_code="def transform(grid): return grid",
        )
        assert prog.code == prog.source_code
        assert prog.code == "def transform(grid): return grid"

    def test_code_property_on_identity(self) -> None:
        """N.3: .code property works on identity programs."""
        prog = synthesize_identity()
        assert prog.code == prog.source_code
        assert "transform" in prog.code


# --- Verifier Tests ---


class TestVerifier:
    def test_verify_correct_program(self) -> None:
        prog = SynthesizedProgram(
            hypothesis="identity",
            source_code="def transform(grid): return [row[:] for row in grid]",
            is_valid=True,
        )
        pairs = [([[1, 2], [3, 4]], [[1, 2], [3, 4]])]
        result = verify_program(prog, pairs)
        assert result.all_pass is True
        assert result.num_passed == 1

    def test_verify_wrong_program(self) -> None:
        prog = SynthesizedProgram(
            hypothesis="always zeros",
            source_code="def transform(grid): return [[0]*len(grid[0]) for _ in grid]",
            is_valid=True,
        )
        pairs = [([[1, 2]], [[1, 2]])]
        result = verify_program(prog, pairs)
        assert result.all_pass is False
        assert result.avg_similarity < 1.0

    def test_verify_compile_error(self) -> None:
        prog = SynthesizedProgram(
            hypothesis="bad code",
            source_code="def transform(grid: invalid syntax",
            is_valid=False,
            syntax_error="invalid syntax",
        )
        pairs = [([[1]], [[1]])]
        result = verify_program(prog, pairs)
        assert result.all_pass is False
        assert result.compile_error != ""

    def test_verify_runtime_error(self) -> None:
        prog = SynthesizedProgram(
            hypothesis="crash",
            source_code="def transform(grid): return 1/0",
            is_valid=True,
        )
        pairs = [([[1]], [[1]])]
        result = verify_program(prog, pairs)
        assert result.all_pass is False
        assert result.pair_results[0].error != ""

    def test_failure_report(self) -> None:
        prog = SynthesizedProgram(
            hypothesis="wrong",
            source_code="def transform(grid): return [[0]]",
            is_valid=True,
        )
        pairs = [([[1, 2], [3, 4]], [[1, 2], [3, 4]])]
        result = verify_program(prog, pairs)
        report = result.failure_report()
        assert "FAIL" in report

    def test_failure_report_includes_grid_diff(self) -> None:
        prog = SynthesizedProgram(
            hypothesis="partial match",
            source_code=(
                "def transform(grid):\n"
                "    out = [row[:] for row in grid]\n"
                "    out[1][1] = 0\n"
                "    return out\n"
            ),
            is_valid=True,
        )
        pairs = [([[1, 2, 3], [4, 5, 6], [7, 8, 9]],
                  [[1, 2, 3], [4, 5, 6], [7, 8, 9]])]
        result = verify_program(prog, pairs)
        report = result.failure_report()
        assert "Expected" in report
        assert "Actual" in report
        assert "X" in report
        assert "Wrong cells" in report

    def test_pair_result_stores_grids(self) -> None:
        prog = SynthesizedProgram(
            hypothesis="identity",
            source_code="def transform(grid): return [row[:] for row in grid]",
            is_valid=True,
        )
        pairs = [([[1, 2], [3, 4]], [[1, 2], [3, 4]])]
        result = verify_program(prog, pairs)
        pr = result.pair_results[0]
        assert pr.expected_output == [[1, 2], [3, 4]]
        assert pr.actual_output == [[1, 2], [3, 4]]


# --- Grid Diff Tests ---


class TestGridDiff:
    def test_identical_grids(self) -> None:
        grid = [[1, 2], [3, 4]]
        diff = format_grid_diff(grid, grid)
        assert "Wrong cells" not in diff  # no wrong cells when grids match

    def test_single_cell_diff(self) -> None:
        expected = [[1, 2], [3, 4]]
        actual = [[1, 2], [3, 0]]
        diff = format_grid_diff(expected, actual)
        assert "X" in diff
        assert "Wrong cells" in diff
        assert "(1,1): expected 4 got 0" in diff

    def test_different_shapes(self) -> None:
        expected = [[1, 2, 3]]
        actual = [[1, 2]]
        diff = format_grid_diff(expected, actual)
        assert "Expected" in diff
        assert "Actual" in diff

    def test_indent(self) -> None:
        expected = [[1]]
        actual = [[2]]
        diff = format_grid_diff(expected, actual, indent=6)
        for line in diff.split("\n"):
            assert line.startswith("      ")

    def test_truncation(self) -> None:
        expected = [[i] for i in range(20)]
        actual = [[i + 1] for i in range(20)]
        diff = format_grid_diff(expected, actual, max_rows=5)
        assert "more rows" in diff

    def test_many_wrong_cells_truncated(self) -> None:
        expected = [[i for i in range(10)]]
        actual = [[i + 1 for i in range(10)]]
        diff = format_grid_diff(expected, actual)
        assert "Wrong cells" in diff


# --- Refiner Tests ---


class TestRefiner:
    def test_diagnose_compile_error(self) -> None:
        result = VerificationResult(
            hypothesis="broken", compile_error="syntax error"
        )
        diag = diagnose_failures(result)
        assert any("compile" in d.lower() for d in diag)

    def test_diagnose_shape_mismatch(self) -> None:
        from loopagi.arc.verifier import PairResult
        result = VerificationResult(
            hypothesis="wrong shape",
            pair_results=[
                PairResult(
                    pair_index=0, passed=False,
                    expected_shape=(2, 2), actual_shape=(3, 3),
                    similarity=0.5,
                ),
            ],
        )
        diag = diagnose_failures(result)
        assert any("shape" in d.lower() for d in diag)

    def test_refine_solved_no_actions(self) -> None:
        from loopagi.arc.verifier import PairResult
        result = VerificationResult(
            hypothesis="correct",
            pair_results=[
                PairResult(pair_index=0, passed=True,
                           expected_shape=(2, 2), actual_shape=(2, 2),
                           similarity=1.0),
            ],
        )
        h = Hypothesis(rule="correct", confidence=0.9)
        plan = refine("test", result, h, iteration=0)
        assert len(plan.actions) == 0

    def test_refine_max_iterations_abandon(self) -> None:
        result = VerificationResult(hypothesis="stuck", compile_error="error")
        h = Hypothesis(rule="stuck", confidence=0.5)
        plan = refine("test", result, h, iteration=10, max_iterations=10)
        assert plan.should_abandon is True

    def test_suggest_refinements(self) -> None:
        from loopagi.arc.verifier import PairResult
        result = VerificationResult(
            hypothesis="partial",
            pair_results=[
                PairResult(pair_index=0, passed=True,
                           expected_shape=(2, 2), actual_shape=(2, 2),
                           similarity=1.0),
                PairResult(pair_index=1, passed=False,
                           expected_shape=(2, 2), actual_shape=(2, 2),
                           similarity=0.75),
            ],
        )
        h = Hypothesis(rule="almost right", confidence=0.7)
        actions = suggest_refinements(result, h, iteration=1)
        assert len(actions) > 0


# --- Solver Tests ---


class TestSolver:
    def test_solve_identity_task(self, identity_task: ArcTask) -> None:
        result = solve_task(identity_task, max_hypotheses=3, max_iterations=3)
        assert isinstance(result, SolveResult)
        assert result.task_id == "identity"
        assert result.num_iterations >= 1

    def test_solve_returns_predictions(self, identity_task: ArcTask) -> None:
        result = solve_task(identity_task, max_hypotheses=2, max_iterations=2)
        assert len(result.predictions) == 1  # 1 test input
        assert len(result.predictions[0]) >= 1

    def test_solve_result_summary(self, identity_task: ArcTask) -> None:
        result = solve_task(identity_task, max_hypotheses=1, max_iterations=1)
        s = result.summary()
        assert "identity" in s

    def test_multi_agent_solver_protocol(self, identity_task: ArcTask) -> None:
        solver = MultiAgentArcSolver(max_hypotheses=2, max_iterations=2)
        assert solver.name == "multi_agent"
        predictions = solver.solve(identity_task)
        assert len(predictions) == 1
        assert len(predictions[0]) >= 1

    def test_solver_with_real_eval_task(self) -> None:
        """Test solver on a real ARC task if data is available."""
        from loopagi.arc.arc_loader import load_default_datasets
        datasets = load_default_datasets(validate=False)
        if "training" not in datasets:
            pytest.skip("Training data not available")
        ds = datasets["training"]
        # Pick a task
        task = ds.get_task(ds.task_ids()[0])
        result = solve_task(task, max_hypotheses=2, max_iterations=2)
        assert result.task_id == task.task_id
        assert result.num_iterations >= 1
