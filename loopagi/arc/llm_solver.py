"""LLM-powered ARC solver refinement loop.

Extracted from llm_bridge.py to respect the 500-line module limit.
Orchestrates: Perceive -> Hypothesize -> Synthesize -> Verify -> Refine.

Usage:
    from loopagi.arc.llm_solver import solve_task_with_llm
    result = solve_task_with_llm(task, bridge)
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from loopagi.arc.few_shot import FewShotContext, build_few_shot_context
from loopagi.arc.nl_describer import describe_transformation, format_nl_context
from loopagi.arc.hypothesizer import (
    Hypothesis,
    HypothesisSet,
    format_hypothesis_prompt,
    hypothesize,
    parse_llm_hypotheses,
)
from loopagi.arc.perceiver import (
    estimate_complexity,
    format_perception_prompt,
    perceive_task,
)
from loopagi.arc.refiner import (
    diagnose_failures,
    format_refinement_prompt,
    refine,
)
from loopagi.arc.sampler import SampleConfig, sample_n_programs
from loopagi.arc.synthesizer import (
    SynthesizedProgram,
    format_synthesis_prompt,
    synthesize_from_hypothesis,
    synthesize_from_llm,
)
from loopagi.arc.verifier import verify_program

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import ArcDataset, ArcTask
    from loopagi.arc.llm_bridge import LLMBridge
    from loopagi.arc.task_similarity import TaskIndex

logger = logging.getLogger(__name__)

# Agent roles for model routing (mirrored from llm_bridge)
ROLE_PERCEIVER = "perceiver"
ROLE_HYPOTHESIZER = "hypothesizer"
ROLE_SYNTHESIZER = "synthesizer"
ROLE_REFINER = "refiner"


def solve_task_with_llm(
    task: ArcTask,
    bridge: LLMBridge,
    max_hypotheses: int = 5,
    max_iterations: int = 5,
    max_attempts: int = 2,
    adaptive: bool = True,
    task_index: TaskIndex | None = None,
    dataset: ArcDataset | None = None,
    sample_config: SampleConfig | None = None,
    enable_nl_description: bool = True,
) -> dict:
    """Solve an ARC task using the full LLM-powered refinement loop.

    Pipeline: Perceive -> Hypothesize -> Synthesize -> Verify -> Refine.
    Supports Best-of-N sampling when sample_config is provided.

    Args:
        task: The ARC task to solve.
        bridge: LLM bridge for inference calls.
        max_hypotheses: Number of hypotheses to try.
        max_iterations: Max refinement iterations per hypothesis.
        max_attempts: Prediction attempts per test input.
        adaptive: If True, override max_hypotheses/max_iterations
            based on estimated task complexity.
        task_index: Optional pre-built similarity index for few-shot.
        dataset: Optional dataset for loading similar task grids.
        sample_config: Optional Best-of-N sampling configuration.
        enable_nl_description: If True, generate NL transformation description
            before code synthesis (Imbue technique).

    Returns:
        Dict with solve result, predictions, bridge stats, and complexity.
    """
    from loopagi.arc.solver import SolveIteration, SolveResult, _apply_program_to_tests, _extract_train_pairs

    start = time.monotonic()
    result = SolveResult(task_id=task.task_id)
    train_pairs = _extract_train_pairs(task)

    # Phase 1: Perceive (deterministic analysis + LLM description)
    logger.info("[%s] Phase 1: Perceiving...", task.task_id)
    perception_prompt = format_perception_prompt(task)
    llm_description = bridge.call_as(ROLE_PERCEIVER, perception_prompt)
    report = perceive_task(task, llm_response=llm_description)

    # Adaptive complexity estimation
    complexity_level = "medium"
    if adaptive:
        complexity_level, params = estimate_complexity(report)
        max_hypotheses = params["max_hypotheses"]
        max_iterations = params["max_iterations"]
        logger.info(
            "[%s] Adaptive: complexity=%s, hyp=%d, iter=%d",
            task.task_id, complexity_level, max_hypotheses, max_iterations,
        )

    # Few-shot context from similar tasks
    few_shot = FewShotContext()
    if task_index is not None:
        logger.info("[%s] Building few-shot context...", task.task_id)
        few_shot = build_few_shot_context(
            task, task_index, dataset=dataset, k=3,
        )

    # Phase 1b: NL description (Imbue technique — describe before code)
    nl_description = ""
    if enable_nl_description and not bridge.is_mock:
        logger.info("[%s] Phase 1b: NL description...", task.task_id)
        nl_description = describe_transformation(bridge, train_pairs)

    # Phase 2: Hypothesize (pattern-based + LLM-generated)
    logger.info("[%s] Phase 2: Hypothesizing...", task.task_id)
    hyp_prompt = format_hypothesis_prompt(
        report, similar_context=few_shot.format_for_hypothesis(),
    )
    llm_hypotheses = bridge.call_as(ROLE_HYPOTHESIZER, hyp_prompt)
    hyp_set = hypothesize(report, llm_response=llm_hypotheses, max_hypotheses=max_hypotheses)

    if not hyp_set.hypotheses:
        result.total_seconds = time.monotonic() - start
        return {"result": result, "bridge_stats": bridge.stats(), "complexity": complexity_level}

    best_program: SynthesizedProgram | None = None
    best_sim = 0.0

    for hypothesis in hyp_set.ranked():
        current_hyp = hypothesis
        prev_iter_sim = 0.0
        stagnant_count = 0

        for iteration in range(max_iterations):
            # Phase 3: Synthesize (try pattern match first, then LLM)
            program = synthesize_from_hypothesis(current_hyp)

            # If pattern match returned identity (fallback), try LLM with examples
            if "identity" in program.hypothesis and not bridge.is_mock:
                similar_ctx = format_nl_context(nl_description) + few_shot.format_for_synthesis()

                if sample_config is not None:
                    # Best-of-N sampling: generate N candidates, pick best
                    logger.info(
                        "[%s] Iter %d: Best-of-%d sampling...",
                        task.task_id, iteration, sample_config.n_samples,
                    )
                    sr = sample_n_programs(
                        bridge, current_hyp, train_pairs,
                        config=sample_config,
                        similar_context=similar_ctx,
                        task_id=task.task_id,
                        hyp_id=hyp_set.hypotheses.index(hypothesis),
                    )
                    if sr.best is not None and "identity" not in sr.best.hypothesis:
                        program = sr.best
                    else:
                        logger.debug(
                            "[%s] Iter %d: Best-of-N fell back to identity",
                            task.task_id, iteration,
                        )
                else:
                    # Single synthesis call (original path)
                    logger.info("[%s] Iter %d: LLM synthesizing...", task.task_id, iteration)
                    synth_prompt = format_synthesis_prompt(
                        current_hyp,
                        train_pairs=train_pairs,
                        similar_context=similar_ctx,
                    )
                    llm_code = bridge.call_as(ROLE_SYNTHESIZER, synth_prompt)
                    llm_program = synthesize_from_llm(current_hyp, llm_code)
                    if "identity" not in llm_program.hypothesis:
                        program = llm_program
                    else:
                        logger.debug(
                            "[%s] Iter %d: LLM synthesis fell back to identity, keeping pattern match",
                            task.task_id, iteration,
                        )

            # Phase 4: Verify
            verification = verify_program(program, train_pairs)

            if verification.avg_similarity > best_sim:
                best_sim = verification.avg_similarity
                best_program = program

            # Adaptive stagnation detection (3-tier thresholds)
            improvement = verification.avg_similarity - prev_iter_sim
            prev_iter_sim = verification.avg_similarity
            if prev_iter_sim >= 0.90:
                stag_threshold, max_stag = 0.01, 4
            elif prev_iter_sim >= 0.70:
                stag_threshold, max_stag = 0.03, 3
            else:
                stag_threshold, max_stag = 0.05, 2

            if iteration > 0 and improvement < stag_threshold:
                stagnant_count += 1
                if stagnant_count >= max_stag:
                    logger.info(
                        "[%s] Stagnant after %d iters (sim=%.1f%%, thresh=%.2f, patience=%d)",
                        task.task_id, iteration + 1, verification.avg_similarity * 100,
                        stag_threshold, max_stag,
                    )
                    break
            else:
                stagnant_count = 0

            iter_record = SolveIteration(
                iteration=iteration,
                hypothesis=current_hyp,
                program=program,
                verification=verification,
                elapsed_seconds=0.0,
            )
            result.iterations.append(iter_record)

            if verification.all_pass:
                logger.info(
                    "[%s] SOLVED on iter %d: %s",
                    task.task_id, iteration, current_hyp.rule[:80],
                )
                result.solved = True
                result.best_program = program
                result.best_similarity = 1.0
                result.predictions = _apply_program_to_tests(program, task, max_attempts)
                result.total_seconds = time.monotonic() - start
                return {"result": result, "bridge_stats": bridge.stats(), "complexity": complexity_level}

            # Phase 5: Refine
            plan = refine(task.task_id, verification, current_hyp, iteration, max_iterations)
            iter_record.refinement = plan

            if plan.should_abandon:
                break

            # Try LLM refinement
            diagnostics = diagnose_failures(verification)
            refine_prompt = format_refinement_prompt(verification, current_hyp, diagnostics)
            llm_refinement = bridge.call_as(ROLE_REFINER, refine_prompt)

            refined_hyps = parse_llm_hypotheses(llm_refinement)
            if refined_hyps:
                current_hyp = refined_hyps[0]
            else:
                for action in plan.actions:
                    if action.new_hypothesis:
                        current_hyp = action.new_hypothesis
                        break
                else:
                    break

    result.best_program = best_program
    result.best_similarity = best_sim
    if best_program:
        result.predictions = _apply_program_to_tests(best_program, task, max_attempts)
    result.total_seconds = time.monotonic() - start

    # Free heavy iteration data to prevent memory accumulation across tasks.
    num_iters = len(result.iterations)
    result.iterations.clear()
    result._num_iterations_final = num_iters  # type: ignore[attr-defined]

    logger.info(
        "[%s] Unsolved after %d iterations (best sim: %.1f%%)",
        task.task_id, num_iters, best_sim * 100,
    )
    return {"result": result, "bridge_stats": bridge.stats(), "complexity": complexity_level}
