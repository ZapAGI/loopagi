"""Direct grid transduction for ARC-AGI tasks.

Instead of synthesizing a Python ``transform()`` function, this module
asks the LLM to directly predict the output grid from training examples.
For simple tasks (color swaps, reflections, fills), the LLM can "see"
the pattern and produce the correct answer without writing code.

This is the "System 1" (fast, intuitive) approach described by Chollet
& Knoop, complementing the "System 2" (deliberate, code synthesis)
pipeline in the main solver.

Usage:
    from loopagi.arc.transducer import transduce
    result = transduce(bridge, task, train_pairs)
    if result.valid:
        print("Transduction succeeded!")
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import ArcTask
    from loopagi.arc.llm_bridge import LLMBridge

logger = logging.getLogger(__name__)

# Type alias
Grid = list[list[int]]
TrainPair = tuple[Grid, Grid]


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass
class TransductionResult:
    """Result of a direct grid transduction attempt."""

    predicted_grid: Grid | None
    """The predicted output grid, or None if parsing failed."""

    similarity: float
    """Average similarity against training outputs (0.0–1.0)."""

    valid: bool
    """Whether transduction passed training verification."""

    raw_response: str = ""
    """The raw LLM response for debugging."""

    error: str = ""
    """Error message if transduction failed."""


# ---------------------------------------------------------------------------
# Prompt formatting
# ---------------------------------------------------------------------------

_TRANSDUCTION_PROMPT = """\
You are solving an ARC-AGI puzzle. Study the input-output pairs below, \
then predict the output for the test input.

{pairs}

Test Input:
{test_input}

