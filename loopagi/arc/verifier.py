"""ARC-AGI Verifier Agent.

Executes synthesized programs against training pairs and reports
which pairs pass and which fail, with diagnostic information.

The Verifier is the fourth step in the refinement loop:
Perceive -> Hypothesize -> Synthesize -> Verify -> Refine
"""

from __future__ import annotations

import logging
import signal
import traceback
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loopagi.arc.arc_evaluator import grid_similarity, grids_match
from loopagi.arc.synthesizer import SynthesizedProgram

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import Grid
else:
    Grid = list[list[int]]

logger = logging.getLogger(__name__)


@dataclass
class PairResult:
    """Result of running a program on a single training pair."""

    pair_index: int
    passed: bool
    expected_shape: tuple[int, int]
    actual_shape: tuple[int, int]
    similarity: float = 0.0
    error: str = ""
    expected_output: Grid | None = None
    actual_output: Grid | None = None

    @property
    def shape_correct(self) -> bool:
        return self.expected_shape == self.actual_shape


@dataclass
class VerificationResult:
    """Result of verifying a program against all training pairs."""

    hypothesis: str
    pair_results: list[PairResult] = field(default_factory=list)
    compile_error: str = ""

    @property
    def all_pass(self) -> bool:
        return (
            not self.compile_error
            and len(self.pair_results) > 0
            and all(r.passed for r in self.pair_results)
        )

    @property
    def num_passed(self) -> int:
        return sum(1 for r in self.pair_results if r.passed)

    @property
    def num_total(self) -> int:
        return len(self.pair_results)

    @property
    def pass_rate(self) -> float:
        if not self.pair_results:
            return 0.0
        return self.num_passed / self.num_total

    @property
    def avg_similarity(self) -> float:
        if not self.pair_results:
            return 0.0
        return sum(r.similarity for r in self.pair_results) / self.num_total

    def summary(self) -> str:
        if self.compile_error:
            return f"COMPILE ERROR: {self.compile_error}"
        return (
            f"Verification: {self.num_passed}/{self.num_total} pairs passed "
            f"(avg similarity: {self.avg_similarity:.1%})"
        )

    def failure_report(self) -> str:
        """Detailed report of failures for the Refiner agent."""
        lines: list[str] = [
            f"Hypothesis: {self.hypothesis}",
            f"Result: {self.num_passed}/{self.num_total} pairs passed",
            "",
        ]
        if self.compile_error:
            lines.append(f"Compile error: {self.compile_error}")
            return "\n".join(lines)

        for r in self.pair_results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(
                f"  Pair {r.pair_index}: {status} "
                f"(shape: {r.expected_shape} vs {r.actual_shape}, "
                f"similarity: {r.similarity:.1%})"
            )
            if r.error:
                lines.append(f"    Error: {r.error}")
            elif not r.passed and r.expected_output and r.actual_output:
                diff_text = format_grid_diff(
                    r.expected_output, r.actual_output, indent=4,
                )
                lines.append(diff_text)

        return "\n".join(lines)


def format_grid_diff(
    expected: Grid,
    actual: Grid,
    indent: int = 0,
    max_rows: int = 15,
) -> str:
    """Render expected/actual/diff grids side-by-side.

    Shows exactly which cells differ, making it easy for the LLM
    to understand what went wrong.

    Args:
        expected: The expected output grid.
        actual: The actual output grid.
        indent: Number of spaces to indent each line.
        max_rows: Maximum rows to display (truncate large grids).

    Returns:
        Formatted string with three columns: Expected, Actual, Diff.
    """
    exp_rows = len(expected)
    exp_cols = len(expected[0]) if expected else 0
    act_rows = len(actual)
    act_cols = len(actual[0]) if actual else 0
    max_r = min(max(exp_rows, act_rows), max_rows)
    max_c = max(exp_cols, act_cols)

    pad = " " * indent
    col_width = max_c * 2 + 2  # each cell is "N " plus padding
    lines: list[str] = [
        f"{pad}{'Expected':<{col_width}}{'Actual':<{col_width}}Diff (X = wrong)",
    ]

    wrong_cells: list[tuple[int, int, int, int]] = []

    for r in range(max_r):
        exp_str = ""
        act_str = ""
        diff_str = ""

        for c in range(max_c):
            e_row_len = len(expected[r]) if r < exp_rows else 0
            a_row_len = len(actual[r]) if r < act_rows else 0
            e_val = expected[r][c] if r < exp_rows and c < e_row_len else "-"
            a_val = actual[r][c] if r < act_rows and c < a_row_len else "-"
            exp_str += f"{e_val} "
            act_str += f"{a_val} "
            if e_val == a_val:
                diff_str += ". "
            else:
                diff_str += "X "
                if isinstance(e_val, int) and isinstance(a_val, int):
                    wrong_cells.append((r, c, e_val, a_val))

        lines.append(
            f"{pad}{exp_str:<{col_width}}{act_str:<{col_width}}{diff_str}"
        )

    if max_r < max(exp_rows, act_rows):
        lines.append(f"{pad}... ({max(exp_rows, act_rows) - max_r} more rows)")

    if wrong_cells:
        summary_parts = [
            f"({r},{c}): expected {e} got {a}"
            for r, c, e, a in wrong_cells[:8]
        ]
        if len(wrong_cells) > 8:
            summary_parts.append(f"... +{len(wrong_cells) - 8} more")
        lines.append(f"{pad}Wrong cells: {', '.join(summary_parts)}")

    return "\n".join(lines)


