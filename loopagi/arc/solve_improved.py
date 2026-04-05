"""Improved ARC solver: transduction -> augmented voting -> synthesis -> evolution."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.arc_analytics import ArcAnalytics
    from loopagi.arc.arc_loader import ArcDataset, ArcTask
    from loopagi.arc.task_similarity import TaskIndex

from loopagi.arc.augmentation_voter import try_augmented_transduction
from loopagi.arc.diff_refiner import try_diff_refine
from loopagi.arc.evolver import EvolutionConfig, evolve_program
from loopagi.arc.grid_describer import format_object_prompt
from loopagi.arc.llm_bridge import LLMBridge
from loopagi.arc.llm_solver import solve_task_with_llm
from loopagi.arc.nl_evolver import nl_evolve
from loopagi.arc.pass_at_k import try_multi_strategy_transduction
from loopagi.arc.sampler import SampleConfig
from loopagi.arc.transducer import transduce, transduce_with_verification
from loopagi.arc.transducer_refine import transduce_with_refinement

logger = logging.getLogger(__name__)


@dataclass
class ImprovedSolverConfig:
    """Configuration for the improved solver pipeline."""

    enable_transduction: bool = True
    enable_object_prompts: bool = True
    enable_evolution: bool = True
    evolution_threshold: float = 0.90
    evolution_budget: int = 200
    evolution_generations: int = 10
    enable_population: bool = True
    population_size: int = 10
    crossover_rate: float = 0.25
    relaxed_transduction_threshold: float = 0.97
    enable_sampling: bool = True
    sample_n: int = 5
    sample_temperature_min: float = 0.2
    sample_temperature_max: float = 0.9
    cell_fix_threshold: float = 0.90
    enable_nl_description: bool = True
    enable_nl_evolution: bool = True
    enable_ttt: bool = True
    enable_multi_strategy: bool = True
    enable_diff_refine: bool = True
    diff_refine_threshold: float = 0.85
    relaxed_auto_accept: float = 0.95
    """Accept relaxed transduction when training sim >= this AND cross-val confirms."""
    enable_augmented_transduction: bool = True
    """v13: Enable D4 augmentation-based voting (16 extra LLM calls per task)."""
    enable_refined_transduction: bool = True
    """v13: Enable iterative refinement transduction."""
    enable_relaxed_retry: bool = True
    """v13: Enable relaxed transduction retry at 0.90 after 0.97 fails."""
    transduction_max_attempts: int = 3
    """v14: Max temperature attempts for strict transduction (1=temp 0.0 only)."""
    max_relaxed_train_pairs: int = 99
    """v14: Skip relaxed transduction if task has more training pairs than this."""
    time_limit: float = 0.0
    """v14: Per-task wall-clock limit in seconds (0=unlimited)."""
    skip_training_verification: bool = False
    """v15: Skip training pair verification in strict transduction (1 LLM call vs N+1)."""

_TRANSDUCTION_TEMPERATURES: tuple[float, ...] = (0.0, 0.3, 0.7)
"""Temperature schedule for multi-attempt transduction."""


def _try_transduction(
    task: ArcTask, bridge: LLMBridge, max_attempts: int = 3,
    temperatures: tuple[float, ...] | None = None,
    skip_verification: bool = False,
) -> dict | None:
    """Strict transduction: requires 100% on all training pairs.

    When *skip_verification* is True, uses ``transduce()`` (1 LLM call per
    test input) instead of ``transduce_with_verification()`` which does N+1
    calls. On T4 (~27 s/call), verification is too slow for >2 training pairs.
    """
    if bridge.is_mock:
        return None
    from loopagi.arc.solver import SolveResult, _extract_train_pairs
    train_pairs = _extract_train_pairs(task)
    temps = (temperatures or _TRANSDUCTION_TEMPERATURES)[:max_attempts]
    for attempt, temp in enumerate(temps):
        predictions: list[list[list[int]]] = []
        all_valid = True
        for test in task.test:
            if skip_verification:
                tr = transduce(bridge, train_pairs, test.input, temperature=temp)
            else:
                tr = transduce_with_verification(
                    bridge, train_pairs, test.input, temperature=temp)
            if tr.valid and tr.predicted_grid is not None:
                predictions.append(tr.predicted_grid)
            else:
                all_valid = False
                break
        if all_valid and predictions:
            logger.info("[%s] Transduction succeeded attempt %d (temp=%.1f, verified=%s)",
                        task.task_id, attempt + 1, temp, not skip_verification)
            result = SolveResult(task_id=task.task_id)
            result.solved = True
            result.best_similarity = 1.0
            result.predictions = predictions
            result.total_seconds = 0.0
            return {"result": result, "bridge_stats": bridge.stats(),
                    "complexity": "transduced"}
        logger.debug("[%s] Transduction attempt %d failed (temp=%.1f)",
                     task.task_id, attempt + 1, temp)
    return None


def _try_refined_transduction(task: ArcTask, bridge: LLMBridge) -> dict | None:
    """Phase Y: iterative refinement transduction with cell-level feedback."""
    if bridge.is_mock:
        return None
    from loopagi.arc.solver import SolveResult, _extract_train_pairs
    train_pairs = _extract_train_pairs(task)
    predictions: list[list[list[int]]] = []
    for test in task.test:
        result = transduce_with_refinement(bridge, train_pairs, test.input)
        if result.valid and result.predicted_grid is not None:
            predictions.append(result.predicted_grid)
        else:
            return None
    if not predictions:
        return None
    logger.info("[%s] Refined transduction succeeded", task.task_id)
    sr = SolveResult(task_id=task.task_id)
    sr.solved = True
    sr.best_similarity = 1.0
    sr.predictions = predictions
    sr.total_seconds = 0.0
    return {"result": sr, "bridge_stats": bridge.stats(), "complexity": "refined_transduction"}


def _cross_validate_predictions(
    bridge: LLMBridge, train_pairs: list, tests: list,
    predictions: list, task_id: str,
) -> bool:
    """Confirm predictions by re-running at temp=0.3 and checking agreement."""
    from loopagi.arc.transducer import _grid_similarity
    for idx, test in enumerate(tests):
        t2 = transduce(bridge, train_pairs, test.input, temperature=0.3)
        if t2.predicted_grid is None:
            return False
        if _grid_similarity(predictions[idx], t2.predicted_grid) < 0.95:
            logger.info("[%s] Relaxed cross-val: prediction %d disagrees", task_id, idx)
            return False
    logger.info("[%s] Relaxed cross-val: all predictions confirmed", task_id)
    return True


def _try_relaxed_transduction(
    task: ArcTask, bridge: LLMBridge, min_similarity: float = 0.97,
    auto_accept: float = 0.0,
) -> dict | None:
    """Relaxed transduction: accepts high-sim training results.

    When auto_accept > 0 and training sim >= auto_accept, runs a cross-validation
    second prediction at temp=0.3 — if it agrees (>=95%), marks as solved.
    """
    if bridge.is_mock:
        return None
    from loopagi.arc.solver import SolveResult, _extract_train_pairs
    from loopagi.arc.transducer import _grid_similarity
    train_pairs = _extract_train_pairs(task)
    train_sims: list[float] = []
    for _, (train_in, train_out) in enumerate(train_pairs):
        trans = transduce(bridge, train_pairs, train_in, temperature=0.0)
        if trans.predicted_grid is None:
            return None
        sim = _grid_similarity(train_out, trans.predicted_grid)
        if sim < min_similarity:
            return None
        train_sims.append(sim)
    predictions: list[list[list[int]]] = []
    for test in task.test:
        trans = transduce(bridge, train_pairs, test.input, temperature=0.0)
        if trans.predicted_grid is None:
            return None
        predictions.append(trans.predicted_grid)
    avg_sim = sum(train_sims) / len(train_sims) if train_sims else 0.0
    min_sim = min(train_sims) if train_sims else 0.0
    solved = avg_sim >= 1.0
    if not solved and auto_accept > 0 and min_sim >= auto_accept:
        solved = _cross_validate_predictions(
            bridge, train_pairs, task.test, predictions, task.task_id)
    logger.info("[%s] Relaxed transduction: avg=%.1f%%, min=%.1f%%, solved=%s",
                 task.task_id, avg_sim * 100, min_sim * 100, solved)
    result = SolveResult(task_id=task.task_id)
    result.solved = solved
    result.best_similarity = avg_sim
    result.predictions = predictions
    result.total_seconds = 0.0
    return {"result": result, "bridge_stats": bridge.stats(),
            "complexity": "relaxed_transduction"}


def _is_identity_program(result: object) -> bool:
    """Check if the best program is effectively identity (return input)."""
    if not hasattr(result, "best_program") or result.best_program is None:
        return False
    code = getattr(result.best_program, "source_code", "")
    if not code:
        return False
    s = code.replace(" ", "").replace("\n", "")
    return any(p in s for p in (
        "returngrid", "returng", "return[row[:]forrowingrid]",
        "return[list(row)forrowingrid]",
    ))


def _try_evolution(
    solve_dict: dict, task: ArcTask, config: ImprovedSolverConfig,
    analytics: ArcAnalytics | None = None, bridge: LLMBridge | None = None,
) -> dict:
    """Improve near-miss programs via AST mutation then LLM-guided evolution."""
    from loopagi.arc.solver import _extract_train_pairs, _apply_program_to_tests
    result = solve_dict["result"]
    if (result.solved or result.best_similarity < config.evolution_threshold
            or result.best_program is None or not result.best_program.source_code):
        return solve_dict
    logger.info("[%s] Evolving near-miss (sim=%.1f%%)...",
                result.task_id, result.best_similarity * 100)
    train_pairs = _extract_train_pairs(task)
    evo_config = EvolutionConfig(
        min_similarity=config.evolution_threshold,
        max_generations=config.evolution_generations,
        max_total_mutations=config.evolution_budget,
    )
    evo_result = evolve_program(
        result.best_program.source_code, train_pairs,
        config=evo_config, analytics=analytics)
    if evo_result.best_similarity > result.best_similarity:
        logger.info("[%s] Evolution: %.1f%% -> %.1f%%", result.task_id,
                    result.best_similarity * 100, evo_result.best_similarity * 100)
        result.best_similarity = evo_result.best_similarity
        result._evolved = True  # type: ignore[attr-defined]
        from loopagi.arc.synthesizer import synthesize_from_code
        evolved_program = synthesize_from_code(
            result.best_program.hypothesis, evo_result.best_code)
        result.best_program = evolved_program
        if evo_result.solved:
            result.solved = True
            result.best_similarity = 1.0
            result.predictions = _apply_program_to_tests(
                evolved_program, task, max_attempts=2)
    # Phase R: LLM-guided evolution as second pass
    if not result.solved and bridge is not None and not bridge.is_mock:
        from loopagi.arc.llm_evolver import llm_evolve
        llm_evo = llm_evolve(
            bridge, task, result.best_program.source_code,
            train_pairs, max_generations=5, candidates_per_gen=2,
            use_population=config.enable_population,
            population_size=config.population_size,
            crossover_rate=config.crossover_rate)
        if llm_evo.best_similarity > result.best_similarity:
            logger.info("[%s] LLM evo: %.1f%% -> %.1f%%", result.task_id,
                        result.best_similarity * 100, llm_evo.best_similarity * 100)
            result.best_similarity = llm_evo.best_similarity
            result._evolved = True  # type: ignore[attr-defined]
            evolved_program = synthesize_from_code(
                result.best_program.hypothesis, llm_evo.best_code)
            result.best_program = evolved_program
            if llm_evo.solved:
                result.solved = True
                result.best_similarity = 1.0
                result.predictions = _apply_program_to_tests(
                    evolved_program, task, max_attempts=2)
    return solve_dict

def _try_cell_fix(solve_dict: dict, task: ArcTask, bridge: LLMBridge) -> dict:
    """Fix near-miss programs by targeting specific wrong cells."""
    from loopagi.arc.cell_fixer import fix_cells
    from loopagi.arc.solver import _apply_program_to_tests, _extract_train_pairs
    result = solve_dict["result"]
    train_pairs = _extract_train_pairs(task)
    fix_result = fix_cells(bridge, task, result.best_program, train_pairs)
    if fix_result.similarity > result.best_similarity:
        logger.info("[%s] Cell fix: %.1f%% -> %.1f%%", result.task_id,
                    result.best_similarity * 100, fix_result.similarity * 100)
        result.best_similarity = fix_result.similarity
        result._cell_fixed = True  # type: ignore[attr-defined]
        if fix_result.fixed_program is not None:
            result.best_program = fix_result.fixed_program
            result.predictions = _apply_program_to_tests(
                fix_result.fixed_program, task, max_attempts=2)
        if fix_result.similarity >= 1.0:
            result.solved = True
            result.best_similarity = 1.0
    return solve_dict

def _try_transduction_cell_fix(
    solve_dict: dict, task: ArcTask, bridge: LLMBridge,
) -> dict:
    """Phase D: fix near-miss transduction predictions using training error analysis."""
    from loopagi.arc.cell_fixer import fix_transduction_cells
    from loopagi.arc.solver import _extract_train_pairs
    from loopagi.arc.transducer import _grid_similarity
    result = solve_dict["result"]
    train_pairs = _extract_train_pairs(task)
    predictions = result.predictions
    if not predictions:
        return solve_dict
    improved = []
    for idx, test in enumerate(task.test):
        pred = predictions[idx] if idx < len(predictions) else None
        if pred is None:
            return solve_dict
        fix = fix_transduction_cells(bridge, train_pairs, test.input, pred)
        if fix.fixed_grid is not None:
            improved.append(fix.fixed_grid)
        else:
            improved.append(pred)
    # Verify improvement on training pairs
    from loopagi.arc.transducer import transduce
    all_perfect = True
    for train_in, train_out in train_pairs:
        tr = transduce(bridge, train_pairs, train_in, temperature=0.0)
        if tr.predicted_grid is None or _grid_similarity(train_out, tr.predicted_grid) < 1.0:
            all_perfect = False
            break
    if all_perfect:
        result.predictions = improved
        result.solved = True
        result.best_similarity = 1.0
        logger.info("[%s] SOLVED via transduction cell fix!", task.task_id)
    return solve_dict


def solve_task_improved(
    task: ArcTask,
    bridge: LLMBridge,
    max_hypotheses: int = 5,
    max_iterations: int = 5,
    max_attempts: int = 2,
    adaptive: bool = True,
    task_index: TaskIndex | None = None,
    dataset: ArcDataset | None = None,
    config: ImprovedSolverConfig | None = None,
    analytics: ArcAnalytics | None = None,
) -> dict:
    """Solve an ARC task using the improved pipeline.

    Pipeline: transduction -> synthesis -> identity bypass ->
    relaxed transduction -> evolution -> cell fix.
    """
    if config is None:
        config = ImprovedSolverConfig()

    start = time.monotonic()
    relaxed = None  # Track relaxed transduction baseline

    # --- Phase 0: Transduction (strict, then refined) ---
    if config.enable_transduction and not bridge.is_mock:
        logger.info("[%s] Phase 0: Attempting transduction...", task.task_id)
        trans_result = _try_transduction(
            task, bridge, max_attempts=config.transduction_max_attempts,
            skip_verification=config.skip_training_verification)
        if trans_result is not None:
            trans_result["result"].total_seconds = time.monotonic() - start
            return trans_result
        # Phase Y: try iterative refinement transduction
        if config.enable_refined_transduction:
            refined = _try_refined_transduction(task, bridge)
            if refined is not None:
                refined["result"].total_seconds = time.monotonic() - start
                return refined
        # Phase CC3: augmentation-based voting transduction
        if config.enable_augmented_transduction:
            aug_result = try_augmented_transduction(task, bridge)
            if aug_result is not None:
                aug_result["result"].total_seconds = time.monotonic() - start
                return aug_result
        # Phase FF: multi-strategy voting (pass-at-K fallback for D4 failures)
        if config.enable_multi_strategy:
            multi_result = try_multi_strategy_transduction(task, bridge)
            if multi_result is not None:
                multi_result["result"].total_seconds = time.monotonic() - start
                return multi_result
        # Phase 0c: relaxed transduction (before code synthesis)
        # v14: skip relaxed transduction if too many training pairs (too slow)
        n_train = len(task.train)
        if n_train <= config.max_relaxed_train_pairs:
            relaxed = _try_relaxed_transduction(
                task, bridge, min_similarity=config.relaxed_transduction_threshold,
                auto_accept=config.relaxed_auto_accept)
        else:
            logger.info("[%s] Skipping relaxed transduction (%d train pairs > %d limit)",
                        task.task_id, n_train, config.max_relaxed_train_pairs)
            relaxed = None
        if relaxed is None and config.enable_relaxed_retry:
            # Retry with lower threshold just to get a floor baseline
            relaxed = _try_relaxed_transduction(
                task, bridge, min_similarity=0.90,
                auto_accept=config.relaxed_auto_accept)
        if relaxed is not None:
            relaxed["result"].total_seconds = time.monotonic() - start
            if relaxed["result"].solved:
                return relaxed
            # Phase D: transduction cell fix for near-miss relaxed outputs
            if relaxed["result"].best_similarity >= 0.95:
                relaxed = _try_transduction_cell_fix(relaxed, task, bridge)
                if relaxed["result"].solved:
                    relaxed["result"].total_seconds = time.monotonic() - start
                    return relaxed

    # v14: check time limit before entering expensive synthesis loop
    if config.time_limit > 0:
        elapsed = time.monotonic() - start
        if elapsed >= config.time_limit:
            logger.info("[%s] Time limit reached (%.0fs >= %.0fs), skipping synthesis",
                        task.task_id, elapsed, config.time_limit)
            from loopagi.arc.solver import SolveResult
            if relaxed is not None:
                relaxed["result"].total_seconds = elapsed
                return relaxed
            fallback = SolveResult(task_id=task.task_id)
            fallback.total_seconds = elapsed
            return {"result": fallback, "bridge_stats": bridge.stats(),
                    "complexity": "timeout"}

    # --- Main solve loop (existing pipeline) ---
    sample_cfg: SampleConfig | None = None
    if config.enable_sampling and not bridge.is_mock:
        sample_cfg = SampleConfig(
            n_samples=config.sample_n,
            temperature_min=config.sample_temperature_min,
            temperature_max=config.sample_temperature_max,
        )
    solve_dict = solve_task_with_llm(
        task=task, bridge=bridge,
        max_hypotheses=max_hypotheses, max_iterations=max_iterations,
        max_attempts=max_attempts, adaptive=adaptive,
        task_index=task_index, dataset=dataset,
        sample_config=sample_cfg,
        enable_nl_description=config.enable_nl_description,
    )
    # Keep relaxed transduction result if code synthesis did worse
    result = solve_dict["result"]
    if (relaxed is not None
            and relaxed["result"].best_similarity > result.best_similarity):
        logger.info("[%s] Relaxed transduction (%.1f%%) beats synthesis (%.1f%%), keeping",
                     task.task_id, relaxed["result"].best_similarity * 100,
                     result.best_similarity * 100)
        solve_dict = relaxed
        result = solve_dict["result"]

    # --- Post-loop evolution (skip for identity programs) ---
    if config.enable_evolution and not _is_identity_program(result):
        try:
            solve_dict = _try_evolution(solve_dict, task, config, analytics, bridge)
        except Exception as exc:
            logger.warning("[%s] Evolution error: %s", task.task_id, exc)

    # --- Post-evolution cell fix for near-miss programs ---
    result = solve_dict["result"]
    if (not result.solved and result.best_similarity >= config.cell_fix_threshold
            and result.best_program is not None
            and result.best_program.source_code
            and not _is_identity_program(result)):
        try:
            solve_dict = _try_cell_fix(solve_dict, task, bridge)
        except Exception as exc:
            logger.warning("[%s] Cell fix error: %s", task.task_id, exc)

    # --- Phase DD: NL evolution fallback for unsolved tasks ---
    result = solve_dict["result"]
    if (not result.solved and config.enable_nl_evolution
            and not bridge.is_mock and result.best_similarity < 0.95):
        try:
            from loopagi.arc.solver import _extract_train_pairs
            tp = _extract_train_pairs(task)
            nl_result = nl_evolve(bridge, task, tp, initial_candidates=8, top_k=3)
            if nl_result.best_similarity > result.best_similarity:
                logger.info("[%s] NL evolution improved: %.1f%% -> %.1f%%",
                             task.task_id, result.best_similarity * 100,
                             nl_result.best_similarity * 100)
                result.best_similarity = nl_result.best_similarity
                result.predictions = [[p] for p in nl_result.predictions]
                if nl_result.solved:
                    logger.info("[%s] SOLVED via NL evolution!", task.task_id)
                    result.solved = True
        except Exception as exc:
            logger.warning("[%s] NL evolution error: %s", task.task_id, exc)

    # --- Phase RR: Diff-based refinement for near-miss outputs ---
    result = solve_dict["result"]
    if (not result.solved and config.enable_diff_refine
            and not bridge.is_mock
            and result.best_similarity >= config.diff_refine_threshold):
        try:
            solve_dict = try_diff_refine(solve_dict, task, bridge,
                                         min_similarity=config.diff_refine_threshold)
        except Exception as exc:
            logger.warning("[%s] Diff refine error: %s", task.task_id, exc)

    # --- Phase EE: Test-Time Training (LoRA) for unsolved near-misses ---
    result = solve_dict["result"]
    if (not result.solved and config.enable_ttt
            and not bridge.is_mock and result.best_similarity >= 0.85):
        from loopagi.arc.ttt import try_ttt_solve
        solve_dict = try_ttt_solve(solve_dict, task)

    solve_dict["result"].total_seconds = time.monotonic() - start
    return solve_dict
