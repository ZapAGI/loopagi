"""Tests for chapter-02/real_emergence_demo.py scoring engine."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "chapter-02"))

from real_emergence_demo import CodeScore, EmergenceResult, score_code_output


class TestScoreCodeOutput:
    """Tests for the deterministic code scoring engine."""

    def test_perfect_code(self) -> None:
        code = (
            "```python\n"
            "import logging\n"
            "import functools\n\n"
            "logger = logging.getLogger(__name__)\n\n"
            "class RetryExhaustedError(Exception):\n"
            '    """Raised when retries are exhausted."""\n\n'
            "def retry(max_retries: int = 3, base_delay: float = 1.0):\n"
            '    """Retry decorator with backoff."""\n'
            "    def decorator(func):\n"
            "        @functools.wraps(func)\n"
            "        def wrapper(*args, **kwargs):\n"
            "            if not max_retries:\n"
            "                return func(*args, **kwargs)\n"
            "            for attempt in range(max_retries):\n"
            "                try:\n"
            "                    return func(*args, **kwargs)\n"
            "                except Exception as e:\n"
            "                    logger.warning('Retry %d', attempt)\n"
            "                    if attempt == max_retries - 1:\n"
            "                        raise RetryExhaustedError() from e\n"
            "        return wrapper\n"
            "    return decorator\n"
            "```"
        )
        score = score_code_output("coder", code)
        assert score.has_function
        assert score.has_class
        assert score.has_type_hints
        assert score.has_docstring
        assert score.has_error_handling
        assert score.has_custom_exception
        assert score.has_decorator
        assert score.has_logging
        assert score.has_multiple_functions
        assert score.has_default_params
        assert score.code_block_found
        assert score.hits >= 10
        assert score.total >= 0.85
        assert score.grade == "A"

    def test_minimal_code(self) -> None:
        code = "def fib(n): return n if n <= 1 else fib(n-1) + fib(n-2)"
        score = score_code_output("agent", code)
        assert score.has_function
        assert not score.has_type_hints
        assert not score.has_docstring
        assert not score.has_error_handling
        assert score.total < 0.5

    def test_no_code(self) -> None:
        score = score_code_output("agent", "I cannot help with that.")
        assert not score.has_function
        assert not score.code_block_found
        assert score.total < 0.2

    def test_code_with_error_handling(self) -> None:
        code = (
            "def process(data):\n"
            "    try:\n"
            "        return int(data)\n"
            "    except ValueError:\n"
            "        return None\n"
        )
        score = score_code_output("agent", code)
        assert score.has_function
        assert score.has_error_handling

    def test_code_with_edge_cases(self) -> None:
        code = (
            "def safe_div(a, b):\n"
            "    if not b:\n"
            "        return 0\n"
            "    return a / b\n"
        )
        score = score_code_output("agent", code)
        assert score.has_edge_cases

    def test_grade_boundaries(self) -> None:
        s = CodeScore(agent_name="test")
        s.has_function = True
        s.has_class = True
        s.has_type_hints = True
        s.has_docstring = True
        s.has_error_handling = True
        s.has_custom_exception = True
        s.has_edge_cases = True
        s.has_decorator = True
        s.has_logging = True
        s.has_multiple_functions = True
        s.has_default_params = True
        s.code_block_found = True
        assert s.grade == "A"
        assert s.hits == 12

        s2 = CodeScore(agent_name="test")
        s2.has_function = True
        assert s2.grade in ("D", "F")


class TestEmergenceResult:
    """Tests for EmergenceResult aggregation."""

    def test_best_individual(self) -> None:
        scores = [
            CodeScore(agent_name="a"),
            CodeScore(agent_name="b"),
        ]
        scores[0].has_function = True
        scores[0].has_type_hints = True
        scores[1].has_function = True
        scores[1].has_type_hints = True
        scores[1].has_docstring = True

        result = EmergenceResult(individual_scores=scores)
        assert result.best_individual == scores[1].total

    def test_avg_individual(self) -> None:
        s1 = CodeScore(agent_name="a")
        s1.has_function = True
        s2 = CodeScore(agent_name="b")
        s2.has_function = True
        s2.has_type_hints = True

        result = EmergenceResult(individual_scores=[s1, s2])
        assert result.avg_individual == (s1.total + s2.total) / 2

    def test_emergence_detected(self) -> None:
        ind = CodeScore(agent_name="solo")
        ind.has_function = True

        orch = CodeScore(agent_name="orchestrated")
        orch.has_function = True
        orch.has_type_hints = True
        orch.has_docstring = True
        orch.has_error_handling = True
        orch.has_edge_cases = True
        orch.code_block_found = True

        result = EmergenceResult(
            individual_scores=[ind],
            orchestrated_score=orch,
        )
        assert result.is_emergent
        assert result.emergence_ratio > 1.0

    def test_no_emergence(self) -> None:
        good = CodeScore(agent_name="good")
        good.has_function = True
        good.has_type_hints = True
        good.has_docstring = True
        good.has_error_handling = True
        good.has_edge_cases = True
        good.code_block_found = True

        weak = CodeScore(agent_name="weak")
        weak.has_function = True

        result = EmergenceResult(
            individual_scores=[good],
            orchestrated_score=weak,
        )
        assert not result.is_emergent

    def test_empty_results(self) -> None:
        result = EmergenceResult()
        assert result.best_individual == 0.0
        assert result.avg_individual == 0.0
        assert result.orchestrated_total == 0.0
