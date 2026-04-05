"""Diagnose why near-miss tasks can't be solved.

Loads the top near-miss tasks and analyzes:
1. What is the "best program" the pipeline produces?
2. Is it just identity (return input)?
3. What are the exact wrong cells?
4. Why does evolution/cell-fix fail?
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loopagi.arc.arc_loader import load_default_datasets
from loopagi.arc.cell_fixer import identify_wrong_cells


def grid_similarity(expected: list, actual: list) -> float:
    """Cell-level similarity."""
    if not expected or not actual:
        return 0.0
    if len(expected) != len(actual) or len(expected[0]) != len(actual[0]):
        return 0.0
    total = len(expected) * len(expected[0])
    matching = sum(
        1 for r in range(len(expected))
        for c in range(len(expected[0]))
        if expected[r][c] == actual[r][c]
    )
    return matching / total if total else 0.0


def analyze_identity(task) -> None:
    """Check how similar input/output are (identity similarity)."""
    print(f"\n{'='*60}")
    print(f"Task: {task.task_id}")
    print(f"Train pairs: {len(task.train)}, Test inputs: {len(task.test)}")

    for i, pair in enumerate(task.train):
        inp = pair.input
        out = pair.output
        inp_rows, inp_cols = len(inp), len(inp[0])
        out_rows, out_cols = len(out), len(out[0])

        print(f"\n  Pair {i+1}:")
        print(f"    Input:  {inp_rows}x{inp_cols}")
        print(f"    Output: {out_rows}x{out_cols}")

        if inp_rows == out_rows and inp_cols == out_cols:
            sim = grid_similarity(out, inp)
            wrong = identify_wrong_cells(out, inp)
            print(f"    Identity similarity: {sim*100:.1f}%")
            print(f"    Wrong cells (identity): {len(wrong)}")

            if wrong:
                # Group wrong cells by pattern
                changes: dict[tuple[int, int], int] = {}
                for wc in wrong:
                    key = (wc.actual, wc.expected)
                    changes[key] = changes.get(key, 0) + 1

                print(f"    Change patterns:")
                for (from_val, to_val), count in sorted(changes.items(), key=lambda x: -x[1]):
                    print(f"      {from_val} -> {to_val}: {count} cells")

                # Show spatial distribution
                wrong_positions = [(wc.row, wc.col) for wc in wrong]
                min_r = min(r for r, c in wrong_positions)
                max_r = max(r for r, c in wrong_positions)
                min_c = min(c for r, c in wrong_positions)
                max_c = max(c for r, c in wrong_positions)
                print(f"    Wrong cell region: rows {min_r}-{max_r}, cols {min_c}-{max_c}")
        else:
            print(f"    Shape differs: identity won't work")
            # Check if output is a subset/transformation of input
            print(f"    Size ratio: {out_rows*out_cols}/{inp_rows*inp_cols} = {out_rows*out_cols/(inp_rows*inp_cols):.2f}")


def analyze_transduction_near_miss(task) -> None:
    """Check how close transduction gets to 100% on training."""
    # The transduction verification requires 100% on ALL training pairs
    # Let's see what similarity it achieves
    for i, pair in enumerate(task.train):
        inp = pair.input
        out = pair.output
        if len(inp) == len(out) and len(inp[0]) == len(out[0]):
            sim = grid_similarity(out, inp)
            if sim >= 0.95:
                wrong = identify_wrong_cells(out, inp)
                print(f"\n  Transduction analysis (pair {i+1}):")
                print(f"    If LLM predicts identity: {sim*100:.1f}% (needs 100%)")
                print(f"    Gap: {len(wrong)} cells need to change")
                print(f"    These {len(wrong)} cells are the ENTIRE puzzle")


def main() -> None:
    print("Loading ARC-AGI-2 datasets...")
    datasets = load_default_datasets(validate=False)
    eval_ds = datasets["evaluation"]

    # Top near-miss tasks from the 10-task validation
    near_miss_ids = [
        "8e5c0c38",   # 98.7% with qwen3:8b
        "135a2760",   # 98.6%
        "b99e7126",   # 97.1%
        "dbff022c",   # 94.8%
        "c4d067a0",   # 94.7%
        "a25697e4",   # 94.2%
    ]

    for task_id in near_miss_ids:
        task = eval_ds.get_task(task_id)
        analyze_identity(task)
        analyze_transduction_near_miss(task)


if __name__ == "__main__":
    main()