# Timeout (seconds) for executing LLM-generated code.
_EXEC_TIMEOUT = 30


class _ExecTimeout(Exception):
    """Raised when LLM-generated code exceeds the execution time limit."""


def _compile_transform(program: SynthesizedProgram) -> tuple[object | None, str]:
    """Compile a synthesized program and extract the transform function.

    Returns:
        Tuple of (transform_function, error_message).
    """
    if not program.is_valid:
        return None, f"Syntax error: {program.syntax_error}"

    namespace: dict = {}
    try:
        exec(program.source_code, namespace)
    except Exception as e:
        return None, f"Execution error: {type(e).__name__}: {e}"

    transform_fn = namespace.get("transform")
    if transform_fn is None:
        return None, "No 'transform' function found in generated code"
    if not callable(transform_fn):
        return None, "'transform' is not callable"

    return transform_fn, ""


def _run_transform(
    transform_fn: object,
    input_grid: Grid,
) -> tuple[Grid | None, str]:
    """Execute a transform function on an input grid safely.

    Uses SIGALRM to enforce a timeout and prevent infinite loops
    in LLM-generated code.

    Returns:
        Tuple of (output_grid, error_message).
    """
    def _alarm_handler(signum: int, frame: object) -> None:
        raise _ExecTimeout(f"transform() timed out after {_EXEC_TIMEOUT}s")

    old_handler = signal.getsignal(signal.SIGALRM)
    try:
        signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(_EXEC_TIMEOUT)
        result = transform_fn(input_grid)  # type: ignore[operator]
    except _ExecTimeout:
        return None, f"Execution timed out after {_EXEC_TIMEOUT}s (likely infinite loop)"
    except Exception as e:
        tb = traceback.format_exc().split("\n")[-3:]
        return None, f"{type(e).__name__}: {e} ({' '.join(tb)})"
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

    # Validate result is a grid
    if not isinstance(result, list):
        return None, f"Output is {type(result).__name__}, expected list[list[int]]"
    if not result:
        return None, "Output is an empty list"
    if not isinstance(result[0], list):
        return None, f"Output rows are {type(result[0]).__name__}, expected list[int]"

    return result, ""


def verify_program(
    program: SynthesizedProgram,
    train_pairs: list[tuple[Grid, Grid]],
) -> VerificationResult:
    """Verify a synthesized program against training pairs.

    Args:
        program: The program to verify.
        train_pairs: List of (input_grid, expected_output_grid) tuples.

    Returns:
        VerificationResult with per-pair results and diagnostics.
    """
    result = VerificationResult(hypothesis=program.hypothesis)

    # Compile
    transform_fn, error = _compile_transform(program)
    if error:
        result.compile_error = error
        logger.warning("Compile failed for '%s': %s", program.hypothesis[:60], error)
        return result

    # Run on each training pair
    for i, (input_grid, expected_output) in enumerate(train_pairs):
        actual_output, run_error = _run_transform(transform_fn, input_grid)

        if run_error:
            exp_rows = len(expected_output)
            exp_cols = len(expected_output[0]) if expected_output else 0
            result.pair_results.append(PairResult(
                pair_index=i,
                passed=False,
                expected_shape=(exp_rows, exp_cols),
                actual_shape=(0, 0),
                similarity=0.0,
                error=run_error,
                expected_output=expected_output,
                actual_output=None,
            ))
            continue

        exp_rows = len(expected_output)
        exp_cols = len(expected_output[0]) if expected_output else 0
        act_rows = len(actual_output)
        act_cols = len(actual_output[0]) if actual_output else 0

        passed = grids_match(actual_output, expected_output)
        sim = grid_similarity(actual_output, expected_output)

        result.pair_results.append(PairResult(
            pair_index=i,
            passed=passed,
            expected_shape=(exp_rows, exp_cols),
            actual_shape=(act_rows, act_cols),
            similarity=sim,
            expected_output=expected_output,
            actual_output=actual_output,
        ))

    logger.info(
        "Verified '%s': %d/%d pairs passed (avg sim %.1f%%)",
        program.hypothesis[:60],
        result.num_passed,
        result.num_total,
        result.avg_similarity * 100,
    )
    return result
