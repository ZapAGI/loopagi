"""ARC-AGI runner.

Orchestrates solving ARC tasks: loads data, runs a solver, evaluates results,
and generates submission.json for Kaggle.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import ArcDataset, ArcTask, Grid

from loopagi.arc.arc_evaluator import EvalReport, evaluate_dataset
from loopagi.arc.arc_loader import ArcDataset, load_default_datasets

logger = logging.getLogger(__name__)


class ArcSolver(Protocol):
    """Protocol for ARC task solvers.

    Any solver must implement this interface to be used with the runner.
    """

    def solve(self, task: ArcTask, max_attempts: int = 2) -> list[list[Grid]]:
        """Solve an ARC task.

        Args:
            task: The ARC task to solve.
            max_attempts: Maximum number of output attempts per test input.

        Returns:
            For each test input, a list of up to max_attempts predicted grids.
        """
        ...

    @property
    def name(self) -> str:
        """Human-readable name of the solver."""
        ...


class IdentitySolver:
    """Baseline solver that returns the input grid unchanged.

    Useful for testing the pipeline and establishing a lower bound.
    """

    @property
    def name(self) -> str:
        return "identity"

    def solve(self, task: ArcTask, max_attempts: int = 2) -> list[list[Grid]]:
        """Return the test input as the prediction (identity transform)."""
        results: list[list[Grid]] = []
        for test in task.test:
            # Return the input grid as-is, up to max_attempts copies
            results.append([test.input] * min(max_attempts, 1))
        return results


class MostCommonOutputSolver:
    """Baseline solver that returns the most common training output.

    If all training outputs have the same shape, returns the first one.
    Otherwise returns the training output whose shape best matches the test input.
    """

    @property
    def name(self) -> str:
        return "most_common_output"

    def solve(self, task: ArcTask, max_attempts: int = 2) -> list[list[Grid]]:
        """Return the best-matching training output for each test input."""
        results: list[list[Grid]] = []

        for test in task.test:
            test_rows, test_cols = test.input_shape
            best_output = task.train[0].output

            # Find training output with shape closest to test input
            best_diff = float("inf")
            for pair in task.train:
                out_rows, out_cols = pair.output_shape
                diff = abs(out_rows - test_rows) + abs(out_cols - test_cols)
                if diff < best_diff:
                    best_diff = diff
                    best_output = pair.output

            results.append([best_output])
        return results


@dataclass
class RunResult:
    """Result of running a solver on a dataset."""

    solver_name: str
    dataset_name: str
    predictions: dict[str, list[list[Grid]]] = field(default_factory=dict)
    solve_times: dict[str, float] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    eval_report: EvalReport | None = None

    @property
    def total_time(self) -> float:
        return sum(self.solve_times.values())

    @property
    def avg_time(self) -> float:
        if not self.solve_times:
            return 0.0
        return self.total_time / len(self.solve_times)

    def summary(self) -> str:
        """Return a formatted summary."""
        lines = [
            f"=== Run Summary: {self.solver_name} on {self.dataset_name} ===",
            f"Tasks attempted: {len(self.predictions) + len(self.errors)}",
            f"Tasks completed: {len(self.predictions)}",
            f"Tasks errored:   {len(self.errors)}",
            f"Total time:      {self.total_time:.1f}s",
            f"Avg time/task:   {self.avg_time:.2f}s",
        ]
        if self.eval_report:
            lines.append("")
            lines.append(self.eval_report.summary())
        return "\n".join(lines)


def run_solver(
    solver: ArcSolver,
    dataset: ArcDataset,
    max_attempts: int = 2,
    task_ids: list[str] | None = None,
    timeout_per_task: float | None = None,
) -> RunResult:
    """Run a solver on all tasks in a dataset.

    Args:
        solver: The solver to use.
        dataset: The dataset to solve.
        max_attempts: Maximum attempts per test output.
        task_ids: Optional subset of task IDs to solve. Solves all if None.
        timeout_per_task: Max seconds per task (None for no limit).

    Returns:
        RunResult with predictions, timing, and evaluation data.
    """
    result = RunResult(
        solver_name=solver.name,
        dataset_name=dataset.name,
    )

    ids_to_solve = task_ids if task_ids else dataset.task_ids()
    total = len(ids_to_solve)

    logger.info(
        f"Running {solver.name} on {total} tasks from '{dataset.name}'"
    )

    for idx, task_id in enumerate(ids_to_solve):
        try:
            task = dataset.get_task(task_id)
        except KeyError:
            result.errors[task_id] = f"Task not found in dataset"
            continue

        logger.debug(f"[{idx + 1}/{total}] Solving {task_id}...")
        start = time.monotonic()

        try:
            predictions = solver.solve(task, max_attempts=max_attempts)
            elapsed = time.monotonic() - start

            if timeout_per_task and elapsed > timeout_per_task:
                result.errors[task_id] = f"Timeout ({elapsed:.1f}s > {timeout_per_task}s)"
                continue

            result.predictions[task_id] = predictions
            result.solve_times[task_id] = elapsed

        except Exception as e:
            elapsed = time.monotonic() - start
            result.solve_times[task_id] = elapsed
            result.errors[task_id] = f"{type(e).__name__}: {e}"
            logger.error(f"Error solving {task_id}: {e}")

    # Evaluate only attempted tasks (not the full dataset)
    attempted_tasks = {
        tid: dataset.get_task(tid)
        for tid in result.predictions
        if dataset.get_task(tid).has_test_outputs
    }
    if attempted_tasks:
        eval_subset = ArcDataset(name=dataset.name, tasks=attempted_tasks)
        result.eval_report = evaluate_dataset(
            eval_subset, result.predictions, max_attempts=max_attempts
        )

    logger.info(result.summary())
    return result


def generate_submission(
    predictions: dict[str, list[list[Grid]]],
    output_path: Path | str = "submission.json",
) -> Path:
    """Generate a Kaggle-format submission.json.

    Format: {task_id: [{"attempt_1": grid, "attempt_2": grid}, ...]}
    Each task has a list of test outputs. Each test output has up to 2 attempts.

    Args:
        predictions: Maps task_id -> list of prediction attempts per test input.
        output_path: Path to write the submission JSON.

    Returns:
        Path to the written file.
    """
    output_path = Path(output_path)
    submission: dict[str, list[dict[str, Grid]]] = {}

    for task_id, test_predictions in predictions.items():
        task_outputs: list[dict[str, Grid]] = []
        for attempts in test_predictions:
            attempt_dict: dict[str, Grid] = {}
            for i, grid in enumerate(attempts[:2]):
                attempt_dict[f"attempt_{i + 1}"] = grid
            # Ensure at least 2 attempts (duplicate first if needed)
            if len(attempt_dict) == 1 and "attempt_1" in attempt_dict:
                attempt_dict["attempt_2"] = attempt_dict["attempt_1"]
            elif not attempt_dict:
                attempt_dict = {"attempt_1": [[0]], "attempt_2": [[0]]}
            task_outputs.append(attempt_dict)
        submission[task_id] = task_outputs

    with open(output_path, "w") as f:
        json.dump(submission, f, indent=2)

    logger.info(f"Submission written to {output_path} ({len(submission)} tasks)")
    return output_path


def run_baseline(
    dataset_name: str = "evaluation",
    solver_name: str = "identity",
) -> RunResult:
    """Quick-start: run a baseline solver on a dataset.

    Args:
        dataset_name: Which dataset to use ('training' or 'evaluation').
        solver_name: Which baseline solver ('identity' or 'most_common_output').

    Returns:
        RunResult with evaluation data.
    """
    datasets = load_default_datasets()

    if dataset_name not in datasets:
        available = ", ".join(datasets.keys())
        raise ValueError(
            f"Dataset '{dataset_name}' not found. Available: {available}"
        )

    dataset = datasets[dataset_name]

    solvers: dict[str, ArcSolver] = {
        "identity": IdentitySolver(),
        "most_common_output": MostCommonOutputSolver(),
    }

    if solver_name not in solvers:
        available = ", ".join(solvers.keys())
        raise ValueError(
            f"Solver '{solver_name}' not found. Available: {available}"
        )

    solver = solvers[solver_name]
    return run_solver(solver, dataset)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("Running baseline solvers on ARC-AGI-2...\n")

    for solver_name in ("identity", "most_common_output"):
        try:
            result = run_baseline(
                dataset_name="evaluation",
                solver_name=solver_name,
            )
            print(result.summary())
            print()
        except Exception as e:
            print(f"Error running {solver_name}: {e}\n")
