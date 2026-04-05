"""Test-Time Training (TTT) script for ARC-AGI tasks.

Runs in a separate Python 3.12 venv with PyTorch+CUDA+Unsloth.
Called as a subprocess from loopagi/arc/ttt.py.

Input: JSON file with task data (training pairs + test inputs)
Output: JSON file with predicted grids

Usage:
    chapter-22/ttt_venv/bin/python chapter-22/ttt_train.py \
        --input /tmp/ttt_task.json \
        --output /tmp/ttt_predictions.json \
        --model unsloth/Qwen3-8B-unsloth-bnb-4bit \
        --steps 50 \
        --rank 8
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import time
from pathlib import Path

# VRAM safety: limit PyTorch to 14GB, leave 2GB for desktop compositor
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "max_split_size_mb:512")
_MAX_VRAM_GB = 14.0

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Type aliases
Grid = list[list[int]]
TrainPair = tuple[Grid, Grid]


# ---------------------------------------------------------------------------
# Data augmentation
# ---------------------------------------------------------------------------


def rotate_cw(grid: Grid) -> Grid:
    """Rotate grid 90 degrees clockwise."""
    if not grid:
        return []
    rows, cols = len(grid), len(grid[0])
    return [[grid[rows - 1 - r][c] for r in range(rows)] for c in range(cols)]


def rotate_ccw(grid: Grid) -> Grid:
    """Rotate grid 90 degrees counter-clockwise."""
    if not grid:
        return []
    rows, cols = len(grid), len(grid[0])
    return [[grid[r][c] for r in range(rows)] for c in range(cols - 1, -1, -1)]


def rotate_180(grid: Grid) -> Grid:
    """Rotate grid 180 degrees."""
    return [row[::-1] for row in reversed(grid)]


def reflect_h(grid: Grid) -> Grid:
    """Reflect grid horizontally (flip top-bottom)."""
    return list(reversed(grid))


def reflect_v(grid: Grid) -> Grid:
    """Reflect grid vertically (flip left-right)."""
    return [row[::-1] for row in grid]


D4_AUGMENTATIONS = [
    ("identity", lambda g: g, lambda g: g),
    ("rot90", rotate_cw, rotate_ccw),
    ("rot180", rotate_180, rotate_180),
    ("rot270", rotate_ccw, rotate_cw),
    ("flip_h", reflect_h, reflect_h),
    ("flip_v", reflect_v, reflect_v),
    ("rot90_flip_h", lambda g: reflect_h(rotate_cw(g)), lambda g: rotate_ccw(reflect_h(g))),
    ("rot90_flip_v", lambda g: reflect_v(rotate_cw(g)), lambda g: rotate_ccw(reflect_v(g))),
]


def permute_colors(grid: Grid, mapping: dict[int, int]) -> Grid:
    """Apply a color permutation to a grid."""
    return [[mapping.get(v, v) for v in row] for row in grid]


def random_color_permutation(grid: Grid) -> tuple[Grid, dict[int, int]]:
    """Create a random color permutation (excluding background 0)."""
    colors = sorted({v for row in grid for v in row if v != 0})
    if len(colors) < 2:
        return grid, {}
    shuffled = colors[:]
    random.shuffle(shuffled)
    mapping = {c: s for c, s in zip(colors, shuffled)}
    mapping[0] = 0
    return permute_colors(grid, mapping), mapping


def compact_grid(grid: Grid) -> str:
    """Compact grid string for prompts."""
    return "[" + ",".join(
        "[" + ",".join(str(v) for v in row) + "]" for row in grid
    ) + "]"


# ---------------------------------------------------------------------------
# Leave-one-out task generation
# ---------------------------------------------------------------------------


def generate_loo_tasks(
    train_pairs: list[TrainPair],
) -> list[dict]:
    """Generate leave-one-out training tasks.

    For N training pairs, creates N tasks where each pair is held out as "test".
    Each task has (N-1) training pairs and 1 test pair with known answer.
    """
    tasks = []
    for held_out_idx in range(len(train_pairs)):
        train = [p for i, p in enumerate(train_pairs) if i != held_out_idx]
        test_inp, test_out = train_pairs[held_out_idx]
        tasks.append({
            "train_pairs": train,
            "test_input": test_inp,
            "test_output": test_out,
        })
    return tasks


def augment_tasks(
    loo_tasks: list[dict],
    n_color_perms: int = 3,
) -> list[dict]:
    """Augment leave-one-out tasks with D4 symmetry + color permutations."""
    augmented = []
    for task in loo_tasks:
        pairs = task["train_pairs"]
        test_in = task["test_input"]
        test_out = task["test_output"]

        # D4 augmentations
        for name, fwd, _ in D4_AUGMENTATIONS:
            aug_pairs = [(fwd(inp), fwd(out)) for inp, out in pairs]
            augmented.append({
                "train_pairs": aug_pairs,
                "test_input": fwd(test_in),
                "test_output": fwd(test_out),
                "aug": name,
            })

        # Color permutations on original orientation
        all_colors = set()
        for inp, out in pairs:
            for row in inp:
                all_colors.update(row)
            for row in out:
                all_colors.update(row)
        non_bg = sorted(c for c in all_colors if c != 0)

        for _ in range(min(n_color_perms, max(1, len(non_bg) - 1))):
            shuffled = non_bg[:]
            random.shuffle(shuffled)
            mapping = {c: s for c, s in zip(non_bg, shuffled)}
            mapping[0] = 0
            aug_pairs = [
                (permute_colors(inp, mapping), permute_colors(out, mapping))
                for inp, out in pairs
            ]
            augmented.append({
                "train_pairs": aug_pairs,
                "test_input": permute_colors(test_in, mapping),
                "test_output": permute_colors(test_out, mapping),
                "aug": "color_perm",
            })

    return augmented


# ---------------------------------------------------------------------------
# Format training data for fine-tuning
# ---------------------------------------------------------------------------


def format_training_example(task: dict) -> dict:
    """Format a single task as a chat training example."""
    pairs = task["train_pairs"]
    test_in = task["test_input"]
    test_out = task["test_output"]

    # Build prompt with training pairs
    prompt_parts = ["Solve this ARC puzzle. Given input/output examples, predict the test output.\n"]
    for i, (inp, out) in enumerate(pairs, 1):
        prompt_parts.append(f"Example {i}: {compact_grid(inp)} -> {compact_grid(out)}")
    prompt_parts.append(f"\nTest input: {compact_grid(test_in)}")
    prompt_parts.append("Reply with ONLY the output grid as a JSON array.")

    user_msg = "\n".join(prompt_parts)
    assistant_msg = compact_grid(test_out)

    return {
        "conversations": [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": assistant_msg},
        ]
    }


# ---------------------------------------------------------------------------
# LoRA training
# ---------------------------------------------------------------------------


def train_lora(
    model_name: str,
    training_data: list[dict],
    max_steps: int = 50,
    lora_rank: int = 8,
    lora_alpha: int = 16,
    learning_rate: float = 2e-4,
    batch_size: int = 2,
) -> tuple:
    """Fine-tune a LoRA adapter on the training data.

    Returns (model, tokenizer) with the adapter applied.
    """
    import torch
    # Limit VRAM to leave room for desktop compositor (~2GB)
    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(
            _MAX_VRAM_GB / (torch.cuda.get_device_properties(0).total_memory / 1e9)
        )

    from unsloth import FastModel
    from trl import SFTTrainer, SFTConfig

    logger.info("Loading model: %s", model_name)
    model, tokenizer = FastModel.from_pretrained(
        model_name=model_name,
        max_seq_length=4096,
        load_in_4bit=True,
        load_in_8bit=False,
        full_finetuning=False,
    )

    logger.info("Applying LoRA: rank=%d, alpha=%d", lora_rank, lora_alpha)
    model = FastModel.get_peft_model(
        model,
        r=lora_rank,
        lora_alpha=lora_alpha,
        lora_dropout=0.0,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )

    # Format data for SFTTrainer
    from unsloth.chat_templates import get_chat_template
    tokenizer = get_chat_template(tokenizer, chat_template="qwen-2.5")

    formatted = []
    for item in training_data:
        text = tokenizer.apply_chat_template(
            item["conversations"],
            tokenize=False,
            add_generation_prompt=False,
        )
        formatted.append({"text": text})

    from datasets import Dataset
    dataset = Dataset.from_list(formatted)

    logger.info("Training on %d examples for %d steps...", len(formatted), max_steps)
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=SFTConfig(
            output_dir="/tmp/ttt_output",
            max_steps=max_steps,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=max(1, 4 // batch_size),
            learning_rate=learning_rate,
            warmup_steps=5,
            logging_steps=10,
            bf16=True,
            optim="adamw_8bit",
            seed=42,
            dataset_text_field="text",
            max_seq_length=4096,
            report_to="none",
        ),
    )

    trainer.train()
    logger.info("Training complete")

    return model, tokenizer


# ---------------------------------------------------------------------------
# Inference with adapted model
# ---------------------------------------------------------------------------


def predict_with_model(
    model,
    tokenizer,
    train_pairs: list[TrainPair],
    test_input: Grid,
    temperature: float = 0.1,
) -> Grid | None:
    """Generate a prediction using the fine-tuned model."""
    import torch

    prompt_parts = ["Solve this ARC puzzle. Given input/output examples, predict the test output.\n"]
    for i, (inp, out) in enumerate(train_pairs, 1):
        prompt_parts.append(f"Example {i}: {compact_grid(inp)} -> {compact_grid(out)}")
    prompt_parts.append(f"\nTest input: {compact_grid(test_input)}")
    prompt_parts.append("Reply with ONLY the output grid as a JSON array.")

    messages = [{"role": "user", "content": "\n".join(prompt_parts)}]
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True,
        enable_thinking=False,
    )

    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    # Estimate output size: rows * cols * ~4 tokens/cell + overhead
    rows = len(test_input)
    cols = len(test_input[0]) if test_input else 0
    max_tokens = min(max(rows * cols * 4 + 100, 512), 2048)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=max(temperature, 0.01),
            do_sample=True,
            use_cache=True,
        )

    response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    return parse_grid(response)


def _majority_vote(candidates: list[Grid]) -> Grid:
    """Cell-wise majority vote across multiple grid predictions."""
    if not candidates:
        return []
    if len(candidates) == 1:
        return candidates[0]
    from collections import Counter
    rows = len(candidates[0])
    cols = len(candidates[0][0]) if candidates[0] else 0
    voted: Grid = []
    for r in range(rows):
        row = []
        for c in range(cols):
            vals = []
            for cand in candidates:
                if r < len(cand) and c < len(cand[r]):
                    vals.append(cand[r][c])
            if vals:
                row.append(Counter(vals).most_common(1)[0][0])
            else:
                row.append(0)
        voted.append(row)
    return voted


def parse_grid(response: str) -> Grid | None:
    """Parse a grid from model response."""
    import re
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


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="ARC-AGI Test-Time Training")
    parser.add_argument("--input", required=True, help="Input task JSON file")
    parser.add_argument("--output", required=True, help="Output predictions JSON file")
    parser.add_argument("--model", default="unsloth/Qwen3-8B-unsloth-bnb-4bit")
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--rank", type=int, default=8)
    parser.add_argument("--alpha", type=int, default=16)
    parser.add_argument("--color-perms", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--n-predictions", type=int, default=1,
                        help="Number of predictions per test input (pass-at-K)")
    args = parser.parse_args()

    start = time.monotonic()

    # Load task data
    with open(args.input) as f:
        task_data = json.load(f)

    train_pairs = [
        (p["input"], p["output"]) for p in task_data["train"]
    ]
    test_inputs = [t["input"] for t in task_data["test"]]
    task_id = task_data.get("task_id", "unknown")

    logger.info("[%s] TTT: %d train pairs, %d test inputs", task_id, len(train_pairs), len(test_inputs))

    # Generate leave-one-out tasks + augment
    loo_tasks = generate_loo_tasks(train_pairs)
    augmented = augment_tasks(loo_tasks, n_color_perms=args.color_perms)
    logger.info("[%s] TTT: %d LOO tasks -> %d augmented examples", task_id, len(loo_tasks), len(augmented))

    # Format for training
    training_data = [format_training_example(t) for t in augmented]

    # Train LoRA adapter
    model, tokenizer = train_lora(
        model_name=args.model,
        training_data=training_data,
        max_steps=args.steps,
        lora_rank=args.rank,
        lora_alpha=args.alpha,
        batch_size=args.batch_size,
    )

    # Generate predictions for each test input (pass-at-K)
    n_preds = max(1, args.n_predictions)
    # Temperature schedule for diverse predictions
    temps = [0.1] if n_preds == 1 else [
        0.1 + 0.15 * k for k in range(n_preds)
    ]
    predictions = []  # Single best prediction per test input
    all_candidates = []  # All K predictions per test input
    for i, test_in in enumerate(test_inputs):
        logger.info("[%s] TTT: predicting test input %d/%d (K=%d)",
                    task_id, i + 1, len(test_inputs), n_preds)
        candidates = []
        for k in range(n_preds):
            temp = temps[k] if k < len(temps) else 0.5
            pred = predict_with_model(
                model, tokenizer, train_pairs, test_in, temperature=temp)
            if pred is not None:
                candidates.append(pred)
        if candidates:
            best = _majority_vote(candidates) if len(candidates) > 1 else candidates[0]
            predictions.append(best)
            all_candidates.append(candidates)
        else:
            logger.warning("[%s] TTT: no valid predictions for test %d", task_id, i + 1)
            predictions.append(test_in)
            all_candidates.append([])

    elapsed = time.monotonic() - start
    logger.info("[%s] TTT complete: %d predictions (%d candidates each) in %.1fs",
                task_id, len(predictions), n_preds, elapsed)

    # Save predictions
    result = {
        "task_id": task_id,
        "predictions": predictions,
        "all_candidates": all_candidates,
        "elapsed_seconds": round(elapsed, 1),
        "n_training_examples": len(training_data),
        "n_predictions_per_test": n_preds,
        "steps": args.steps,
        "rank": args.rank,
    }
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    logger.info("[%s] TTT: saved to %s", task_id, args.output)

    # Cleanup GPU memory
    import torch
    del model, tokenizer
    torch.cuda.empty_cache()
    import gc
    gc.collect()


if __name__ == "__main__":
    main()
