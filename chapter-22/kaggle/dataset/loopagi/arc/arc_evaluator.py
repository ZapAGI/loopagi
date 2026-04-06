"""ARC-AGI evaluator.

Scores predictions against ground truth with exact grid matching.
Supports pass@2 evaluation (2 attempts per test output).
Generates evaluation reports with per-task and aggregate statistics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import ArcDataset, ArcTask, Grid

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result of evaluating predictions for a single ARC task."""

    task_id: str
    num_test: int
    correct: list[bool] = field(default_factory=list)
    best_attempts: list[int] = field(default_factory=list)
    similarity_scores: list[float] = field(default_factory=list)

    @property
    def solved(self) -> bool:
        """Task is solved if ALL test outputs are correct."""
        return len(self.correct) == self.num_test and all(self.correct)

    @property
    def partial_score(self) -> float:
        """Fraction of test outputs that were correct."""
        if not self.correct:
            return 0.0
        return sum(self.correct) / self.num_test

    @property
    def num_correct(self) -> int:
        return sum(self.correct)


@dataclass
class EvalReport:
    """Aggregate evaluation report across all tasks."""

    dataset_name: str
    results: dict[str, TaskResult] = field(default_factory=dict)

    @property
    def num_tasks(self) -> int:
        return len(self.results)

    @property
    def num_solved(self) -> int:
        return sum(1 for r in self.results.values() if r.solved)

    @property
    def accuracy(self) -> float:
        """Fraction of tasks fully solved."""
        if not self.results:
            return 0.0
        return self.num_solved / self.num_tasks

    @property
    def partial_accuracy(self) -> float:
        """Average partial score across all tasks."""
        if not self.results:
            return 0.0
        return sum(r.partial_score for r in self.results.values()) / self.num_tasks

    def summary(self) -> str:
        """Return a formatted summary of the evaluation."""
        lines = [
            f"=== Evaluation Report: {self.dataset_name} ===",
            f"Tasks:          {self.num_tasks}",
            f"Solved:         {self.num_solved}/{self.num_tasks} "
            f"({self.accuracy:.1%})",
            f"Partial score:  {self.partial_accuracy:.1%}",
        ]
        if self.num_solved > 0:
            solved_ids = sorted(
                tid for tid, r in self.results.items() if r.solved
            )
            lines.append(f"Solved tasks:   {', '.join(solved_ids)}")
        return "\n".join(lines)

    def detailed_report(self) -> str:
        """Return a detailed per-task report."""
        lines = [self.summary(), "", "--- Per-Task Results ---"]
        for task_id in sorted(self.results.keys()):
            r = self.results[task_id]
            status = "SOLVED" if r.solved else f"PARTIAL ({r.num_correct}/{r.num_test})"
            lines.append(f"  {task_id}: {status}")
            if r.similarity_scores:
                sims = ", ".join(f"{s:.2f}" for s in r.similarity_scores)
                lines.append(f"    Similarity: [{sims}]")
        return "\n".join(lines)


def grids_match(predicted: Grid, expected: Grid) -> bool:
    """Check if two grids are an exact match.

    Args:
        predicted: The predicted output grid.
        expected: The expected output grid.

    Returns:
        True if grids have identical dimensions and values.
    """
    if len(predicted) != len(expected):
        return False
    for pred_row, exp_row in zip(predicted, expected):
        if len(pred_row) != len(exp_row):
            return False
        if pred_row != exp_row:
            return False
    return True


def grid_similarity(predicted: Grid, expected: Grid) -> float:
    """Compute cell-level similarity between two grids.

    Returns the fraction of matching cells. If dimensions differ,
    compares the overlapping region and penalizes size mismatch.

    Args:
        predicted: The predicted output grid.
        expected: The expected output grid.

    Returns:
        Similarity score between 0.0 and 1.0.
    """
    if not predicted or not expected:
        return 0.0

    pred_rows, pred_cols = len(predicted), len(predicted[0])
    exp_rows, exp_cols = len(expected), len(expected[0])

    # Total cells in expected grid
    total_cells = exp_rows * exp_cols
    if total_cells == 0:
        return 1.0 if pred_rows == 0 and pred_cols == 0 else 0.0

    # Compare overlapping region (handle jagged rows from LLM code)
    overlap_rows = min(pred_rows, exp_rows)
    matching = 0

    for i in range(overlap_rows):
        pred_row_len = len(predicted[i]) if i < len(predicted) else 0
        exp_row_len = len(expected[i]) if i < len(expected) else 0
        overlap_cols = min(pred_row_len, exp_row_len)
        for j in range(overlap_cols):
            if predicted[i][j] == expected[i][j]:
                matching += 1

    return matching / total_cells


def evaluate_task(
    task: ArcTask,
    predictions: list[list[Grid]],
    max_attempts: int = 2,
) -> TaskResult:
    """Evaluate predictions for a single task using pass@k.

    Args:
        task: The ARC task with ground truth test outputs.
        predictions: For each test input, a list of up to max_attempts predicted grids.
        max_attempts: Maximum attempts per test output (default 2 for ARC).

    Returns:
        TaskResult with correctness and similarity data.

    Raises:
        ValueError: If task has no test outputs to evaluate against.
    """
    if not task.has_test_outputs:
        raise ValueError(
            f"Task {task.task_id} has no test outputs for evaluation"
        )

    result = TaskResult(task_id=task.task_id, num_test=task.num_test)

    for test_idx, test in enumerate(task.test):
        expected = test.output
        if expected is None:
            result.correct.append(False)
            result.best_attempts.append(0)
            result.similarity_scores.append(0.0)
            continue

        # Get predictions for this test input
        if test_idx < len(predictions):
            attempts = predictions[test_idx][:max_attempts]
        else:
            attempts = []

        # Check each attempt
        is_correct = False
        best_attempt = 0
        best_similarity = 0.0

        for attempt_idx, pred in enumerate(attempts):
            sim = grid_similarity(pred, expected)
            if sim > best_similarity:
                best_similarity = sim
                best_attempt = attempt_idx + 1

            if grids_match(pred, expected):
                is_correct = True
                best_attempt = attempt_idx + 1
                best_similarity = 1.0
                break

        result.correct.append(is_correct)
        result.best_attempts.append(best_attempt)
        result.similarity_scores.append(best_similarity)

    return result


def evaluate_dataset(
    dataset: ArcDataset,
    all_predictions: dict[str, list[list[Grid]]],
    max_attempts: int = 2,
) -> EvalReport:
    """Evaluate predictions for an entire dataset.

    Args:
        dataset: The ARC dataset with ground truth.
        all_predictions: Maps task_id -> list of prediction attempts per test input.
        max_attempts: Maximum attempts per test output.

    Returns:
        EvalReport with per-task and aggregate results.
    """
    report = EvalReport(dataset_name=dataset.name)

    for task_id in dataset.task_ids():
        task = dataset.get_task(task_id)

        if not task.has_test_outputs:
            logger.warning(f"Task {task_id} has no test outputs, skipping")
            continue

        predictions = all_predictions.get(task_id, [])
        if not predictions:
            # No predictions: mark as failed
            result = TaskResult(
                task_id=task_id,
                num_test=task.num_test,
                correct=[False] * task.num_test,
                best_attempts=[0] * task.num_test,
                similarity_scores=[0.0] * task.num_test,
            )
        else:
            result = evaluate_task(task, predictions, max_attempts=max_attempts)

        report.results[task_id] = result

    logger.info(report.summary())
    return report
