"""Fitness scoring for ARC program evolution.

Implements Imbue-style normalized scoring where identity programs score
low (0.2) and fully correct programs score 1.0. Also provides simplicity
scoring via code heuristics and output diversity checking.

Usage:
    from loopagi.arc.fitness import normalized_fitness, is_identity_code
    score = normalized_fitness(similarity=0.97, code="def transform(g): return g")
"""

from __future__ import annotations

import ast
import copy
import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Type aliases
Grid = list[list[int]]
TrainPair = tuple[Grid, Grid]

# ---------------------------------------------------------------------------
# Identity detection
# ---------------------------------------------------------------------------

_IDENTITY_PATTERNS = (
    "returngrid",
    "returng",
    "return[row[:]forrowingrid]",
    "return[row[:]forrowinggrid]",
    "return[list(row)forrowingrid]",
    "returnlist(grid)",
    "returncopy.deepcopy(grid)",
)


def is_identity_code(code: str) -> bool:
    """Check if code is effectively identity (returns input unchanged)."""
    if not code:
        return False
    s = code.replace(" ", "").replace("\n", "").replace("\t", "")
    return any(p in s for p in _IDENTITY_PATTERNS)


def _compute_identity_similarity(
    code: str,
    train_pairs: list[TrainPair],
) -> float | None:
    """Run code on training pairs and check if output == input for all.

    Returns the average input/output similarity if identity-like, None otherwise.
    """
    if not train_pairs:
        return None
    try:
        ns: dict = {}
        exec(code, ns)  # noqa: S102
        transform = ns.get("transform")
        if not callable(transform):
            return None
    except Exception:
        return None

    total_identity_sim = 0.0
    for inp, _expected in train_pairs:
        try:
            result = transform(copy.deepcopy(inp))
        except Exception:
            return None
        if not isinstance(result, list):
            return None
        # Check if result == input
        if result == inp:
            total_identity_sim += 1.0
        else:
            return None  # Not pure identity
    return total_identity_sim / len(train_pairs)


# ---------------------------------------------------------------------------
# Normalized fitness scoring (Imbue-style)
# ---------------------------------------------------------------------------

_IDENTITY_BASE = 0.2
_CORRECT_BONUS = 0.1


def normalized_fitness(
    similarity: float,
    code: str = "",
    train_pairs: list[TrainPair] | None = None,
    simplicity_weight: float = 0.03,
    transfer_weight: float = 0.07,
    transfer_score: float | None = None,
) -> float:
    """Compute normalized fitness score (Imbue-style).

    Identity = 0.2. Non-identity scaled 0.2-1.0. Weights: correctness 90%,
    transfer 7%, simplicity 3%. Transfer score is optional (defaults to 0.5
    if not provided, skipped if weight is 0).
    """
    if code and is_identity_code(code):
        return _IDENTITY_BASE
    if code and train_pairs and _compute_identity_similarity(code, train_pairs) is not None:
        return _IDENTITY_BASE

    # Correctness: 0.0 -> 0.2, 1.0 -> 0.9, bonus at 1.0 -> 1.0
    correctness_weight = 1.0 - simplicity_weight - transfer_weight
    correctness = _IDENTITY_BASE + similarity * (0.9 - _IDENTITY_BASE)
    if similarity >= 1.0:
        correctness += _CORRECT_BONUS

    simp = simplicity_score(code) if code else 0.5
    xfer = transfer_score if transfer_score is not None else 0.5

    fitness = (
        correctness * correctness_weight
        + simp * simplicity_weight
        + xfer * transfer_weight
    )
    return min(max(fitness, 0.0), 1.0)


# ---------------------------------------------------------------------------
# Simplicity scoring
# ---------------------------------------------------------------------------


def simplicity_score(code: str) -> float:
    """Score code simplicity from 0.0 (complex) to 1.0 (simple).

    Penalizes:
    - Hard-coded integer constants (especially color values 0-9)
    - Long code (more lines/characters)
    - Deeply nested structures
    """
    if not code:
        return 0.5

    # Count hard-coded integers via AST
    num_constants = 0
    num_color_constants = 0
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, int):
                num_constants += 1
                if 0 <= node.value <= 9:
                    num_color_constants += 1
    except SyntaxError:
        num_constants = len(re.findall(r"\b\d+\b", code))

    # Code length
    lines = [l for l in code.strip().split("\n") if l.strip()]
    num_lines = len(lines)

    # Scoring (lower counts = higher simplicity)
    constant_penalty = min(num_constants / 20.0, 1.0)
    color_penalty = min(num_color_constants / 10.0, 1.0)
    length_penalty = min(num_lines / 30.0, 1.0)

    score = 1.0 - (constant_penalty * 0.4 + color_penalty * 0.3 + length_penalty * 0.3)
    return max(score, 0.0)


# ---------------------------------------------------------------------------
# Output diversity checking
# ---------------------------------------------------------------------------


def outputs_differ(
    code_a: str,
    code_b: str,
    train_pairs: list[TrainPair],
) -> bool:
    """Check if two programs produce different outputs on any training input.

    Used as a diversity filter: reject mutations that produce identical
    outputs to the parent (they waste population slots).
    """
    if not train_pairs:
        return True

    for inp, _ in train_pairs:
        out_a = _safe_execute(code_a, inp)
        out_b = _safe_execute(code_b, inp)
        if out_a is None or out_b is None:
            return True  # Error = different behavior
        if out_a != out_b:
            return True
    return False


def _safe_execute(code: str, grid: Grid) -> Grid | None:
    """Execute transform code on a grid, return output or None on error."""
    try:
        ns: dict = {}
        exec(code, ns)  # noqa: S102
        transform = ns.get("transform")
        if not callable(transform):
            return None
        result = transform(copy.deepcopy(grid))
        return result if isinstance(result, list) else None
    except Exception:
        return None
