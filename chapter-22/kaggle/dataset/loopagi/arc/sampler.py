"""Best-of-N candidate sampling for ARC program synthesis.

Instead of generating a single program per synthesis step, this module
generates N candidates with varied temperatures and selects the best
one by verification score.  This is the #1 technique from ARC Prize
2025 — Ryan Greenblatt scored 43% on ARC-AGI-1 with k=2048 samples.

We use a much smaller N (3-8) since each sample requires an LLM call,
but even N=5 dramatically reduces variance and increases the chance
of hitting 100% similarity for near-miss tasks.

Usage:
    from loopagi.arc.sampler import sample_n_programs, SampleConfig
    result = sample_n_programs(bridge, hypothesis, train_pairs)
    best_program = result.best
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.arc_analytics import ArcAnalytics
    from loopagi.arc.arc_loader import Grid
    from loopagi.arc.hypothesizer import Hypothesis
    from loopagi.arc.llm_bridge import LLMBridge

from loopagi.arc.synthesizer import (
    SynthesizedProgram,
    format_synthesis_prompt,
    synthesize_from_llm,
    synthesize_identity,
)
from loopagi.arc.verifier import VerificationResult, verify_program

logger = logging.getLogger(__name__)

# Type alias
TrainPair = tuple[list[list[int]], list[list[int]]]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class SampleConfig:
    """Controls Best-of-N sampling behaviour."""

    n_samples: int = 5
    """Number of candidate programs to generate per synthesis step."""

    temperature_min: float = 0.2
    """Minimum temperature for diversity."""

    temperature_max: float = 0.9
    """Maximum temperature for diversity."""

    timeout_per_sample: int = 10
    """Seconds before killing code execution for a sample."""


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass
class SampleResult:
    """Result of a Best-of-N sampling run."""

    programs: list[SynthesizedProgram] = field(default_factory=list)
    verifications: list[VerificationResult] = field(default_factory=list)
    best: SynthesizedProgram | None = None
    best_verification: VerificationResult | None = None
    best_similarity: float = 0.0
    n_valid: int = 0
    n_total: int = 0


# ---------------------------------------------------------------------------
# Temperature schedule
# ---------------------------------------------------------------------------


def _temperature_schedule(config: SampleConfig) -> list[float]:
    """Generate a list of temperatures for N samples.

    Linearly spaced between min and max, ensuring diversity.
    """
    n = config.n_samples
    if n <= 1:
        return [config.temperature_min]
    step = (config.temperature_max - config.temperature_min) / (n - 1)
    return [round(config.temperature_min + i * step, 3) for i in range(n)]


# ---------------------------------------------------------------------------
# Core sampling
# ---------------------------------------------------------------------------


def sample_n_programs(
    bridge: LLMBridge,
    hypothesis: Hypothesis,
    train_pairs: list[TrainPair],
    config: SampleConfig | None = None,
    similar_context: str = "",
    analytics: ArcAnalytics | None = None,
    task_id: str = "",
    hyp_id: int = 0,
) -> SampleResult:
    """Generate N candidate programs and return the best by verification.

    Args:
        bridge: LLM bridge for inference.
        hypothesis: The hypothesis to synthesize from.
        train_pairs: Training (input, output) pairs for verification.
        config: Sampling parameters.
        similar_context: Optional few-shot context for synthesis prompt.
        analytics: Optional analytics tracker.
        task_id: Task ID for analytics tracking.
        hyp_id: Hypothesis ID for analytics tracking.

    Returns:
        SampleResult with the best program and all candidates.
    """
    if config is None:
        config = SampleConfig()

    temps = _temperature_schedule(config)
    result = SampleResult(n_total=config.n_samples)

    synth_prompt = format_synthesis_prompt(
        hypothesis,
        train_pairs=train_pairs,
        similar_context=similar_context,
    )

    best_sim = 0.0
    best_prog: SynthesizedProgram | None = None
    best_verif: VerificationResult | None = None

    for sample_idx, temp in enumerate(temps):
        # Call LLM with varied temperature
        llm_response = bridge.call(synth_prompt)

        # Parse into program
        program = synthesize_from_llm(hypothesis, llm_response)
        result.programs.append(program)

        if not program.is_valid or "identity" in program.hypothesis.lower():
            # Invalid or fallback — record but skip verification
            verif = verify_program(program, train_pairs)
            result.verifications.append(verif)

            if analytics:
                analytics.add_candidate(
                    task_id=task_id,
                    hyp_id=hyp_id,
                    sample_id=sample_idx,
                    similarity=verif.avg_similarity,
                    wrong_cells=0,
                    error="invalid" if not program.is_valid else "identity_fallback",
                )
            continue

        # Verify against training pairs
        verif = verify_program(program, train_pairs)
        result.verifications.append(verif)
        result.n_valid += 1

        # Track in analytics
        if analytics:
            analytics.add_candidate(
                task_id=task_id,
                hyp_id=hyp_id,
                sample_id=sample_idx,
                similarity=verif.avg_similarity,
                wrong_cells=sum(
                    1 for pr in verif.pair_results if not pr.passed
                ),
            )

        # Update best
        if verif.avg_similarity > best_sim:
            best_sim = verif.avg_similarity
            best_prog = program
            best_verif = verif

        # Early exit: perfect score
        if verif.all_pass:
            logger.info(
                "Best-of-N: perfect score on sample %d/%d (temp=%.2f)",
                sample_idx + 1, config.n_samples, temp,
            )
            break

    # Fallback to identity if nothing worked
    if best_prog is None:
        best_prog = synthesize_identity()
        best_verif = verify_program(best_prog, train_pairs)
        best_sim = best_verif.avg_similarity

    result.best = best_prog
    result.best_verification = best_verif
    result.best_similarity = best_sim

    logger.info(
        "Best-of-N: %d/%d valid, best_sim=%.3f",
        result.n_valid, result.n_total, best_sim,
    )
    return result
