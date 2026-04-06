"""Iterative transduction refinement for ARC-AGI tasks (Phase Y).

Multi-round transduction with cell-level feedback and differential
formatting for near-identity tasks. Builds on the base transducer.

Usage:
    from loopagi.arc.transducer_refine import transduce_with_refinement
    result = transduce_with_refinement(bridge, train_pairs, test_input)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.llm_bridge import LLMBridge

from loopagi.arc.transducer import (
    Grid,
    TrainPair,
    TransductionResult,
    _compact_grid,
    _grid_similarity,
    format_transduction_prompt,
    parse_grid_from_response,
    validate_transduction,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_REFINEMENT_PROMPT = """\
You are solving an ARC-AGI puzzle. Your previous prediction was close but had errors.

{pairs}

Test Input:
{test_input}

Your previous prediction:
{previous}

Wrong cells (row,col): actual -> expected:
{wrong_cells}

Fix ONLY the wrong cells. Reply with the COMPLETE corrected output grid
as a JSON array of arrays. Do NOT include explanation or code."""

_DIFF_PROMPT = """\
You are solving an ARC-AGI puzzle where most cells stay the same.

{pairs_diff}

Test Input:
{test_input}

Only a few cells change between input and output. Predict the output grid.
Reply with ONLY the output grid as a JSON array of arrays."""


# ---------------------------------------------------------------------------
# Differential formatting
# ---------------------------------------------------------------------------


def should_use_diff_format(train_pairs: list[TrainPair]) -> bool:
    """Check if differential formatting is appropriate (< 15% cells change)."""
    for inp, out in train_pairs:
        if len(inp) != len(out) or not inp or len(inp[0]) != len(out[0]):
            return False
        total = len(inp) * len(inp[0])
        changed = sum(
            1 for r in range(len(inp)) for c in range(len(inp[0]))
            if inp[r][c] != out[r][c]
        )
        if changed >= total * 0.15:
            return False
    return True


def format_diff_pairs(train_pairs: list[TrainPair]) -> str:
    """Format training pairs showing only changed cells."""
    parts: list[str] = []
    for i, (inp, out) in enumerate(train_pairs, 1):
        if (
            len(inp) == len(out) and inp and len(inp[0]) == len(out[0])
        ):
            total = len(inp) * len(inp[0])
            changed = sum(
                1 for r in range(len(inp)) for c in range(len(inp[0]))
                if inp[r][c] != out[r][c]
            )
            if changed < total * 0.15:
                parts.append(
                    f"Pair {i} ({len(inp)}x{len(inp[0])}, {changed} cells change):"
                )
                parts.append(f"  Input: {_compact_grid(inp)}")
                parts.append("  Changed cells:")
                for r in range(len(inp)):
                    for c in range(len(inp[0])):
                        if inp[r][c] != out[r][c]:
                            parts.append(f"    ({r},{c}): {inp[r][c]} -> {out[r][c]}")
                continue
        parts.append(f"Pair {i}:")
        parts.append(f"  Input:  {_compact_grid(inp)}")
        parts.append(f"  Output: {_compact_grid(out)}")
    return "\n".join(parts)


def format_wrong_cells(expected: Grid, actual: Grid) -> str:
    """Format wrong cells as (row,col): actual -> expected."""
    lines: list[str] = []
    for r in range(min(len(expected), len(actual))):
        for c in range(min(len(expected[r]), len(actual[r]))):
            if expected[r][c] != actual[r][c]:
                lines.append(f"  ({r},{c}): {actual[r][c]} -> {expected[r][c]}")
    return "\n".join(lines) if lines else "(none)"


# ---------------------------------------------------------------------------
# Iterative refinement
# ---------------------------------------------------------------------------


def transduce_with_refinement(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
    test_input: Grid,
    max_rounds: int = 3,
) -> TransductionResult:
    """Iterative transduction with cell-level feedback.

    Round 1: Standard transduction (differential format if applicable).
    Rounds 2+: Show LLM wrong cells from training, ask to fix.
    """
    use_diff = should_use_diff_format(train_pairs)

    # Round 1
    if use_diff:
        prompt = _DIFF_PROMPT.format(
            pairs_diff=format_diff_pairs(train_pairs),
            test_input=_compact_grid(test_input),
        )
    else:
        prompt = format_transduction_prompt(train_pairs, test_input)

    try:
        response = bridge.call(prompt, temperature=0.0)
    except Exception:
        return TransductionResult(predicted_grid=None, similarity=0.0, valid=False)

    grid = parse_grid_from_response(response)
    if grid is None:
        return TransductionResult(predicted_grid=None, similarity=0.0, valid=False)

    best_grid = grid
    best_sim = _check_train_accuracy(bridge, train_pairs)

    # Refinement rounds
    for round_num in range(1, max_rounds):
        if best_sim >= 1.0:
            break

        wrong_text, worst_sim = _find_worst_training_errors(bridge, train_pairs)
        if not wrong_text or worst_sim >= 1.0:
            break

        pairs_text = (
            format_diff_pairs(train_pairs) if use_diff
            else "\n".join(
                f"Pair {i}: {_compact_grid(inp)} -> {_compact_grid(out)}"
                for i, (inp, out) in enumerate(train_pairs, 1)
            )
        )

        prompt = _REFINEMENT_PROMPT.format(
            pairs=pairs_text,
            test_input=_compact_grid(test_input),
            previous=_compact_grid(best_grid),
            wrong_cells=wrong_text,
        )

        try:
            response = bridge.call(prompt, temperature=0.0)
        except Exception:
            break

        refined = parse_grid_from_response(response)
        if refined is None:
            break

        refined_sim = _check_train_accuracy(bridge, train_pairs)
        if refined_sim > best_sim:
            best_grid = refined
            best_sim = refined_sim
            logger.info("Refinement round %d: improved to %.1f%%", round_num, best_sim * 100)
        else:
            break

    confidence = validate_transduction(best_grid, train_pairs)
    return TransductionResult(
        predicted_grid=best_grid,
        similarity=best_sim,
        valid=confidence >= 0.8 and best_sim >= 1.0,
    )


def _check_train_accuracy(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
) -> float:
    """Check transduction accuracy on training pairs."""
    if not train_pairs:
        return 0.0
    total_sim = 0.0
    for train_in, train_out in train_pairs:
        prompt = format_transduction_prompt(train_pairs, train_in)
        try:
            response = bridge.call(prompt, temperature=0.0)
        except Exception:
            return 0.0
        predicted = parse_grid_from_response(response)
        if predicted is None:
            return 0.0
        total_sim += _grid_similarity(train_out, predicted)
    return total_sim / len(train_pairs)


def _find_worst_training_errors(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
) -> tuple[str, float]:
    """Find worst training pair errors for refinement feedback."""
    worst_sim = 1.0
    wrong_text = ""
    for train_in, train_out in train_pairs:
        prompt = format_transduction_prompt(train_pairs, train_in)
        try:
            response = bridge.call(prompt, temperature=0.0)
        except Exception:
            continue
        predicted = parse_grid_from_response(response)
        if predicted is None:
            continue
        sim = _grid_similarity(train_out, predicted)
        if sim < worst_sim:
            worst_sim = sim
            wrong_text = format_wrong_cells(train_out, predicted)
    return wrong_text, worst_sim
