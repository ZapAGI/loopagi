"""ARC-AGI Challenge: Multi-Agent Solver Demo.

Runs the full LLM-powered refinement loop on ARC tasks.
Works with Ollama (real inference) or mock mode (no GPU needed).

Usage:
    uv run python chapter-22/demo_solver.py
    uv run python chapter-22/demo_solver.py --model qwen3:8b --limit 5
    uv run python chapter-22/demo_solver.py --task 0a1d4ef5
    uv run python chapter-22/demo_solver.py --dataset training --limit 10
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loopagi.arc.arc_loader import load_default_datasets
from loopagi.arc.arc_visualizer import print_task
from loopagi.arc.llm_bridge import create_llm_bridge, solve_task_with_llm


def main() -> None:
    parser = argparse.ArgumentParser(description="ARC-AGI Multi-Agent Solver Demo")
    parser.add_argument("--model", type=str, default="qwen3:8b", help="Ollama model")
    parser.add_argument("--task", type=str, default=None, help="Solve a specific task by ID")
    parser.add_argument("--dataset", type=str, default="training", choices=["training", "evaluation"])
    parser.add_argument("--limit", type=int, default=3, help="Max tasks to attempt")
    parser.add_argument("--max-hyp", type=int, default=3, help="Max hypotheses per task")
    parser.add_argument("--max-iter", type=int, default=3, help="Max refinement iterations")
    parser.add_argument("--show-task", action="store_true", help="Visualize each task before solving")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    # Load data
    print("Loading ARC-AGI-2 datasets...")
    datasets = load_default_datasets(validate=False)
    if args.dataset not in datasets:
        print(f"Dataset '{args.dataset}' not found. Available: {', '.join(datasets.keys())}")
        sys.exit(1)
    dataset = datasets[args.dataset]
    print(f"  {dataset.summary()}\n")

    # Create LLM bridge
    bridge = create_llm_bridge(model=args.model)
    mode = "MOCK" if bridge.is_mock else args.model
    print(f"LLM: {mode}\n")

    # Select tasks
    if args.task:
        task_ids = [args.task]
    else:
        task_ids = dataset.task_ids()[:args.limit]

    # Solve
    solved_count = 0
    total_count = len(task_ids)

    for i, task_id in enumerate(task_ids):
        try:
            task = dataset.get_task(task_id)
        except KeyError:
            print(f"Task '{task_id}' not found.")
            continue

        print(f"{'=' * 60}")
        print(f"[{i + 1}/{total_count}] Task: {task_id}")
        print(f"  Train pairs: {task.num_train}, Test inputs: {task.num_test}")

        if args.show_task:
            print_task(task, show_test_output=False)

        output = solve_task_with_llm(
            task, bridge,
            max_hypotheses=args.max_hyp,
            max_iterations=args.max_iter,
        )

        result = output["result"]
        status = "SOLVED" if result.solved else "UNSOLVED"
        print(f"  Result: {status}")
        print(f"  Iterations: {result.num_iterations}")
        print(f"  Best similarity: {result.best_similarity:.1%}")
        print(f"  Time: {result.total_seconds:.1f}s")

        if result.best_program:
            print(f"  Best hypothesis: {result.best_program.hypothesis[:80]}")

        if result.solved:
            solved_count += 1
        print()

    # Summary
    print(f"{'=' * 60}")
    print(f"=== Final Results ===")
    print(f"Solved: {solved_count}/{total_count} ({solved_count/max(total_count,1):.0%})")
    print(f"{bridge.stats()}")


if __name__ == "__main__":
    main()
