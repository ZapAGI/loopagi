"""Natural language instruction evolution for ARC tasks.

Jeremy Berman approach: evolve plain-English instructions describing the
transformation rule, rather than Python code. An 8b model writes much
better English descriptions than syntactically correct transform functions.

Pipeline:
1. Generate N candidate NL instructions
2. Score each by having a sub-agent apply it to training examples
3. Individual revision: refine top candidates with error feedback
4. Pooled revision: combine best elements from multiple instructions
5. Apply winning instruction to test inputs via transduction

Usage:
    from loopagi.arc.nl_evolver import nl_evolve
    result = nl_evolve(bridge, task, train_pairs)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import ArcTask
    from loopagi.arc.llm_bridge import LLMBridge

logger = logging.getLogger(__name__)

# Type aliases
Grid = list[list[int]]
TrainPair = tuple[Grid, Grid]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_GENERATE_PROMPT = """\
You are solving an ARC-AGI puzzle. Given input/output grid pairs, \
write a precise English instruction that describes how to transform \
any input grid into its correct output grid.

{examples}

Write ONE clear, step-by-step instruction. Be specific about:
- Which cells/regions change and which stay the same
- Exact color values (integers 0-9)
- Spatial relationships (rows, columns, objects, boundaries)
- Order of operations

Reply with ONLY the instruction, no code."""

_APPLY_PROMPT = """\
Apply this transformation instruction to the input grid.

Instruction: {instruction}

Input grid: {input_grid}

Output the transformed grid as a JSON 2D array. \
Reply with ONLY the grid, like: [[1,2],[3,4]]"""

_REVISE_PROMPT = """\
Your transformation instruction is partially wrong.

Instruction: {instruction}

{error_feedback}

Write an improved instruction that fixes these errors. \
Be more specific about the transformation rule. \
Reply with ONLY the improved instruction, no code."""

_POOL_PROMPT = """\
Below are {n} transformation instructions for the same ARC puzzle. \
Each captures part of the pattern but none is fully correct.

{instructions}

