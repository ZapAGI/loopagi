"""Grid traversal representations for ARC-AGI tasks.

Different traversal orders expose different spatial patterns to the LLM.
NVARC ablation shows traversals are worth +6 percentage points.

Methods: row, column, snake, diagonal, spiral.  Each serializes a grid
to a 1-D token sequence and reconstructs it back.

Usage::

    tokens = traverse(grid, "column")
    grid_back = reconstruct(tokens, rows, cols, "column")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.llm_bridge import LLMBridge

logger = logging.getLogger(__name__)

# Type aliases
Grid = list[list[int]]
TrainPair = tuple[Grid, Grid]

TRAVERSAL_METHODS = ("row", "column", "snake", "diagonal", "spiral")


# ---------------------------------------------------------------------------
# Traversal functions: Grid -> flat token list
# ---------------------------------------------------------------------------


def traverse_row(grid: Grid) -> list[int]:
    """Standard row-by-row left-to-right traversal."""
    return [v for row in grid for v in row]


def traverse_column(grid: Grid) -> list[int]:
    """Column-by-column top-to-bottom traversal."""
    if not grid or not grid[0]:
        return []
    rows, cols = len(grid), len(grid[0])
    return [grid[r][c] for c in range(cols) for r in range(rows)]


def traverse_snake(grid: Grid) -> list[int]:
    """Snake traversal: even rows L->R, odd rows R->L."""
    tokens: list[int] = []
    for i, row in enumerate(grid):
        tokens.extend(row if i % 2 == 0 else reversed(row))
    return tokens


def traverse_diagonal(grid: Grid) -> list[int]:
    """Diagonal traversal: cells grouped by (row + col) value."""
    if not grid or not grid[0]:
        return []
    rows, cols = len(grid), len(grid[0])
    tokens: list[int] = []
    for d in range(rows + cols - 1):
        r_start = max(0, d - cols + 1)
        r_end = min(d, rows - 1)
        for r in range(r_start, r_end + 1):
            c = d - r
            tokens.append(grid[r][c])
    return tokens


def traverse_spiral(grid: Grid) -> list[int]:
    """Spiral traversal: outside-in clockwise starting from top-left."""
    if not grid or not grid[0]:
        return []
    rows, cols = len(grid), len(grid[0])
    tokens: list[int] = []
    top, bottom, left, right = 0, rows - 1, 0, cols - 1

    while top <= bottom and left <= right:
        # Right across top
        for c in range(left, right + 1):
            tokens.append(grid[top][c])
        top += 1
        # Down right side
        for r in range(top, bottom + 1):
            tokens.append(grid[r][right])
        right -= 1
        # Left across bottom
        if top <= bottom:
            for c in range(right, left - 1, -1):
                tokens.append(grid[bottom][c])
            bottom -= 1
        # Up left side
        if left <= right:
            for r in range(bottom, top - 1, -1):
                tokens.append(grid[r][left])
            left += 1

    return tokens


# ---------------------------------------------------------------------------
# Reconstruction: flat token list -> Grid
# ---------------------------------------------------------------------------


def reconstruct_row(tokens: list[int], rows: int, cols: int) -> Grid:
    """Reconstruct grid from row-by-row traversal."""
    return [list(tokens[r * cols : (r + 1) * cols]) for r in range(rows)]


def reconstruct_column(tokens: list[int], rows: int, cols: int) -> Grid:
    """Reconstruct grid from column-by-column traversal."""
    grid: Grid = [[0] * cols for _ in range(rows)]
    idx = 0
    for c in range(cols):
        for r in range(rows):
            grid[r][c] = tokens[idx]
            idx += 1
    return grid


def reconstruct_snake(tokens: list[int], rows: int, cols: int) -> Grid:
    """Reconstruct grid from snake traversal."""
    grid: Grid = []
    for r in range(rows):
        start = r * cols
        row_vals = list(tokens[start : start + cols])
        if r % 2 == 1:
            row_vals.reverse()
        grid.append(row_vals)
    return grid


def reconstruct_diagonal(tokens: list[int], rows: int, cols: int) -> Grid:
    """Reconstruct grid from diagonal traversal."""
    grid: Grid = [[0] * cols for _ in range(rows)]
    idx = 0
    for d in range(rows + cols - 1):
        r_start = max(0, d - cols + 1)
        r_end = min(d, rows - 1)
        for r in range(r_start, r_end + 1):
            c = d - r
            grid[r][c] = tokens[idx]
            idx += 1
    return grid


def reconstruct_spiral(tokens: list[int], rows: int, cols: int) -> Grid:
    """Reconstruct grid from spiral traversal."""
    grid: Grid = [[0] * cols for _ in range(rows)]
    top, bottom, left, right = 0, rows - 1, 0, cols - 1
    idx = 0

    while top <= bottom and left <= right:
        for c in range(left, right + 1):
            grid[top][c] = tokens[idx]
            idx += 1
        top += 1
        for r in range(top, bottom + 1):
            grid[r][right] = tokens[idx]
            idx += 1
        right -= 1
        if top <= bottom:
            for c in range(right, left - 1, -1):
                grid[bottom][c] = tokens[idx]
                idx += 1
            bottom -= 1
        if left <= right:
            for r in range(bottom, top - 1, -1):
                grid[r][left] = tokens[idx]
                idx += 1
            left += 1

    return grid


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_TRAVERSE_FNS = {
    "row": traverse_row,
    "column": traverse_column,
    "snake": traverse_snake,
    "diagonal": traverse_diagonal,
    "spiral": traverse_spiral,
}

_RECONSTRUCT_FNS = {
    "row": reconstruct_row,
    "column": reconstruct_column,
    "snake": reconstruct_snake,
    "diagonal": reconstruct_diagonal,
    "spiral": reconstruct_spiral,
}


def traverse(grid: Grid, method: str = "row") -> list[int]:
    """Serialize a grid using the given traversal method."""
    fn = _TRAVERSE_FNS.get(method)
    if fn is None:
        raise ValueError(f"Unknown traversal method: {method!r}. "
                         f"Choose from {TRAVERSAL_METHODS}")
    return fn(grid)


def reconstruct(tokens: list[int], rows: int, cols: int, method: str = "row") -> Grid:
    """Reconstruct a grid from a flat token sequence."""
    expected = rows * cols
    if len(tokens) != expected:
        raise ValueError(
            f"Token count {len(tokens)} != expected {expected} "
            f"({rows}×{cols})"
        )
    fn = _RECONSTRUCT_FNS.get(method)
    if fn is None:
        raise ValueError(f"Unknown traversal method: {method!r}. "
                         f"Choose from {TRAVERSAL_METHODS}")
    return fn(tokens, rows, cols)


# ---------------------------------------------------------------------------
# Prompt formatting
# ---------------------------------------------------------------------------


def format_traversal_grid(grid: Grid, method: str = "row") -> str:
    """Format a grid for LLM prompts using a specific traversal."""
    if method == "row":
        return json.dumps(grid, separators=(",", ":"))

    tokens = traverse(grid, method)
    rows, cols = len(grid), len(grid[0]) if grid else 0
    return f"[{method} {rows}x{cols}] {json.dumps(tokens, separators=(',', ':'))}"


def format_traversal_prompt(
    train_pairs: list[TrainPair],
    test_input: Grid,
    method: str = "row",
) -> str:
    """Build a transduction prompt using a specific grid traversal."""
    rows_out = len(train_pairs[0][1]) if train_pairs else 0
    cols_out = len(train_pairs[0][1][0]) if train_pairs and train_pairs[0][1] else 0

    parts: list[str] = []
    if method != "row":
        parts.append(
            f"Grids are encoded using {method} traversal. "
            f"The format is [{method} RxC] followed by the flat token list."
        )
        parts.append("")

    parts.append(
        "You are solving an ARC-AGI puzzle. Study the input-output pairs "
        "below, then predict the output for the test input."
    )
    parts.append("")

    for i, (inp, out) in enumerate(train_pairs, 1):
        parts.append(f"Pair {i}:")
        parts.append(f"  Input:  {format_traversal_grid(inp, method)}")
        parts.append(f"  Output: {format_traversal_grid(out, method)}")

    parts.append("")
    parts.append(f"Test Input:")
    parts.append(f"  {format_traversal_grid(test_input, method)}")
    parts.append("")

    if method == "row":
        parts.append(
            "Reply with ONLY the output grid as a JSON array of arrays "
            "(e.g. [[1,2],[3,4]])."
        )
    else:
        parts.append(
            f"Reply with ONLY the output as a flat JSON array of integers "
            f"in {method} traversal order (same format as above)."
        )
    parts.append("Do NOT include any explanation, code, or markdown fences.")

    return "\n".join(parts)


@dataclass
class TraversalTransductionResult:
    """Result of multi-traversal transduction."""

    grid: Grid | None
    agreement: float
    n_valid: int
    n_total: int
    method: str = "traversal_vote"
    per_traversal: list[dict] = field(default_factory=list)


def _parse_traversal_response(
    response: str, method: str, rows: int, cols: int,
) -> Grid | None:
    """Parse an LLM response for a traversal-encoded grid."""
    from loopagi.arc.transducer import parse_grid_from_response

    if method == "row":
        return parse_grid_from_response(response)

    # Try to extract a flat JSON array from the response
    import re

    text = response.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Remove traversal prefix if echoed back
    text = re.sub(r"\[\w+\s+\d+x\d+\]\s*", "", text)

    match = re.search(r"\[[\d,\s]+\]", text)
    if not match:
        return parse_grid_from_response(response)

    try:
        tokens = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

    if not isinstance(tokens, list):
        return None

    expected = rows * cols
    if len(tokens) != expected:
        # Try standard grid parser as fallback (LLM may ignore format)
        return parse_grid_from_response(response)

    try:
        int_tokens = [int(t) for t in tokens]
        return reconstruct(int_tokens, rows, cols, method)
    except (ValueError, TypeError):
        return None


def multi_traversal_transduce(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
    test_input: Grid,
    methods: tuple[str, ...] | None = None,
) -> TraversalTransductionResult:
    """Run transduction using multiple grid traversals and vote."""
    from loopagi.arc.augmentation_voter import _compute_agreement, _majority_vote_grid

    if methods is None:
        methods = TRAVERSAL_METHODS

    # Determine expected output dimensions from training
    if not train_pairs:
        return TraversalTransductionResult(
            grid=None, agreement=0.0, n_valid=0, n_total=0,
        )

    out_rows = len(train_pairs[0][1])
    out_cols = len(train_pairs[0][1][0]) if train_pairs[0][1] else 0

    candidate_grids: list[Grid] = []
    per_traversal: list[dict] = []

    for method in methods:
        prompt = format_traversal_prompt(train_pairs, test_input, method)
        try:
            response = bridge.call(prompt, temperature=0.0)
        except Exception as e:
            logger.warning("Traversal %s LLM call failed: %s", method, e)
            per_traversal.append({"method": method, "valid": False, "error": str(e)})
            continue

        grid = _parse_traversal_response(response, method, out_rows, out_cols)
        if grid is not None:
            candidate_grids.append(grid)
            per_traversal.append({"method": method, "valid": True})
            logger.debug("Traversal %s: parsed %dx%d grid", method,
                         len(grid), len(grid[0]) if grid else 0)
        else:
            per_traversal.append({"method": method, "valid": False})
            logger.debug("Traversal %s: failed to parse grid", method)

    if not candidate_grids:
        return TraversalTransductionResult(
            grid=None, agreement=0.0,
            n_valid=0, n_total=len(methods),
            per_traversal=per_traversal,
        )

    voted_grid = _majority_vote_grid(candidate_grids)
    agreement = _compute_agreement(candidate_grids)

    logger.info(
        "Traversal voter: %d/%d valid, agreement=%.1f%%",
        len(candidate_grids), len(methods), agreement * 100,
    )

    return TraversalTransductionResult(
        grid=voted_grid,
        agreement=agreement,
        n_valid=len(candidate_grids),
        n_total=len(methods),
        per_traversal=per_traversal,
    )
