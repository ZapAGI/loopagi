"""Kaggle submission script for ARC Prize 2026 - ARC-AGI-2.

Self-contained script that runs our full solver pipeline using direct
HuggingFace inference (no Ollama, no internet required).

Reads: arc-agi_test_challenges.json (240 tasks)
Writes: submission.json (2 attempts per test output)

Hardware target: Kaggle T4/P100 GPU (16GB VRAM), ~30GB RAM, ~12h runtime.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import warnings

# Suppress known harmless warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths — adapt for Kaggle environment
# ---------------------------------------------------------------------------

# Kaggle competition data directory
KAGGLE_INPUT = os.environ.get("KAGGLE_INPUT", "/kaggle/input/arc-prize-2026-arc-agi-2")
if not os.path.exists(KAGGLE_INPUT):
    # Local testing fallback
    KAGGLE_INPUT = "/tmp/arc-prize-2026-data"

CHALLENGES_PATH = os.path.join(KAGGLE_INPUT, "arc-agi_test_challenges.json")
SAMPLE_SUB_PATH = os.path.join(KAGGLE_INPUT, "sample_submission.json")
OUTPUT_PATH = "/kaggle/working/submission.json"
if not os.path.exists("/kaggle/working"):
    OUTPUT_PATH = "submission.json"

# Model — either from Kaggle dataset or HuggingFace cache
MODEL_NAME = os.environ.get(
    "ARC_MODEL", "unsloth/Qwen3-8B-unsloth-bnb-4bit"
)

# Time budget: leave 30 min buffer for safety
MAX_TOTAL_SECONDS = int(os.environ.get("ARC_MAX_SECONDS", "39600"))  # 11h
MAX_PER_TASK_SECONDS = int(os.environ.get("ARC_MAX_PER_TASK", "600"))  # 10 min

# ---------------------------------------------------------------------------
# Pipeline configuration (optimized for Kaggle time limits)
# ---------------------------------------------------------------------------


def get_kaggle_config():
    """Return solver config optimized for Kaggle's 12h time limit."""
    from loopagi.arc.solve_improved import ImprovedSolverConfig
    return ImprovedSolverConfig(
        enable_transduction=True,
        enable_evolution=False,       # Too slow for 240 tasks
        enable_sampling=True,
        enable_ttt=False,             # No separate venv on Kaggle
        enable_multi_strategy=True,
        enable_diff_refine=False,     # Too slow for 240 tasks
        enable_nl_evolution=False,    # Too slow for 240 tasks
        relaxed_auto_accept=0.95,
        sample_n=3,                   # Fewer samples to save time
        cell_fix_threshold=0.90,
    )


# Solver params (not part of ImprovedSolverConfig)
KAGGLE_MAX_HYPOTHESES = 2
KAGGLE_MAX_ITERATIONS = 2


# ---------------------------------------------------------------------------
# Task loading (direct from Kaggle JSON, not our ArcLoader)
# ---------------------------------------------------------------------------


def load_tasks(path: str) -> dict:
    """Load challenge tasks from Kaggle JSON format."""
    with open(path) as f:
        return json.load(f)


def kaggle_task_to_arc_task(task_id: str, task_data: dict):
    """Convert Kaggle JSON task format to our ArcTask dataclass."""
    from loopagi.arc.arc_loader import ArcTask, GridPair, TestInput
    train_pairs = [
        GridPair(input=p["input"], output=p["output"])
        for p in task_data["train"]
    ]
    test_inputs = [
        TestInput(input=t["input"], output=t.get("output"))
        for t in task_data["test"]
    ]
    return ArcTask(
        task_id=task_id,
        train=train_pairs,
        test=test_inputs,
    )


# ---------------------------------------------------------------------------
# Main submission pipeline
# ---------------------------------------------------------------------------