Combine the best elements from ALL instructions into a single, \
precise instruction that correctly describes the transformation. \
Reply with ONLY the combined instruction, no code."""


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class NLCandidate:
    """A natural language instruction candidate."""

    instruction: str
    similarity: float = 0.0
    generation: int = 0
    source: str = "initial"  # initial, revised, pooled


@dataclass
class NLEvolutionResult:
    """Result of NL instruction evolution."""

    best_instruction: str
    best_similarity: float
    predictions: list[Grid]
    total_candidates: int
    generations: int
    solved: bool
    history: list[NLCandidate] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compact_grid(grid: Grid) -> str:
    """Compact grid representation for prompts."""
    return "[" + ",".join(
        "[" + ",".join(str(v) for v in row) + "]" for row in grid
    ) + "]"


def _format_examples(train_pairs: list[TrainPair], max_pairs: int = 3) -> str:
    """Format training pairs for prompts."""
    lines: list[str] = []
    for i, (inp, out) in enumerate(train_pairs[:max_pairs], 1):
        lines.append(f"Pair {i}:\n  Input:  {_compact_grid(inp)}\n  Output: {_compact_grid(out)}")
    return "\n".join(lines)


def _parse_grid(response: str) -> Grid | None:
    """Parse a grid from LLM response."""
    import json
    import re
    # Find first JSON array in response
    match = re.search(r"\[[\s\S]*\]", response)
    if not match:
        return None
    try:
        grid = json.loads(match.group())
        if isinstance(grid, list) and grid and isinstance(grid[0], list):
            return grid
    except (json.JSONDecodeError, IndexError):
        pass
    return None


def _grid_similarity(expected: Grid, actual: Grid) -> float:
    """Compute cell-level similarity between two grids."""
    if not expected or not actual:
        return 0.0
    if len(expected) != len(actual):
        return 0.0
    if len(expected[0]) != len(actual[0]):
        return 0.0
    total = len(expected) * len(expected[0])
    matching = sum(
        1 for r in range(len(expected)) for c in range(len(expected[0]))
        if expected[r][c] == actual[r][c]
    )
    return matching / total if total else 0.0


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def generate_instructions(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
    n: int = 10,
) -> list[NLCandidate]:
    """Generate N candidate NL instructions for the transformation."""
    examples_text = _format_examples(train_pairs)
    prompt = _GENERATE_PROMPT.format(examples=examples_text)
    candidates: list[NLCandidate] = []

    for i in range(n):
        temp = 0.3 + (i / max(n - 1, 1)) * 0.6  # 0.3 to 0.9
        try:
            response = bridge.call(prompt, temperature=temp)
        except Exception:
            continue
        if response.strip():
            candidates.append(NLCandidate(
                instruction=response.strip()[:500],
                generation=0,
                source="initial",
            ))
    return candidates


def score_instruction(
    bridge: LLMBridge,
    instruction: str,
    train_pairs: list[TrainPair],
) -> tuple[float, list[str]]:
    """Score an instruction by applying it to training pairs.

    Returns (avg_similarity, list_of_error_messages).
    """
    total_sim = 0.0
    errors: list[str] = []

    for i, (inp, expected) in enumerate(train_pairs):
        prompt = _APPLY_PROMPT.format(
            instruction=instruction,
            input_grid=_compact_grid(inp),
        )
        try:
            response = bridge.call(prompt)
        except Exception:
            errors.append(f"Pair {i+1}: LLM call failed")
            continue

        predicted = _parse_grid(response)
        if predicted is None:
            errors.append(f"Pair {i+1}: could not parse grid from response")
            continue

        sim = _grid_similarity(expected, predicted)
        total_sim += sim
        if sim < 1.0:
            errors.append(
                f"Pair {i+1}: {sim:.0%} correct. "
                f"Expected {_compact_grid(expected)}, got {_compact_grid(predicted)}"
            )

    avg_sim = total_sim / len(train_pairs) if train_pairs else 0.0
    return avg_sim, errors


def revise_instruction(
    bridge: LLMBridge,
    instruction: str,
    errors: list[str],
    generation: int,
) -> NLCandidate | None:
    """Revise a single instruction based on error feedback."""
    if not errors:
        return None
    error_text = "\n".join(errors[:3])  # Limit feedback length
    prompt = _REVISE_PROMPT.format(
        instruction=instruction,
        error_feedback=error_text,
    )
    try:
        response = bridge.call(prompt)
    except Exception:
        return None
    if not response.strip():
        return None
    return NLCandidate(
        instruction=response.strip()[:500],
        generation=generation,
        source="revised",
    )


def pool_instructions(
    bridge: LLMBridge,
    candidates: list[NLCandidate],
    generation: int,
) -> NLCandidate | None:
    """Combine the best elements from multiple instructions."""
    if len(candidates) < 2:
        return None
    numbered = "\n".join(
        f"{i+1}. {c.instruction}" for i, c in enumerate(candidates[:5])
    )
    prompt = _POOL_PROMPT.format(n=len(candidates[:5]), instructions=numbered)
    try:
        response = bridge.call(prompt)
    except Exception:
        return None
    if not response.strip():
        return None
    return NLCandidate(
        instruction=response.strip()[:500],
        generation=generation,
        source="pooled",
    )


def apply_instruction_to_test(
    bridge: LLMBridge,
    instruction: str,
    test_input: Grid,
) -> Grid | None:
    """Apply the winning instruction to a test input."""
    prompt = _APPLY_PROMPT.format(
        instruction=instruction,
        input_grid=_compact_grid(test_input),
    )
    try:
        response = bridge.call(prompt)
    except Exception:
        return None
    return _parse_grid(response)


# ---------------------------------------------------------------------------
# Main evolution loop
# ---------------------------------------------------------------------------


def nl_evolve(
    bridge: LLMBridge,
    task: ArcTask,
    train_pairs: list[TrainPair],
    initial_candidates: int = 10,
    top_k: int = 5,
) -> NLEvolutionResult:
    """Evolve NL instructions for an ARC task.

    Pipeline:
    1. Generate initial_candidates instructions
    2. Score all on training pairs
    3. Individual revision of top_k (with error feedback)
    4. Pooled revision combining top_k
    5. Apply best instruction to test inputs

    Args:
        bridge: LLM bridge for inference.
        task: ARC task with .test for predictions.
        train_pairs: Training (input, output) pairs.
        initial_candidates: Number of initial instructions to generate.
        top_k: Number of top candidates to revise/pool.

    Returns:
        NLEvolutionResult with predictions and best instruction.
    """
    if bridge.is_mock:
        return NLEvolutionResult(
            best_instruction="", best_similarity=0.0,
            predictions=[], total_candidates=0,
            generations=0, solved=False,
        )

    # Phase 1: Generate initial candidates
    logger.info("[%s] NL evolution: generating %d candidates...",
                task.task_id, initial_candidates)
    candidates = generate_instructions(bridge, train_pairs, n=initial_candidates)

    if not candidates:
        return NLEvolutionResult(
            best_instruction="", best_similarity=0.0,
            predictions=[], total_candidates=0,
            generations=0, solved=False,
        )

    # Phase 2: Score all candidates
    logger.info("[%s] NL evolution: scoring %d candidates...",
                task.task_id, len(candidates))
    for c in candidates:
        c.similarity, _ = score_instruction(bridge, c.instruction, train_pairs)

    candidates.sort(key=lambda c: c.similarity, reverse=True)
    best = candidates[0]
    logger.info("[%s] NL evolution: best initial sim=%.1f%%",
                task.task_id, best.similarity * 100)

    if best.similarity >= 1.0:
        return _finalize(bridge, task, candidates, generation=0)

    # Phase 3: Individual revision of top_k
    logger.info("[%s] NL evolution: revising top %d...", task.task_id, top_k)
    revised: list[NLCandidate] = []
    for c in candidates[:top_k]:
        _, errors = score_instruction(bridge, c.instruction, train_pairs)
        rev = revise_instruction(bridge, c.instruction, errors, generation=1)
        if rev is not None:
            rev.similarity, _ = score_instruction(
                bridge, rev.instruction, train_pairs,
            )
            revised.append(rev)
            if rev.similarity >= 1.0:
                all_cands = candidates + revised
                return _finalize(bridge, task, all_cands, generation=1)

    # Phase 4: Pooled revision
    logger.info("[%s] NL evolution: pooling top candidates...", task.task_id)
    all_scored = candidates + revised
    all_scored.sort(key=lambda c: c.similarity, reverse=True)
    pooled = pool_instructions(bridge, all_scored[:top_k], generation=2)
    if pooled is not None:
        pooled.similarity, _ = score_instruction(
            bridge, pooled.instruction, train_pairs,
        )
        all_scored.append(pooled)

    all_scored.sort(key=lambda c: c.similarity, reverse=True)
    return _finalize(bridge, task, all_scored, generation=2)


def _finalize(
    bridge: LLMBridge,
    task: ArcTask,
    candidates: list[NLCandidate],
    generation: int,
) -> NLEvolutionResult:
    """Apply the best instruction to test inputs and build result."""
    candidates.sort(key=lambda c: c.similarity, reverse=True)
    best = candidates[0]

    predictions: list[Grid] = []
    for test in task.test:
        pred = apply_instruction_to_test(bridge, best.instruction, test.input)
        if pred is not None:
            predictions.append(pred)
        else:
            predictions.append(test.input)  # Fallback to identity

    solved = best.similarity >= 1.0

    logger.info(
        "[%s] NL evolution done: best_sim=%.1f%%, %d candidates, solved=%s",
        task.task_id, best.similarity * 100, len(candidates), solved,
    )

    return NLEvolutionResult(
        best_instruction=best.instruction,
        best_similarity=best.similarity,
        predictions=predictions,
        total_candidates=len(candidates),
        generations=generation + 1,
        solved=solved,
        history=candidates,
    )
