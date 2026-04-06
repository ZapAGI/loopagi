"""LLM-guided code evolution for ARC programs.

Uses the LLM to understand what code does wrong and generate targeted
fixes with diff visualization. Imbue-style normalized fitness scoring.

Usage:
    from loopagi.arc.llm_evolver import llm_evolve
    result = llm_evolve(bridge, task, seed_code, train_pairs)
"""

from __future__ import annotations

import copy
import logging
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import ArcTask, Grid
    from loopagi.arc.llm_bridge import LLMBridge
    from loopagi.arc.verifier import VerificationResult

from loopagi.arc.fitness import normalized_fitness, outputs_differ
from loopagi.arc.population import Organism, Population, crossover
from loopagi.arc.transfer_scorer import compute_transfer_score

logger = logging.getLogger(__name__)

# Type aliases
TrainPair = tuple[list[list[int]], list[list[int]]]


# ---------------------------------------------------------------------------
# Mutation prompt templates
# ---------------------------------------------------------------------------

_MUTATION_PROMPT = """\
You are fixing a Python function that solves an ARC-AGI puzzle.

Training examples:
{examples}

Current code:
```python
{current_code}
```

Current code output vs expected (wrong cells marked with X):
{diff_visualization}

Overall accuracy: {similarity:.1%}

{mutation_instruction}

First, describe in one sentence what the code does wrong.
Then, write a corrected version of the transform() function.
Reply with ONLY the explanation line and a ```python block."""

_INCREMENTAL_INSTRUCTION = (
    "Make a small, targeted fix to the existing code. "
    "Change only what is necessary to fix the wrong cells."
)

_RADICAL_INSTRUCTION = (
    "Reconsider the approach entirely. The current method may be "
    "fundamentally wrong. Try a completely different transformation strategy."
)


# ---------------------------------------------------------------------------
# Differential visualization
# ---------------------------------------------------------------------------


def format_diff_visualization(expected: Grid, actual: Grid) -> str:
    """Create ASCII visualization highlighting wrong cells.

    Correct cells show their value. Wrong cells show ``X<actual>-><expected>``.

    Args:
        expected: The correct output grid.
        actual: The produced output grid.

    Returns:
        Multi-line string visualization.
    """
    if not expected or not actual:
        return "(empty grid)"

    exp_rows, exp_cols = len(expected), len(expected[0]) if expected else 0
    act_rows = len(actual)
    act_cols = len(actual[0]) if actual else 0

    if exp_rows != act_rows or exp_cols != act_cols:
        return (
            f"Shape mismatch: expected {exp_rows}x{exp_cols}, "
            f"got {act_rows}x{act_cols}"
        )

    lines: list[str] = []
    for r in range(exp_rows):
        parts: list[str] = []
        for c in range(exp_cols):
            if expected[r][c] == actual[r][c]:
                parts.append(str(actual[r][c]))
            else:
                parts.append(f"X{actual[r][c]}->{expected[r][c]}")
        lines.append(" ".join(parts))
    return "\n".join(lines)


