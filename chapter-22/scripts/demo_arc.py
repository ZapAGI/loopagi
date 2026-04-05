"""ARC-AGI Challenge: Phase 1 Demo.

Loads ARC-AGI-2 data, visualizes tasks, runs baseline solvers,
and generates a sample submission.json.

Usage:
    uv run python chapter-22/demo_arc.py
    uv run python chapter-22/demo_arc.py --task 0934a4d8
    uv run python chapter-22/demo_arc.py --solver most_common_output
    uv run python chapter-22/demo_arc.py --plot
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from loopagi.arc.arc_loader import load_default_datasets
from loopagi.arc.arc_runner import (
    IdentitySolver,
    MostCommonOutputSolver,
    generate_submission,
    run_solver,
)
from loopagi.arc.arc_visualizer import print_task


def main() -> None:
    parser = argparse.ArgumentParser(description="ARC-AGI Challenge Demo")
    parser.add_argument(
        "--task",
        type=str,
        default=None,
        help="Visualize a specific task by ID",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="evaluation",
        choices=["training", "evaluation"],
        help="Which dataset to use (default: evaluation)",
    )
    parser.add_argument(
        "--solver",
        type=str,
        default="identity",
        choices=["identity", "most_common_output"],
        help="Baseline solver to run (default: identity)",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Use matplotlib for visualization instead of terminal",
    )
    parser.add_argument(
        "--submit",
        type=str,
        default=None,
        help="Generate submission.json at this path",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of tasks to process",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    # Load datasets
    print("Loading ARC-AGI-2 datasets...")
    datasets = load_default_datasets(validate=False)

    for name, ds in datasets.items():
        print(f"  {ds.summary()}")

    if args.dataset not in datasets:
        print(f"\nError: Dataset '{args.dataset}' not found.")
        print(f"Available: {', '.join(datasets.keys())}")
        sys.exit(1)

    dataset = datasets[args.dataset]

    # Visualize a specific task
    if args.task:
        try:
            task = dataset.get_task(args.task)
        except KeyError:
            print(f"\nError: Task '{args.task}' not found in '{args.dataset}'.")
            print(f"Available: {', '.join(dataset.task_ids()[:10])}...")
            sys.exit(1)

        if args.plot:
            from loopagi.arc.arc_visualizer import plot_task
            plot_task(task, show_test_output=True)
        else:
            print_task(task, show_test_output=True)
        return

    # Run a baseline solver
    solvers = {
        "identity": IdentitySolver(),
        "most_common_output": MostCommonOutputSolver(),
    }
    solver = solvers[args.solver]

    task_ids = dataset.task_ids()
    if args.limit:
        task_ids = task_ids[:args.limit]

    print(f"\nRunning '{solver.name}' on {len(task_ids)} tasks from '{args.dataset}'...")
    result = run_solver(solver, dataset, task_ids=task_ids)
    print(f"\n{result.summary()}")

    # Generate submission if requested
    if args.submit:
        path = generate_submission(result.predictions, args.submit)
        print(f"\nSubmission written to {path}")


if __name__ == "__main__":
    main()
