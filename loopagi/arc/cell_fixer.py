"""Targeted cell-fix refinement for near-miss ARC programs.

For programs that achieve high similarity (>=95%), identifies the specific
wrong cells and asks the LLM to fix either the code or the cell values.

Usage:
    from loopagi.arc.cell_fixer import fix_cells
    result = fix_cells(bridge, task, best_program, train_pairs)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import ArcTask, Grid
    from loopagi.arc.llm_bridge import LLMBridge
    from loopagi.arc.synthesizer import SynthesizedProgram
    from loopagi.arc.transducer import TrainPair

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class WrongCell:
    """A single wrong cell in a grid comparison."""

    row: int
    col: int
    expected: int
    actual: int


@dataclass
class CellFixResult:
    """Result of a cell-fix attempt."""

    fixed_grid: Grid | None
    similarity: float
    method: str  # "code_fix" or "cell_transduction"
    fixed_program: SynthesizedProgram | None = None
    error: str = ""


# ---------------------------------------------------------------------------
# Cell identification
# ---------------------------------------------------------------------------


def identify_wrong_cells(
    expected: Grid,
    actual: Grid,
) -> list[WrongCell]:
    """Return list of wrong cells between expected and actual grids.

    Args:
        expected: The correct output grid.
        actual: The produced output grid.

    Returns:
        List of WrongCell entries for each mismatched cell.
        Returns empty list if shapes differ.
    """
    if not expected or not actual:
        return []
    if len(expected) != len(actual):
        return []
    if len(expected[0]) != len(actual[0]):
        return []

    wrong: list[WrongCell] = []
    for r, (exp_row, act_row) in enumerate(zip(expected, actual)):
        for c, (exp_val, act_val) in enumerate(zip(exp_row, act_row)):
            if exp_val != act_val:
                wrong.append(WrongCell(row=r, col=c, expected=exp_val, actual=act_val))
    return wrong


def format_wrong_cells_text(wrong_cells: list[WrongCell]) -> str:
    """Format wrong cells as human-readable text for prompts."""
    if not wrong_cells:
        return "No wrong cells."
    lines = [f"  ({wc.row},{wc.col}): got {wc.actual}, expected {wc.expected}" for wc in wrong_cells]
    return f"{len(wrong_cells)} wrong cell(s):\n" + "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompt formatting
# ---------------------------------------------------------------------------


def _compact_grid(grid: Grid) -> str:
    """Compact grid representation for prompts."""
    return "[" + ",".join("[" + ",".join(str(v) for v in row) + "]" for row in grid) + "]"


def format_cell_fix_prompt(
    train_pairs: list[TrainPair],
    current_code: str,
    wrong_cells: list[WrongCell],
    current_output: Grid,
    expected_output: Grid,
) -> str:
    """Format a targeted prompt for fixing specific wrong cells.

    Args:
        train_pairs: Training (input, output) pairs for context.
        current_code: The current Python transform function.
        wrong_cells: List of cells that are wrong.
        current_output: The grid the current code produced.
        expected_output: The correct expected grid.

    Returns:
        A prompt string for the LLM.
    """
    pairs_text = ""
    for i, (inp, out) in enumerate(train_pairs, 1):
        pairs_text += f"Pair {i}: {_compact_grid(inp)} -> {_compact_grid(out)}\n"

    wrong_text = format_wrong_cells_text(wrong_cells)

    return (
        "You are fixing a Python function that solves an ARC-AGI puzzle.\n\n"
        f"Training examples:\n{pairs_text}\n"
        f"Current code:\n```python\n{current_code}\n```\n\n"
        f"Current output: {_compact_grid(current_output)}\n"
        f"Expected output: {_compact_grid(expected_output)}\n\n"
        f"{wrong_text}\n\n"
        "Fix the transform() function so ALL cells are correct.\n"
        "Reply with ONLY a ```python block containing the corrected function."
    )


# ---------------------------------------------------------------------------
# Cell-fix execution
# ---------------------------------------------------------------------------


def fix_cells(
    bridge: LLMBridge,
    task: ArcTask,
    best_program: SynthesizedProgram,
    train_pairs: list[TrainPair],
) -> CellFixResult:
    """Try to fix a near-miss program by targeting specific wrong cells.

    Runs the current program on each training pair, identifies wrong cells,
    then asks the LLM to fix the code with that targeted information.

    Args:
        bridge: LLM bridge for inference.
        task: The ARC task being solved.
        best_program: The near-miss program to fix.
        train_pairs: Training (input, output) pairs.

    Returns:
        CellFixResult with the fix outcome.
    """
    from loopagi.arc.synthesizer import extract_code_from_response, synthesize_from_code
    from loopagi.arc.verifier import verify_program

    if not best_program.source_code:
        return CellFixResult(fixed_grid=None, similarity=0.0, method="code_fix", error="No source code")

    # Find worst training pair (most wrong cells)
    worst_pair_idx = -1
    worst_wrong: list[WrongCell] = []
    worst_actual: Grid = []
    worst_expected: Grid = []

    for i, (train_in, train_out) in enumerate(train_pairs):
        try:
            ns: dict = {}
            exec(best_program.source_code, ns)  # noqa: S102
            transform = ns.get("transform")
            if transform is None:
                continue
            actual = transform(train_in)
            if not isinstance(actual, list):
                continue
        except Exception:
            continue

        wrong = identify_wrong_cells(train_out, actual)
        if len(wrong) > len(worst_wrong):
            worst_pair_idx = i
            worst_wrong = wrong
            worst_actual = actual
            worst_expected = train_out

    if worst_pair_idx < 0 or not worst_wrong:
        logger.debug("Cell fixer: no wrong cells found (program may be perfect or crashing)")
        return CellFixResult(fixed_grid=None, similarity=1.0, method="code_fix")

    logger.info(
        "[%s] Cell fixer: %d wrong cells on training pair %d",
        task.task_id, len(worst_wrong), worst_pair_idx + 1,
    )

    # Ask LLM to fix the code
    prompt = format_cell_fix_prompt(
        train_pairs, best_program.source_code,
        worst_wrong, worst_actual, worst_expected,
    )
    response = bridge.call(prompt)
    fixed_code = extract_code_from_response(response)

    if not fixed_code:
        logger.debug("Cell fixer: LLM returned no code")
        return CellFixResult(fixed_grid=None, similarity=0.0, method="code_fix", error="No code in response")

    # Verify the fixed program
    fixed_program = synthesize_from_code(best_program.hypothesis, fixed_code)
    if not fixed_program.is_valid:
        logger.debug("Cell fixer: fixed code has syntax errors")
        return CellFixResult(fixed_grid=None, similarity=0.0, method="code_fix", error="Syntax error in fix")

    vr = verify_program(fixed_program, train_pairs)
    logger.info(
        "[%s] Cell fixer result: %d/%d pairs passed, avg_sim=%.1f%%",
        task.task_id, sum(1 for p in vr.pair_results if p.passed), len(vr.pair_results),
        vr.avg_similarity * 100,
    )

    return CellFixResult(
        fixed_grid=None,
        similarity=vr.avg_similarity,
        method="code_fix",
        fixed_program=fixed_program,
    )


# ---------------------------------------------------------------------------
# Transduction cell fix (Phase D: post-relaxed near-miss recovery)
# ---------------------------------------------------------------------------

_TRANSDUCTION_FIX_PROMPT = (
    "You are fixing a near-miss prediction for an ARC-AGI puzzle.\n\n"
    "Training examples (input -> output):\n{pairs}\n"
    "When I predict the training outputs, I get these errors:\n{errors}\n\n"
    "Test input: {test_input}\n"
    "My current prediction: {prediction}\n\n"
    "Based on the error patterns above, fix my prediction.\n"
    "Reply with ONLY the corrected grid in the same compact format."
)


def fix_transduction_cells(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
    test_input: Grid,
    prediction: Grid,
    transduction_fn: callable | None = None,
) -> CellFixResult:
    """Fix a near-miss transduction prediction by analyzing training errors.

    Runs the same transduction on each training input, compares against
    expected outputs to find systematic errors, then asks the LLM to
    fix the test prediction based on those error patterns.

    Args:
        bridge: LLM bridge for inference.
        train_pairs: Training (input, output) pairs.
        test_input: The test input grid.
        prediction: The near-miss test prediction to fix.
        transduction_fn: Optional callable(bridge, pairs, input) -> grid.
            If None, uses default transduce().
    """
    from loopagi.arc.transducer import _grid_similarity, transduce

    # Identify training errors
    error_lines: list[str] = []
    for i, (train_in, train_out) in enumerate(train_pairs):
        if transduction_fn is not None:
            train_pred = transduction_fn(bridge, train_pairs, train_in)
        else:
            result = transduce(bridge, train_pairs, train_in, temperature=0.0)
            train_pred = result.predicted_grid if result.predicted_grid else None
        if train_pred is None:
            continue
        wrong = identify_wrong_cells(train_out, train_pred)
        if wrong:
            error_lines.append(
                f"Pair {i+1}: {format_wrong_cells_text(wrong)}")

    if not error_lines:
        # No training errors found — can't guide fix
        return CellFixResult(
            fixed_grid=None, similarity=0.0,
            method="transduction_fix", error="No training errors to learn from")

    pairs_text = ""
    for i, (inp, out) in enumerate(train_pairs, 1):
        pairs_text += f"Pair {i}: {_compact_grid(inp)} -> {_compact_grid(out)}\n"

    prompt = _TRANSDUCTION_FIX_PROMPT.format(
        pairs=pairs_text,
        errors="\n".join(error_lines),
        test_input=_compact_grid(test_input),
        prediction=_compact_grid(prediction),
    )

    response = bridge.call(prompt, temperature=0.0)
    from loopagi.arc.transducer import parse_grid_from_response
    fixed = parse_grid_from_response(response)

    if fixed is None:
        return CellFixResult(
            fixed_grid=None, similarity=0.0,
            method="transduction_fix", error="No grid in response")

    sim = _grid_similarity(prediction, fixed)
    logger.info("Transduction cell fix: original->fixed sim=%.1f%%", sim * 100)
    return CellFixResult(
        fixed_grid=fixed, similarity=sim, method="transduction_fix")