def solve_all_tasks(tasks: dict, bridge) -> dict:
    """Run solver on all tasks and build submission dict."""
    from loopagi.arc.solve_improved import solve_task_improved

    config = get_kaggle_config()
    submission = {}
    total_start = time.monotonic()
    solved_count = 0
    n_tasks = len(tasks)

    logger.info("Starting: %d tasks, model=%s", n_tasks, MODEL_NAME)
    logger.info("Config: max_hypotheses=%d, max_iterations=%d, sample_n=%d",
                config.max_hypotheses, config.max_iterations, config.sample_n)

    for i, (task_id, task_data) in enumerate(tasks.items()):
        elapsed_total = time.monotonic() - total_start
        remaining = MAX_TOTAL_SECONDS - elapsed_total

        if remaining < 120:
            logger.warning("Time budget exhausted at task %d/%d, filling rest with fallback",
                          i + 1, n_tasks)
            # Fill remaining tasks with identity fallback
            for tid, tdata in list(tasks.items())[i:]:
                submission[tid] = _fallback_submission(tdata)
            break

        task = kaggle_task_to_arc_task(task_id, task_data)
        task_start = time.monotonic()

        try:
            solve_dict = solve_task_improved(
                task=task,
                bridge=bridge,
                max_hypotheses=KAGGLE_MAX_HYPOTHESES,
                max_iterations=KAGGLE_MAX_ITERATIONS,
                config=config,
                analytics=None,
            )
            result = solve_dict["result"]
            task_time = time.monotonic() - task_start

            if result.solved:
                solved_count += 1
                logger.info("[%d/%d] %s: SOLVED [%s] (%.1fs)",
                           i + 1, n_tasks, task_id,
                           getattr(result, '_solve_method', 'unknown'),
                           task_time)
            else:
                logger.info("[%d/%d] %s: %.0f%% (%.1fs)",
                           i + 1, n_tasks, task_id,
                           result.best_similarity * 100, task_time)

            # Build submission entry with 2 attempts
            submission[task_id] = _build_submission_entry(task, result)

        except Exception as e:
            task_time = time.monotonic() - task_start
            logger.warning("[%d/%d] %s: ERROR %s (%.1fs)",
                          i + 1, n_tasks, task_id, e, task_time)
            submission[task_id] = _fallback_submission(task_data)

    total_time = time.monotonic() - total_start
    logger.info("=" * 60)
    logger.info("Done: %d/%d solved (%.1f%%), %.0fs total",
                solved_count, n_tasks, solved_count / n_tasks * 100, total_time)

    return submission


def _build_submission_entry(task, result) -> list:
    """Convert solver result to Kaggle submission format.

    Each test output gets 2 attempts. attempt_1 is the best prediction,
    attempt_2 is a second-best or identity fallback.
    """
    entries = []
    predictions = getattr(result, 'predictions', [])

    for idx, test in enumerate(task.test):
        entry = {}

        # attempt_1: best prediction
        if idx < len(predictions):
            pred = predictions[idx]
            # Handle nested format [[grid1, grid2], ...]
            if isinstance(pred, list) and pred and isinstance(pred[0], list):
                if isinstance(pred[0][0], list):
                    # Nested: list of candidate grids
                    entry["attempt_1"] = pred[0]
                    entry["attempt_2"] = pred[1] if len(pred) > 1 else pred[0]
                else:
                    # Single grid
                    entry["attempt_1"] = pred
                    entry["attempt_2"] = pred
            else:
                entry["attempt_1"] = pred
                entry["attempt_2"] = pred
        else:
            # Fallback to identity (input = output)
            entry["attempt_1"] = test.input
            entry["attempt_2"] = test.input

        entries.append(entry)

    return entries


def _fallback_submission(task_data: dict) -> list:
    """Create fallback submission entry (identity: output = input)."""
    entries = []
    for test in task_data["test"]:
        entries.append({
            "attempt_1": test["input"],
            "attempt_2": test["input"],
        })
    return entries


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    start = time.monotonic()

    # Check if running on Kaggle
    on_kaggle = os.path.exists("/kaggle/input")
    logger.info("Environment: %s", "Kaggle" if on_kaggle else "Local")

    # Load tasks
    logger.info("Loading tasks from %s", CHALLENGES_PATH)
    if not os.path.exists(CHALLENGES_PATH):
        logger.error("Challenge file not found: %s", CHALLENGES_PATH)
        sys.exit(1)

    tasks = load_tasks(CHALLENGES_PATH)
    logger.info("Loaded %d tasks", len(tasks))

    # Create HF bridge (direct model inference, no Ollama)
    logger.info("Loading model: %s", MODEL_NAME)
    from loopagi.arc.hf_bridge import create_hf_bridge
    bridge = create_hf_bridge(model=MODEL_NAME)
    logger.info("Model loaded in %.1fs", time.monotonic() - start)

    # Solve all tasks
    submission = solve_all_tasks(tasks, bridge)

    # Validate submission
    if os.path.exists(SAMPLE_SUB_PATH):
        with open(SAMPLE_SUB_PATH) as f:
            sample = json.load(f)
        missing = set(sample.keys()) - set(submission.keys())
        if missing:
            logger.warning("Missing %d tasks in submission, adding fallback", len(missing))
            test_data = load_tasks(CHALLENGES_PATH)
            for tid in missing:
                submission[tid] = _fallback_submission(test_data[tid])

    # Write submission
    with open(OUTPUT_PATH, "w") as f:
        json.dump(submission, f)
    logger.info("Submission saved to %s (%d tasks)", OUTPUT_PATH, len(submission))
    logger.info("Total time: %.1fs", time.monotonic() - start)


if __name__ == "__main__":
    main()
