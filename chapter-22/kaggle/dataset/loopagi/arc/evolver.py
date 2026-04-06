"""Evolutionary program refinement for ARC solving.

Takes a near-miss program (≥ 90% similarity) and evolves it through
systematic mutations — verifying each variant by direct code execution
(no LLM calls).  Thousands of mutations per second are feasible.

The mutation generators live in ``mutator.py``; this module handles
verification, grid similarity, and the evolution loop.

Usage:
    from loopagi.arc.evolver import evolve_program, EvolutionConfig
    result = evolve_program(source_code, train_pairs)
    if result.solved:
        print("Exact solve via mutation!")
"""

from __future__ import annotations

import copy
import logging
import signal
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loopagi.arc.mutator import generate_mutations

if TYPE_CHECKING:
    from loopagi.arc.arc_analytics import ArcAnalytics

logger = logging.getLogger(__name__)

# Type aliases
Grid = list[list[int]]
TrainPair = tuple[Grid, Grid]


# ---------------------------------------------------------------------------
# Configuration & result
# ---------------------------------------------------------------------------


@dataclass
class EvolutionConfig:
    """Controls the mutation / evolution budget."""

    min_similarity: float = 0.90
    """Only evolve programs above this similarity threshold."""

    max_generations: int = 10
    """Maximum number of mutation generations."""

    mutations_per_generation: int = 20
    """How many mutations to evaluate per generation."""

    max_total_mutations: int = 200
    """Hard budget cap on total mutations evaluated."""

    exec_timeout: int = 5
    """Seconds before killing a mutant's execution."""


@dataclass
class EvolutionResult:
    """Result of an evolution run."""

    best_code: str
    best_similarity: float
    generations: int
    total_mutations: int
    solved: bool
    history: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Verification (fast, no LLM)
# ---------------------------------------------------------------------------

_EXEC_TIMEOUT = 5


class _MutantTimeout(Exception):
    pass


def _verify_mutant(
    code: str,
    train_pairs: list[TrainPair],
    timeout: int = _EXEC_TIMEOUT,
) -> float:
    """Execute mutated code and compute average similarity.

    Returns 0.0 on any error (syntax, runtime, timeout).
    """
    try:
        compile(code, "<mutant>", "exec")
    except SyntaxError:
        return 0.0

    ns: dict = {}
    try:
        exec(code, ns)
    except Exception:
        return 0.0

    transform_fn = ns.get("transform")
    if not callable(transform_fn):
        return 0.0

    def _alarm(signum: int, frame: object) -> None:
        raise _MutantTimeout()

    total_sim = 0.0
    for inp, expected in train_pairs:
        old_handler = signal.getsignal(signal.SIGALRM)
        try:
            signal.signal(signal.SIGALRM, _alarm)
            signal.alarm(timeout)
            result = transform_fn(copy.deepcopy(inp))
        except Exception:
            return 0.0
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

        if not isinstance(result, list):
            return 0.0

        total_sim += _grid_similarity(expected, result)

    return total_sim / len(train_pairs) if train_pairs else 0.0


def _grid_similarity(expected: Grid, actual: Grid) -> float:
    """Compute cell-level similarity between two grids."""
    if not expected or not actual:
        return 0.0
    exp_rows, exp_cols = len(expected), len(expected[0])
    act_rows = len(actual)
    act_cols = len(actual[0]) if actual else 0

    if exp_rows != act_rows or exp_cols != act_cols:
        max_rows = max(exp_rows, act_rows)
        max_cols = max(exp_cols, act_cols)
        total = max_rows * max_cols
        matching = 0
        for r in range(min(exp_rows, act_rows)):
            for c in range(min(exp_cols, act_cols)):
                if expected[r][c] == actual[r][c]:
                    matching += 1
        return matching / total if total else 0.0

    total = exp_rows * exp_cols
    matching = sum(
        1 for r in range(exp_rows)
        for c in range(exp_cols)
        if expected[r][c] == actual[r][c]
    )
    return matching / total if total else 0.0


# ---------------------------------------------------------------------------
# Evolution loop
# ---------------------------------------------------------------------------


def evolve_program(
    source_code: str,
    train_pairs: list[TrainPair],
    config: EvolutionConfig | None = None,
    analytics: ArcAnalytics | None = None,
) -> EvolutionResult:
    """Evolve a program through systematic mutations.

    Args:
        source_code: The Python source code of the best program so far.
        train_pairs: Training (input, output) pairs for verification.
        config: Evolution parameters.
        analytics: Optional analytics tracker.

    Returns:
        EvolutionResult with the best mutant found.
    """
    if config is None:
        config = EvolutionConfig()

    parent_code = source_code
    parent_sim = _verify_mutant(parent_code, train_pairs, config.exec_timeout)

    best_code = parent_code
    best_sim = parent_sim
    total_mutations = 0
    history: list[dict] = []

    logger.info(
        "Evolution starting: parent_sim=%.3f, budget=%d",
        parent_sim, config.max_total_mutations,
    )

    for gen in range(config.max_generations):
        if total_mutations >= config.max_total_mutations:
            logger.info("Evolution budget exhausted at gen %d", gen)
            break

        mutations = generate_mutations(parent_code)
        if not mutations:
            logger.info("No mutations possible at gen %d", gen)
            break

        mutations = mutations[:config.mutations_per_generation]

        gen_best_code = parent_code
        gen_best_sim = parent_sim
        gen_improved = False

        for mut in mutations:
            if total_mutations >= config.max_total_mutations:
                break
            total_mutations += 1

            sim = _verify_mutant(mut.mutated_code, train_pairs, config.exec_timeout)
            delta = sim - parent_sim

            if analytics:
                analytics.add_mutation(
                    task_id="",
                    parent_id=gen,
                    generation=gen,
                    mutation_type=mut.mutation_type,
                    target=mut.target,
                    similarity=sim,
                    delta=delta,
                )

            if sim > gen_best_sim:
                gen_best_sim = sim
                gen_best_code = mut.mutated_code
                gen_improved = True
                logger.debug(
                    "Gen %d: improved to %.3f via %s (%s)",
                    gen, sim, mut.mutation_type, mut.target,
                )

            if sim >= 1.0:
                logger.info("SOLVED via mutation: %s (%s)", mut.mutation_type, mut.target)
                return EvolutionResult(
                    best_code=mut.mutated_code,
                    best_similarity=1.0,
                    generations=gen + 1,
                    total_mutations=total_mutations,
                    solved=True,
                    history=history,
                )

        history.append({
            "generation": gen,
            "mutations_tried": min(len(mutations), config.mutations_per_generation),
            "best_sim": gen_best_sim,
            "improved": gen_improved,
        })

        if gen_best_sim > best_sim:
            best_sim = gen_best_sim
            best_code = gen_best_code

        if gen_improved:
            parent_code = gen_best_code
            parent_sim = gen_best_sim
        else:
            logger.info("No improvement at gen %d (sim=%.3f), stopping", gen, parent_sim)
            break

    return EvolutionResult(
        best_code=best_code,
        best_similarity=best_sim,
        generations=len(history),
        total_mutations=total_mutations,
        solved=best_sim >= 1.0,
        history=history,
    )
