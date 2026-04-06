"""Diff-based iterative refinement for near-miss ARC transductions.

When D4 voting or relaxed transduction produces a grid with high similarity
but a few wrong cells, this module shows the LLM an ASCII diff of the
predicted vs. expected grid and asks it to correct the output. This is
inspired by Jeremy Berman's V2 approach where explicit diff feedback
dramatically improves correction rates.

The key insight: LLMs are much better at fixing specific highlighted errors
than at getting everything right in one shot.

Usage:
    from loopagi.arc.diff_refiner import refine_with_diff
    result = refine_with_diff(bridge, train_pairs, test_input, prediction)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.llm_bridge import LLMBridge

logger = logging.getLogger(__name__)

# Type aliases
Grid = list[list[int]]
TrainPair = tuple[Grid, Grid]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DiffCell:
    """A single cell difference between two grids."""

    row: int
    col: int
    expected: int
    actual: int


@dataclass
class GridDiff:
    """Diff between expected and actual grids."""

    wrong_cells: list[DiffCell] = field(default_factory=list)
    total_cells: int = 0
    similarity: float = 0.0

    @property
    def n_wrong(self) -> int:
        return len(self.wrong_cells)

    @property
    def n_correct(self) -> int:
        return self.total_cells - self.n_wrong


@dataclass
class RefineResult:
    """Result of diff-based refinement."""

    grid: Grid | None
    similarity: float
    rounds_used: int
    improved: bool
    method: str = "diff_refine"


# ---------------------------------------------------------------------------
# Diff computation
# ---------------------------------------------------------------------------

def compute_grid_diff(expected: Grid, actual: Grid) -> GridDiff:
    """Compute cell-level diff between expected and actual grids.

    Returns GridDiff with list of wrong cells and similarity score.
    Returns empty diff if shapes don't match.
    """
    if not expected or not actual:
        return GridDiff()
    if len(expected) != len(actual):
        return GridDiff()
    if not expected[0] or not actual[0]:
        return GridDiff()
    if len(expected[0]) != len(actual[0]):
        return GridDiff()

    rows, cols = len(expected), len(expected[0])
    total = rows * cols
    wrong: list[DiffCell] = []

    for r in range(rows):
        for c in range(cols):
            if expected[r][c] != actual[r][c]:
                wrong.append(DiffCell(
                    row=r, col=c,
                    expected=expected[r][c],
                    actual=actual[r][c],
                ))

    similarity = (total - len(wrong)) / total if total > 0 else 0.0
    return GridDiff(wrong_cells=wrong, total_cells=total, similarity=similarity)


def format_ascii_diff(expected: Grid, actual: Grid) -> str:
    """Format a visual ASCII diff highlighting wrong cells.

    Correct cells show '.' and wrong cells show 'X' with details.
    This is the format shown to the LLM for correction.

    Example:
        . . . .
        . X . .  ← row 1, col 1: got 7, expected 4
        . . . .
    """
    if not expected or not actual:
        return "(empty grids)"
    if len(expected) != len(actual):
        return f"(shape mismatch: expected {len(expected)} rows, got {len(actual)} rows)"

    rows = len(expected)
    cols = len(expected[0]) if expected else 0
    if cols == 0 or len(actual[0]) != cols:
        return "(column mismatch)"

    lines: list[str] = []
    for r in range(rows):
        row_chars: list[str] = []
        annotations: list[str] = []
        for c in range(cols):
            if expected[r][c] == actual[r][c]:
                row_chars.append(".")
            else:
                row_chars.append("X")
                annotations.append(
                    f"({r},{c}): got {actual[r][c]}, expected {expected[r][c]}"
                )
        line = " ".join(row_chars)
        if annotations:
            line += "  ← " + "; ".join(annotations)
        lines.append(line)

    return "\n".join(lines)


def format_wrong_cells_summary(diff: GridDiff) -> str:
    """Format wrong cells as a concise summary for prompts."""
    if not diff.wrong_cells:
        return "All cells correct."
    parts = [f"{diff.n_wrong} wrong cell(s) out of {diff.total_cells}:"]
    for wc in diff.wrong_cells[:20]:  # Limit to 20 to avoid prompt bloat
        parts.append(f"  row {wc.row}, col {wc.col}: got {wc.actual}, should be {wc.expected}")
    if diff.n_wrong > 20:
        parts.append(f"  ... and {diff.n_wrong - 20} more")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

def _compact_grid(grid: Grid) -> str:
    """Compact grid representation."""
    import json
    return json.dumps(grid, separators=(",", ":"))


_REFINE_PROMPT = """\
You are solving an ARC-AGI puzzle. Your previous prediction was close but had errors.

Training examples:
{pairs}