def _format_examples(train_pairs: list[TrainPair]) -> str:
    """Format training pairs for the mutation prompt."""
    lines: list[str] = []
    for i, (inp, out) in enumerate(train_pairs, 1):
        inp_str = "[" + ",".join("[" + ",".join(str(v) for v in row) + "]" for row in inp) + "]"
        out_str = "[" + ",".join("[" + ",".join(str(v) for v in row) + "]" for row in out) + "]"
        lines.append(f"Pair {i}: {inp_str} -> {out_str}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LLM mutation
# ---------------------------------------------------------------------------


def llm_mutate(
    bridge: LLMBridge,
    current_code: str,
    train_pairs: list[TrainPair],
    similarity: float,
    diff_text: str,
    strength: str = "incremental",
) -> str | None:
    """Generate an LLM-guided mutation of the current code."""
    from loopagi.arc.synthesizer import extract_code_from_response

    instruction = (
        _INCREMENTAL_INSTRUCTION if strength == "incremental"
        else _RADICAL_INSTRUCTION
    )

    prompt = _MUTATION_PROMPT.format(
        examples=_format_examples(train_pairs),
        current_code=current_code,
        diff_visualization=diff_text,
        similarity=similarity,
        mutation_instruction=instruction,
    )

    response = bridge.call(prompt)
    code = extract_code_from_response(response)

    if not code or "def transform" not in code:
        return None

    # Quick syntax check
    try:
        compile(code, "<llm_mutant>", "exec")
    except SyntaxError:
        return None

    return code


# ---------------------------------------------------------------------------
# Verification (fast, no LLM)
# ---------------------------------------------------------------------------


def _verify_code(
    code: str,
    train_pairs: list[TrainPair],
) -> tuple[float, list[Grid]]:
    """Execute code and compute average similarity.

    Returns:
        Tuple of (similarity, list_of_actual_outputs).
        Returns (0.0, []) on any error.
    """
    try:
        compile(code, "<llm_mutant>", "exec")
    except SyntaxError:
        return 0.0, []

    ns: dict = {}
    try:
        exec(code, ns)  # noqa: S102
    except Exception:
        return 0.0, []

    transform_fn = ns.get("transform")
    if not callable(transform_fn):
        return 0.0, []

    total_sim = 0.0
    outputs: list[Grid] = []

    for inp, expected in train_pairs:
        try:
            result = transform_fn(copy.deepcopy(inp))
        except Exception:
            return 0.0, []

        if not isinstance(result, list):
            return 0.0, []

        outputs.append(result)
        total_sim += _grid_similarity(expected, result)

    avg_sim = total_sim / len(train_pairs) if train_pairs else 0.0
    return avg_sim, outputs


def _grid_similarity(expected: Grid, actual: Grid) -> float:
    """Compute cell-level similarity between two grids."""
    if not expected or not actual:
        return 0.0
    exp_rows, exp_cols = len(expected), len(expected[0])
    act_rows = len(actual)
    act_cols = len(actual[0]) if actual else 0

    if exp_rows != act_rows or exp_cols != act_cols:
        return 0.0

    total = exp_rows * exp_cols
    matching = sum(
        1 for r in range(exp_rows) for c in range(exp_cols)
        if expected[r][c] == actual[r][c]
    )
    return matching / total if total else 0.0


# ---------------------------------------------------------------------------
# Evolution result
# ---------------------------------------------------------------------------


@dataclass
class LLMEvolutionResult:
    """Result of an LLM-guided evolution run."""

    best_code: str
    best_similarity: float
    generations: int
    total_mutations: int
    solved: bool
    history: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# LLM-guided evolution loop
# ---------------------------------------------------------------------------


def llm_evolve(
    bridge: LLMBridge,
    task: ArcTask,
    seed_code: str,
    train_pairs: list[TrainPair],
    max_generations: int = 5,
    candidates_per_gen: int = 2,
    use_population: bool = False,
    population_size: int = 10,
    crossover_rate: float = 0.25,
) -> LLMEvolutionResult:
    """Evolve a program using LLM-guided mutations with optional population."""
    current_code = seed_code
    current_sim, current_outputs = _verify_code(current_code, train_pairs)
    best_code = current_code
    best_sim = current_sim
    total_mutations = 0
    history: list[dict] = []

    # Population pool for diverse candidate tracking
    pop: Population | None = None
    if use_population:
        pop = Population(max_size=population_size)
        seed_fitness = normalized_fitness(
            current_sim, code=seed_code, train_pairs=train_pairs,
        )
        pop.add(Organism(code=seed_code, fitness=seed_fitness, generation=0))

    mode = f"population(size={population_size})" if pop else "single-track"
    logger.info(
        "[%s] LLM evolution starting (%s): sim=%.1f%%, budget=%d gens x %d candidates",
        task.task_id, mode, current_sim * 100, max_generations, candidates_per_gen,
    )

    for gen in range(max_generations):
        # Select mutation parent (population-weighted or current best)
        if pop is not None:
            parent = pop.select_parent()
            mutation_code = parent.code if parent else current_code
            mutation_sim, mutation_outputs = _verify_code(mutation_code, train_pairs)
        else:
            mutation_code = current_code
            mutation_sim = current_sim
            mutation_outputs = current_outputs

        # Build diff visualization from worst training pair
        diff_text = _build_worst_diff(train_pairs, mutation_outputs)

        gen_best_code = current_code
        gen_best_sim = current_sim
        gen_improved = False

        # --- Crossover attempt (population mode, every other gen) ---
        if (
            pop is not None
            and gen % 2 == 1
            and len(pop) >= 3
            and random.random() < crossover_rate
        ):
            parents = pop.select_parents(3)
            examples_text = _format_examples(train_pairs)
            xover_code = crossover(bridge, parents, examples_text, gen)
            total_mutations += 1

            if xover_code is not None:
                xover_sim, _ = _verify_code(xover_code, train_pairs)
                xfer = _maybe_transfer_score(bridge, xover_code, task, xover_sim)
                xover_fit = normalized_fitness(
                    xover_sim, code=xover_code, train_pairs=train_pairs,
                    transfer_score=xfer,
                )
                pop.add(Organism(
                    code=xover_code, fitness=xover_fit,
                    generation=gen, parent_id=-1,
                ))
                logger.debug(
                    "[%s] Gen %d: crossover produced sim=%.1f%%",
                    task.task_id, gen, xover_sim * 100,
                )

                if xover_sim > gen_best_sim:
                    gen_best_sim = xover_sim
                    gen_best_code = xover_code
                    gen_improved = True

                if xover_sim >= 1.0:
                    logger.info(
                        "[%s] SOLVED via crossover at gen %d!",
                        task.task_id, gen,
                    )
                    return LLMEvolutionResult(
                        best_code=xover_code,
                        best_similarity=1.0,
                        generations=gen + 1,
                        total_mutations=total_mutations,
                        solved=True,
                        history=history,
                    )

        # --- Mutation candidates ---
        for candidate_idx in range(candidates_per_gen):
            strength = random.choice(["incremental", "radical"])

            mutated = llm_mutate(
                bridge, mutation_code, train_pairs,
                mutation_sim, diff_text, strength=strength,
            )
            total_mutations += 1

            if mutated is None:
                logger.debug(
                    "[%s] Gen %d, candidate %d: LLM returned no valid code",
                    task.task_id, gen, candidate_idx,
                )
                continue

            mut_sim, mut_outputs = _verify_code(mutated, train_pairs)

            # Diversity filter: reject if outputs identical to parent
            if not outputs_differ(mutated, mutation_code, train_pairs):
                logger.debug(
                    "[%s] Gen %d, candidate %d: identical outputs, rejected",
                    task.task_id, gen, candidate_idx,
                )
                continue

            # Add to population pool with normalized fitness
            if pop is not None:
                xfer = _maybe_transfer_score(bridge, mutated, task, mut_sim)
                mut_fit = normalized_fitness(
                    mut_sim, code=mutated, train_pairs=train_pairs,
                    transfer_score=xfer,
                )
                pop.add(Organism(
                    code=mutated, fitness=mut_fit, generation=gen,
                ))

            if mut_sim > gen_best_sim:
                gen_best_sim = mut_sim
                gen_best_code = mutated
                gen_improved = True
                logger.debug(
                    "[%s] Gen %d: improved to %.1f%% via %s mutation",
                    task.task_id, gen, mut_sim * 100, strength,
                )

            if mut_sim >= 1.0:
                logger.info(
                    "[%s] SOLVED via LLM evolution at gen %d!", task.task_id, gen,
                )
                return LLMEvolutionResult(
                    best_code=mutated,
                    best_similarity=1.0,
                    generations=gen + 1,
                    total_mutations=total_mutations,
                    solved=True,
                    history=history,
                )

        # Update population best tracking
        if pop is not None:
            pop_best = pop.best()
            if pop_best and pop_best.fitness > best_sim:
                best_sim = pop_best.fitness
                best_code = pop_best.code

        history.append({
            "generation": gen,
            "candidates": candidates_per_gen,
            "best_sim": gen_best_sim,
            "improved": gen_improved,
            "population": pop.summary() if pop else None,
        })

        if gen_best_sim > best_sim:
            best_sim = gen_best_sim
            best_code = gen_best_code

        if gen_improved:
            current_code = gen_best_code
            current_sim = gen_best_sim
            _, current_outputs = _verify_code(current_code, train_pairs)
        else:
            logger.info(
                "[%s] LLM evolution: no improvement at gen %d (sim=%.1f%%), stopping",
                task.task_id, gen, current_sim * 100,
            )
            break

    if pop is not None:
        logger.info(
            "[%s] LLM evolution finished: %s",
            task.task_id, pop.summary(),
        )

    return LLMEvolutionResult(
        best_code=best_code,
        best_similarity=best_sim,
        generations=len(history),
        total_mutations=total_mutations,
        solved=best_sim >= 1.0,
        history=history,
    )


def _maybe_transfer_score(
    bridge: LLMBridge, code: str, task: ArcTask, similarity: float,
) -> float | None:
    """Compute transfer score only for promising candidates (sim >= 0.8)."""
    if similarity < 0.8 or bridge.is_mock:
        return None
    try:
        return compute_transfer_score(bridge, code, task)
    except Exception:
        return None


def _build_worst_diff(
    train_pairs: list[TrainPair],
    outputs: list[Grid],
) -> str:
    """Build diff visualization for the worst-performing training pair."""
    if not outputs or not train_pairs:
        return "(no outputs to compare)"

    worst_sim = 1.0
    worst_idx = 0
    for i, ((_, expected), actual) in enumerate(zip(train_pairs, outputs)):
        sim = _grid_similarity(expected, actual)
        if sim < worst_sim:
            worst_sim = sim
            worst_idx = i

    _, expected = train_pairs[worst_idx]
    actual = outputs[worst_idx] if worst_idx < len(outputs) else []
    return format_diff_visualization(expected, actual)