Reply with ONLY the output grid as a JSON array of arrays (e.g. [[1,2],[3,4]]).
Do NOT include any explanation, code, or markdown fences."""


def format_transduction_prompt(
    train_pairs: list[TrainPair],
    test_input: Grid,
) -> str:
    """Format a compact transduction prompt showing all I/O pairs."""
    parts: list[str] = []
    for i, (inp, out) in enumerate(train_pairs, 1):
        parts.append(f"Pair {i}:")
        parts.append(f"  Input:  {_compact_grid(inp)}")
        parts.append(f"  Output: {_compact_grid(out)}")
    pairs_text = "\n".join(parts)
    return _TRANSDUCTION_PROMPT.format(
        pairs=pairs_text,
        test_input=_compact_grid(test_input),
    )


def _compact_grid(grid: Grid) -> str:
    """Format a grid as a compact JSON array."""
    return json.dumps(grid, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def parse_grid_from_response(response: str) -> Grid | None:
    """Extract a 2-D integer grid from an LLM response.

    Handles:
    - Raw JSON arrays
    - Markdown-fenced JSON
    - Whitespace / newlines in the array
    - Extra text before/after the array

    Returns None if no valid grid can be extracted.
    """
    if not response or not response.strip():
        return None

    text = response.strip()

    # Strip markdown fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Try to find a JSON array in the text
    # Look for the outermost [[...]]
    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        return None

    candidate = match.group(0)

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        # Try fixing common issues: trailing commas
        cleaned = re.sub(r",\s*]", "]", candidate)
        cleaned = re.sub(r",\s*}", "}", cleaned)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: row-by-row extraction for large/truncated grids
            return _parse_rows_fallback(text)

    return _validate_grid(parsed)


def _parse_rows_fallback(text: str) -> Grid | None:
    """Extract grid rows individually when full JSON parsing fails."""
    row_pattern = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")
    rows: Grid = []
    for m in row_pattern.finditer(text):
        try:
            vals = [int(v.strip()) for v in m.group(1).split(",")]
            rows.append(vals)
        except ValueError:
            continue
    if len(rows) < 2:
        return None
    return _validate_grid(rows)


def _validate_grid(parsed: object) -> Grid | None:
    """Validate and convert parsed data to a rectangular integer grid."""
    if not isinstance(parsed, list) or not parsed:
        return None
    grid: Grid = []
    for row in parsed:
        if not isinstance(row, list):
            return None
        int_row: list[int] = []
        for val in row:
            if not isinstance(val, (int, float)):
                return None
            int_row.append(int(val))
        grid.append(int_row)
    if not grid:
        return None
    col_count = len(grid[0])
    if any(len(row) != col_count for row in grid):
        return None
    return grid


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def _grid_similarity(expected: Grid, actual: Grid) -> float:
    """Compute cell-level similarity between two grids."""
    if not expected or not actual:
        return 0.0
    exp_rows, exp_cols = len(expected), len(expected[0])
    act_rows = len(actual)
    act_cols = len(actual[0]) if actual else 0

    if exp_rows != act_rows or exp_cols != act_cols:
        return 0.0  # Shape mismatch = fail for transduction

    total = exp_rows * exp_cols
    matching = sum(
        1 for r in range(exp_rows)
        for c in range(exp_cols)
        if expected[r][c] == actual[r][c]
    )
    return matching / total if total else 0.0


def validate_transduction(
    predicted_grid: Grid,
    train_pairs: list[TrainPair],
) -> float:
    """Validate a transduced grid against training pairs.

    For transduction, we can't directly validate against training
    outputs because the predicted grid is for the *test* input.
    Instead, we check dimensional consistency: does the predicted
    grid have the expected output dimensions based on training?

    Returns a confidence score (0.0–1.0).
    """
    if not train_pairs or not predicted_grid:
        return 0.0

    # Check output dimensions match training pattern
    train_out_shapes = {(len(out), len(out[0])) for _, out in train_pairs}
    pred_shape = (len(predicted_grid), len(predicted_grid[0]))

    # If all training outputs have the same shape, predicted should too
    if len(train_out_shapes) == 1:
        expected_shape = train_out_shapes.pop()
        if pred_shape == expected_shape:
            return 1.0
        return 0.0

    # Multiple output shapes — check if predicted matches any
    if pred_shape in train_out_shapes:
        return 0.8

    return 0.3  # Unknown shape, low confidence


# ---------------------------------------------------------------------------
# Main transduction function
# ---------------------------------------------------------------------------


def transduce(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
    test_input: Grid,
    temperature: float = 0.0,
) -> TransductionResult:
    """Ask the LLM to directly predict the test output grid.

    Args:
        bridge: LLM bridge for inference.
        train_pairs: Training (input, output) pairs.
        test_input: The test input grid.
        temperature: LLM sampling temperature (0.0 = deterministic).

    Returns:
        TransductionResult with the predicted grid and confidence.
    """
    prompt = format_transduction_prompt(train_pairs, test_input)

    try:
        response = bridge.call(prompt, temperature=temperature)
    except Exception as e:
        logger.warning("Transduction LLM call failed: %s", e)
        return TransductionResult(
            predicted_grid=None,
            similarity=0.0,
            valid=False,
            error=str(e),
        )

    grid = parse_grid_from_response(response)
    if grid is None:
        logger.debug("Transduction: failed to parse grid from response")
        return TransductionResult(
            predicted_grid=None,
            similarity=0.0,
            valid=False,
            raw_response=response,
            error="Could not parse grid from LLM response",
        )

    confidence = validate_transduction(grid, train_pairs)
    valid = confidence >= 0.8

    logger.info(
        "Transduction: parsed %dx%d grid, confidence=%.2f, valid=%s",
        len(grid), len(grid[0]) if grid else 0, confidence, valid,
    )

    return TransductionResult(
        predicted_grid=grid,
        similarity=confidence,
        valid=valid,
        raw_response=response,
    )


# ---------------------------------------------------------------------------
# Training-verified transduction
# ---------------------------------------------------------------------------


def transduce_with_verification(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
    test_input: Grid,
    temperature: float = 0.0,
) -> TransductionResult:
    """Transduce with training pair verification.

    Before predicting the test output, verifies the LLM can correctly
    transduce each training input to its known output. Only proceeds
    to the test input if all training pairs match 100%.

    This adds N extra LLM calls (one per training pair), but dramatically
    increases confidence in the test prediction.

    Args:
        bridge: LLM bridge for inference.
        train_pairs: Training (input, output) pairs.
        test_input: The test input grid.
        temperature: LLM sampling temperature.

    Returns:
        TransductionResult with the predicted grid and confidence.
    """
    for i, (train_in, train_out) in enumerate(train_pairs):
        train_result = transduce(bridge, train_pairs, train_in, temperature)
        if not train_result.valid or train_result.predicted_grid is None:
            logger.debug(
                "Training verification failed on pair %d/%d: invalid result",
                i + 1, len(train_pairs),
            )
            return TransductionResult(
                predicted_grid=None,
                similarity=0.0,
                valid=False,
                error=f"Training verification failed on pair {i + 1}",
            )
        sim = _grid_similarity(train_out, train_result.predicted_grid)
        if sim < 1.0:
            logger.debug(
                "Training verification failed on pair %d/%d: sim=%.1f%%",
                i + 1, len(train_pairs), sim * 100,
            )
            return TransductionResult(
                predicted_grid=None,
                similarity=sim,
                valid=False,
                error=f"Training verification: pair {i + 1} sim={sim:.1%}",
            )

    logger.info(
        "Training verification passed (%d pairs), predicting test output",
        len(train_pairs),
    )
    return transduce(bridge, train_pairs, test_input, temperature)
