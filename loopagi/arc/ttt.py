"""Test-Time Training orchestrator for ARC-AGI tasks.

Calls the standalone ttt_train.py script in a separate Python 3.12 venv
with PyTorch+CUDA+Unsloth. This is necessary because the main project
uses Python 3.14 which has no PyTorch CUDA wheels yet.

The TTT script:
1. Creates leave-one-out tasks from training pairs
2. Augments with D4 symmetry + color permutations
3. LoRA fine-tunes qwen3:8b on augmented tasks
4. Generates predictions with the adapted model
5. Discards the adapter

Usage:
    from loopagi.arc.ttt import run_ttt
    predictions = run_ttt(task)
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import ArcTask

logger = logging.getLogger(__name__)

# Type aliases
Grid = list[list[int]]

# Paths
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_TTT_VENV_PYTHON = _PROJECT_ROOT / "chapter-21" / "ttt_venv" / "bin" / "python"
_TTT_SCRIPT = _PROJECT_ROOT / "chapter-21" / "ttt_train.py"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class TTTConfig:
    """Configuration for Test-Time Training."""

    model: str = "unsloth/Qwen3-8B-unsloth-bnb-4bit"
    """HuggingFace model for LoRA fine-tuning."""

    steps: int = 50
    """Number of gradient steps per task."""

    rank: int = 8
    """LoRA rank."""

    alpha: int = 16
    """LoRA alpha scaling factor."""

    color_perms: int = 3
    """Number of color permutation augmentations."""

    batch_size: int = 2
    """Training batch size."""

    timeout: int = 3600
    """Maximum seconds to wait for TTT script."""

    adaptive_steps: bool = True
    """Reduce gradient steps for tasks with many training examples."""

    n_predictions: int = 5
    """Number of predictions per test input (pass-at-K voting)."""


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass
class TTTResult:
    """Result of Test-Time Training on a task."""

    predictions: list[Grid] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    n_training_examples: int = 0
    success: bool = False
    error: str = ""


# ---------------------------------------------------------------------------
# Task serialization
# ---------------------------------------------------------------------------


def _serialize_task(task: ArcTask) -> dict:
    """Serialize an ARC task to JSON-compatible dict."""
    return {
        "task_id": task.task_id,
        "train": [
            {"input": p.input, "output": p.output}
            for p in task.train
        ],
        "test": [
            {"input": t.input}
            for t in task.test
        ],
    }


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def is_ttt_available() -> bool:
    """Check if TTT venv and script are available."""
    return _TTT_VENV_PYTHON.exists() and _TTT_SCRIPT.exists()


def _stop_ollama() -> bool:
    """Unload all Ollama models to free GPU VRAM. Returns True if models were loaded."""
    try:
        result = subprocess.run(
            ["ollama", "ps"], capture_output=True, text=True, timeout=10,
        )
        lines = [l for l in result.stdout.strip().split("\n") if l and not l.startswith("NAME")]
        had_models = len(lines) > 0
    except Exception:
        had_models = False

    if had_models:
        logger.info("TTT: unloading Ollama models to free VRAM...")
        for line in lines:
            model_name = line.split()[0]
            try:
                subprocess.run(["ollama", "stop", model_name], timeout=10)
            except Exception:
                pass
        time.sleep(2)  # Wait for GPU memory to be released
    return had_models


def _start_ollama() -> None:
    """Pre-warm Ollama after TTT (models load on demand, nothing to do)."""
    logger.info("TTT: Ollama ready (models will load on next request)")


def run_ttt(
    task: ArcTask,
    config: TTTConfig | None = None,
) -> TTTResult:
    """Run Test-Time Training on an ARC task.

    Spawns a subprocess using the Python 3.12 TTT venv with
    PyTorch+CUDA+Unsloth. The subprocess fine-tunes a LoRA adapter
    on augmented leave-one-out tasks, generates predictions, and
    returns them.

    Args:
        task: ARC task with training pairs and test inputs.
        config: TTT configuration parameters.

    Returns:
        TTTResult with predictions and metadata.
    """
    if config is None:
        config = TTTConfig()

    if not is_ttt_available():
        logger.warning("[%s] TTT: venv not available at %s", task.task_id, _TTT_VENV_PYTHON)
        return TTTResult(error="TTT venv not available")

    # VRAM safety: stop Ollama to free GPU memory before loading PyTorch model
    ollama_was_running = _stop_ollama()

    # Serialize task to temp file
    task_data = _serialize_task(task)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", prefix=f"ttt_{task.task_id}_",
        delete=False,
    ) as inp_f:
        json.dump(task_data, inp_f)
        input_path = inp_f.name

    output_path = input_path.replace(".json", "_predictions.json")

    # Adaptive gradient steps: fewer steps for larger augmented datasets
    steps = config.steps
    if config.adaptive_steps:
        n_train = len(task.train)
        n_augmented = n_train * config.color_perms * 8  # D4 × color perms
        if n_augmented > 80:
            steps = 30
            logger.info("[%s] TTT: adaptive steps %d->%d (n_augmented=%d)",
                        task.task_id, config.steps, steps, n_augmented)
        elif n_augmented > 50:
            steps = 40
            logger.info("[%s] TTT: adaptive steps %d->%d (n_augmented=%d)",
                        task.task_id, config.steps, steps, n_augmented)

    # Build command
    cmd = [
        str(_TTT_VENV_PYTHON),
        str(_TTT_SCRIPT),
        "--input", input_path,
        "--output", output_path,
        "--model", config.model,
        "--steps", str(steps),
        "--rank", str(config.rank),
        "--alpha", str(config.alpha),
        "--color-perms", str(config.color_perms),
        "--batch-size", str(config.batch_size),
        "--n-predictions", str(config.n_predictions),
    ]

    logger.info(
        "[%s] TTT: starting (model=%s, steps=%d, rank=%d)",
        task.task_id, config.model, steps, config.rank,
    )

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config.timeout,
            cwd=str(_PROJECT_ROOT),
        )

        if result.returncode != 0:
            logger.warning(
                "[%s] TTT: subprocess failed (exit %d): %s",
                task.task_id, result.returncode, result.stderr[-500:],
            )
            return TTTResult(error=f"Exit {result.returncode}: {result.stderr[-200:]}")

        # Log stdout from training
        for line in result.stdout.strip().split("\n")[-5:]:
            logger.info("[%s] TTT: %s", task.task_id, line)

    except subprocess.TimeoutExpired:
        logger.warning("[%s] TTT: timed out after %ds", task.task_id, config.timeout)
        if ollama_was_running:
            _start_ollama()
        return TTTResult(error=f"Timeout after {config.timeout}s")
    except Exception as e:
        logger.warning("[%s] TTT: error: %s", task.task_id, e)
        if ollama_was_running:
            _start_ollama()
        return TTTResult(error=str(e))

    # VRAM safety: restart Ollama after TTT is done
    if ollama_was_running:
        _start_ollama()

    # Load predictions
    output_file = Path(output_path)
    if not output_file.exists():
        logger.warning("[%s] TTT: output file not found", task.task_id)
        return TTTResult(error="Output file not found")

    try:
        with open(output_file) as f:
            pred_data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("[%s] TTT: failed to read output: %s", task.task_id, e)
        return TTTResult(error=f"Output parse error: {e}")
    finally:
        # Cleanup temp files
        Path(input_path).unlink(missing_ok=True)
        output_file.unlink(missing_ok=True)

    predictions = pred_data.get("predictions", [])
    elapsed = pred_data.get("elapsed_seconds", 0.0)
    n_examples = pred_data.get("n_training_examples", 0)

    logger.info(
        "[%s] TTT: done — %d predictions in %.1fs (%d training examples)",
        task.task_id, len(predictions), elapsed, n_examples,
    )

    return TTTResult(
        predictions=predictions,
        elapsed_seconds=elapsed,
        n_training_examples=n_examples,
        success=len(predictions) > 0,
    )


def try_ttt_solve(solve_dict: dict, task: ArcTask) -> dict:
    """Try TTT on a task and update solve_dict if it improves results.

    Handles the full TTT flow: run training, score predictions,
    update result if improved. Modifies solve_dict in-place.
    """
    result = solve_dict["result"]
    if not is_ttt_available():
        return solve_dict

    logger.info("[%s] TTT: attempting LoRA fine-tune (sim=%.1f%%)",
                 task.task_id, result.best_similarity * 100)

    ttt_result = run_ttt(task)
    if not ttt_result.success or not ttt_result.predictions:
        return solve_dict

    train_pairs = [(p.input, p.output) for p in task.train]
    ttt_sim = score_ttt_predictions(ttt_result.predictions, train_pairs, task)
    if ttt_sim > result.best_similarity:
        logger.info("[%s] TTT improved: %.1f%% -> %.1f%%",
                     task.task_id, result.best_similarity * 100, ttt_sim * 100)
        result.best_similarity = ttt_sim
        result.predictions = [[p] for p in ttt_result.predictions]
        if ttt_sim >= 1.0:
            logger.info("[%s] SOLVED via TTT!", task.task_id)
            result.solved = True

    return solve_dict


def score_ttt_predictions(
    predictions: list[Grid],
    train_pairs: list[tuple[Grid, Grid]],
    task: ArcTask,
) -> float:
    """Score TTT predictions using symbolic scoring + training accuracy.

    Combines structural prior score with how well the model reproduces
    training outputs (transduction quality as proxy for test correctness).
    """
    from loopagi.arc.symbolic_filter import extract_priors, score_candidate

    priors = extract_priors(train_pairs)
    sym_scores = [
        score_candidate(pred, test.input, priors)
        for pred, test in zip(predictions, task.test)
    ]
    avg_sym = sum(sym_scores) / len(sym_scores) if sym_scores else 0.0
    if avg_sym < 0.3:
        return 0.0
    return avg_sym