Test Input:
{test_input}

Your previous prediction:
{prediction}

Diff (X = wrong cell):
{diff}

{wrong_summary}

Fix the wrong cells. Keep all correct cells (marked '.') unchanged.
Reply with ONLY the complete corrected output grid as a JSON array of arrays."""


_REFINE_WITH_TRAINING_PROMPT = """\
You are solving an ARC-AGI puzzle. I will show you where the model makes errors \
on training examples to help you understand the pattern better.

Training examples:
{pairs}

Training error analysis:
{training_errors}

Test Input:
{test_input}

Your previous prediction for the test:
{prediction}

Diff on test prediction (X = wrong cell, based on pattern analysis):
{diff}

{wrong_summary}

Use the training error analysis to understand what the model gets wrong, \
then fix the test prediction. Keep all correct cells unchanged.
Reply with ONLY the complete corrected output grid as a JSON array of arrays."""


# ---------------------------------------------------------------------------
# Core refinement
# ---------------------------------------------------------------------------

def _format_pairs(train_pairs: list[TrainPair]) -> str:
    """Format training pairs for prompt."""
    parts: list[str] = []
    for i, (inp, out) in enumerate(train_pairs, 1):
        parts.append(f"Pair {i}:\n  Input:  {_compact_grid(inp)}\n  Output: {_compact_grid(out)}")
    return "\n".join(parts)


def _analyze_training_errors(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
) -> tuple[str, float]:
    """Transduce each training input and report errors.

    Returns (error_text, worst_similarity).
    """
    from loopagi.arc.transducer import transduce, _grid_similarity

    error_parts: list[str] = []
    worst_sim = 1.0

    for i, (train_in, train_out) in enumerate(train_pairs):
        result = transduce(bridge, train_pairs, train_in, temperature=0.0)
        if result.predicted_grid is None:
            error_parts.append(f"Pair {i+1}: transduction failed entirely")
            worst_sim = 0.0
            continue

        diff = compute_grid_diff(train_out, result.predicted_grid)
        if diff.n_wrong > 0:
            error_parts.append(
                f"Pair {i+1}: {diff.n_wrong} wrong cells — "
                + ", ".join(
                    f"({wc.row},{wc.col}): predicted {wc.actual} should be {wc.expected}"
                    for wc in diff.wrong_cells[:10]
                )
            )
        else:
            error_parts.append(f"Pair {i+1}: all correct")

        if diff.similarity < worst_sim:
            worst_sim = diff.similarity

    return "\n".join(error_parts), worst_sim


def refine_with_diff(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
    test_input: Grid,
    prediction: Grid,
    max_rounds: int = 3,
    use_training_errors: bool = True,
) -> RefineResult:
    """Iteratively refine a near-miss prediction using training-guided diff feedback.

    V9 rewrite: instead of diffing against a fresh prediction (circular),
    always use training errors as the ground truth signal. Each round:
    1. Analyze training errors (where model gets training pairs wrong)
    2. Show the LLM those errors + the current test prediction
    3. Ask the LLM to fix the test prediction based on error patterns
    4. Score via training consistency to check improvement
    """
    from loopagi.arc.transducer import _grid_similarity, parse_grid_from_response

    if bridge.is_mock:
        return RefineResult(grid=prediction, similarity=0.0, rounds_used=0, improved=False)

    best_grid = prediction
    best_sim = _score_via_training(bridge, train_pairs, prediction, test_input)
    pairs_text = _format_pairs(train_pairs)
    rounds_used = 0

    for round_num in range(max_rounds):
        rounds_used = round_num + 1
        # Analyze training errors each round (model may respond differently)
        training_error_text, worst_train_sim = _analyze_training_errors(
            bridge, train_pairs)

        if worst_train_sim >= 1.0:
            # Model gets all training pairs perfect — high confidence in prediction
            logger.info("Diff refiner round %d: all training correct, high confidence",
                        rounds_used)
            break

        if not training_error_text or "all correct" in training_error_text.lower():
            break

        # Generate a second test prediction at different temp for diff context
        from loopagi.arc.transducer import transduce
        fresh = transduce(
            bridge, train_pairs, test_input,
            temperature=0.15 * (round_num + 1))
        diff_text = "(no diff available)"
        wrong_text = ""
        if fresh.predicted_grid is not None:
            diff = compute_grid_diff(best_grid, fresh.predicted_grid)
            if diff.n_wrong > 0:
                diff_text = format_ascii_diff(best_grid, fresh.predicted_grid)
                wrong_text = format_wrong_cells_summary(diff)

        # Always use training-guided prompt (key V9 fix)
        prompt = _REFINE_WITH_TRAINING_PROMPT.format(
            pairs=pairs_text,
            training_errors=training_error_text,
            test_input=_compact_grid(test_input),
            prediction=_compact_grid(best_grid),
            diff=diff_text,
            wrong_summary=wrong_text,
        )

        try:
            response = bridge.call(prompt, temperature=0.0)
        except Exception as e:
            logger.warning("Diff refiner round %d: LLM call failed: %s", rounds_used, e)
            break

        refined = parse_grid_from_response(response)
        if refined is None:
            logger.debug("Diff refiner round %d: could not parse grid", rounds_used)
            break

        train_sim = _score_via_training(bridge, train_pairs, refined, test_input)
        if train_sim > best_sim:
            logger.info("Diff refiner round %d: improved %.1f%% -> %.1f%%",
                        rounds_used, best_sim * 100, train_sim * 100)
            best_grid = refined
            best_sim = train_sim
        else:
            logger.debug("Diff refiner round %d: no improvement (%.1f%%)",
                         rounds_used, train_sim * 100)

    return RefineResult(
        grid=best_grid, similarity=best_sim, rounds_used=rounds_used,
        improved=best_grid is not prediction,
    )


def _score_via_training(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
    candidate: Grid,
    test_input: Grid,
) -> float:
    """Score a test prediction via structural checks + training accuracy.

    Returns 0.0 for invalid candidates, otherwise the average training
    similarity (how well the model reproduces training outputs when the
    candidate is structurally valid).
    """
    from loopagi.arc.symbolic_filter import extract_priors, score_candidate

    priors = extract_priors(train_pairs)
    sym = score_candidate(candidate, test_input, priors)
    if sym < 0.3:
        return 0.0

    # Compute actual training accuracy
    from loopagi.arc.transducer import transduce, _grid_similarity
    sims: list[float] = []
    for train_in, train_out in train_pairs:
        result = transduce(bridge, train_pairs, train_in, temperature=0.0)
        if result.predicted_grid is not None:
            sims.append(_grid_similarity(train_out, result.predicted_grid))
        else:
            sims.append(0.0)

    avg_train = sum(sims) / len(sims) if sims else 0.0
    # Combine: structural score (20%) + training accuracy (80%)
    return 0.2 * sym + 0.8 * avg_train


def try_diff_refine(
    solve_dict: dict,
    task: object,
    bridge: LLMBridge,
    min_similarity: float = 0.85,
) -> dict:
    """Try diff-based refinement on a near-miss task.

    Runs after D4 voting or relaxed transduction produces a high-similarity
    but imperfect result. Modifies solve_dict in-place if refinement improves.

    Args:
        solve_dict: Current solve state with result and predictions.
        task: ARC task with .train and .test attributes.
        bridge: LLM bridge for inference.
        min_similarity: Minimum similarity to attempt refinement.

    Returns:
        Updated solve_dict.
    """
    result = solve_dict["result"]
    if result.solved:
        return solve_dict
    if result.best_similarity < min_similarity:
        return solve_dict
    if not result.predictions:
        return solve_dict

    train_pairs: list[TrainPair] = [(p.input, p.output) for p in task.train]

    logger.info(
        "[%s] Diff refiner: attempting refinement (sim=%.1f%%)",
        task.task_id, result.best_similarity * 100,
    )

    improved_predictions: list[Grid] = []
    any_improved = False

    for i, test in enumerate(task.test):
        # Get current prediction for this test
        pred = result.predictions[i] if i < len(result.predictions) else None
        if pred is None:
            improved_predictions.append(test.input)  # Fallback
            continue

        # Handle nested prediction format (list of candidates)
        current_pred = pred[0] if isinstance(pred, list) and pred and isinstance(pred[0], list) and pred[0] and isinstance(pred[0][0], list) else pred

        refine_result = refine_with_diff(
            bridge, train_pairs, test.input, current_pred,
            max_rounds=2, use_training_errors=True,
        )

        if refine_result.improved and refine_result.grid is not None:
            improved_predictions.append(refine_result.grid)
            any_improved = True
            logger.info(
                "[%s] Diff refiner: test %d improved",
                task.task_id, i + 1,
            )
        else:
            improved_predictions.append(current_pred)

    if any_improved:
        # Check if the refined predictions pass symbolic filters
        from loopagi.arc.symbolic_filter import extract_priors, filter_candidate
        priors = extract_priors(train_pairs)
        all_valid = all(
            filter_candidate(pred, test.input, priors)
            for pred, test in zip(improved_predictions, task.test)
        )
        if all_valid:
            result.predictions = improved_predictions
            logger.info("[%s] Diff refiner: accepted refined predictions", task.task_id)
        else:
            logger.info("[%s] Diff refiner: rejected — failed symbolic filter", task.task_id)

    return solve_dict
