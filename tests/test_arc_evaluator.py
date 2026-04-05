"""Tests for loopagi.arc.arc_evaluator module."""

from __future__ import annotations

import pytest

from loopagi.arc.arc_evaluator import (
    EvalReport,
    TaskResult,
    evaluate_dataset,
    evaluate_task,
    grid_similarity,
    grids_match,
)
from loopagi.arc.arc_loader import (
    ArcDataset,
    ArcTask,
    GridPair,
    TestInput,
)


# --- Fixtures ---


@pytest.fixture
def simple_task() -> ArcTask:
    """A simple task with known test outputs."""
    return ArcTask(
        task_id="test_001",
        train=[
            GridPair(input=[[0, 1], [1, 0]], output=[[1, 0], [0, 1]]),
        ],
        test=[
            TestInput(input=[[2, 3], [3, 2]], output=[[3, 2], [2, 3]]),
        ],
    )


@pytest.fixture
def multi_test_task() -> ArcTask:
    """A task with multiple test inputs."""
    return ArcTask(
        task_id="test_002",
        train=[
            GridPair(input=[[0]], output=[[1]]),
        ],
        test=[
            TestInput(input=[[2]], output=[[3]]),
            TestInput(input=[[4]], output=[[5]]),
        ],
    )


# --- grids_match tests ---


class TestGridsMatch:
    """Tests for exact grid matching."""

    def test_identical_grids(self) -> None:
        assert grids_match([[0, 1], [2, 3]], [[0, 1], [2, 3]]) is True

    def test_different_values(self) -> None:
        assert grids_match([[0, 1]], [[0, 2]]) is False

    def test_different_rows(self) -> None:
        assert grids_match([[0]], [[0], [1]]) is False

    def test_different_cols(self) -> None:
        assert grids_match([[0, 1]], [[0]]) is False

    def test_empty_grids(self) -> None:
        assert grids_match([], []) is True

    def test_single_cell(self) -> None:
        assert grids_match([[5]], [[5]]) is True

    def test_large_grid(self) -> None:
        g = [[i * 10 + j for j in range(10)] for i in range(10)]
        assert grids_match(g, g) is True


# --- grid_similarity tests ---


class TestGridSimilarity:
    """Tests for cell-level similarity scoring."""

    def test_identical_grids(self) -> None:
        assert grid_similarity([[0, 1]], [[0, 1]]) == 1.0

    def test_no_match(self) -> None:
        assert grid_similarity([[0, 0]], [[1, 1]]) == 0.0

    def test_half_match(self) -> None:
        assert grid_similarity([[0, 1]], [[0, 0]]) == 0.5

    def test_different_sizes_overlap(self) -> None:
        # Predicted 1x1, expected 2x2: only 1 of 4 cells can match
        sim = grid_similarity([[0]], [[0, 1], [2, 3]])
        assert sim == 0.25

    def test_empty_expected(self) -> None:
        assert grid_similarity([[0]], []) == 0.0

    def test_empty_predicted(self) -> None:
        assert grid_similarity([], [[0]]) == 0.0


# --- TaskResult tests ---


class TestTaskResult:
    """Tests for TaskResult dataclass."""

    def test_solved(self) -> None:
        r = TaskResult(task_id="t", num_test=2, correct=[True, True])
        assert r.solved is True

    def test_not_solved(self) -> None:
        r = TaskResult(task_id="t", num_test=2, correct=[True, False])
        assert r.solved is False

    def test_partial_score(self) -> None:
        r = TaskResult(task_id="t", num_test=4, correct=[True, False, True, False])
        assert r.partial_score == 0.5

    def test_empty_result(self) -> None:
        r = TaskResult(task_id="t", num_test=1)
        assert r.solved is False
        assert r.partial_score == 0.0


# --- evaluate_task tests ---


class TestEvaluateTask:
    """Tests for evaluating a single task."""

    def test_correct_prediction(self, simple_task: ArcTask) -> None:
        predictions = [
            [[[3, 2], [2, 3]]],  # test 0: 1 attempt, correct
        ]
        result = evaluate_task(simple_task, predictions)
        assert result.solved is True
        assert result.correct == [True]

    def test_wrong_prediction(self, simple_task: ArcTask) -> None:
        predictions = [
            [[[0, 0], [0, 0]]],  # wrong
        ]
        result = evaluate_task(simple_task, predictions)
        assert result.solved is False
        assert result.correct == [False]

    def test_second_attempt_correct(self, simple_task: ArcTask) -> None:
        predictions = [
            [
                [[0, 0], [0, 0]],     # attempt 1: wrong
                [[3, 2], [2, 3]],     # attempt 2: correct
            ],
        ]
        result = evaluate_task(simple_task, predictions)
        assert result.solved is True
        assert result.best_attempts == [2]

    def test_no_predictions(self, simple_task: ArcTask) -> None:
        result = evaluate_task(simple_task, [])
        assert result.solved is False

    def test_multi_test_all_correct(self, multi_test_task: ArcTask) -> None:
        predictions = [
            [[[3]]],  # test 0: correct
            [[[5]]],  # test 1: correct
        ]
        result = evaluate_task(multi_test_task, predictions)
        assert result.solved is True
        assert result.num_correct == 2

    def test_multi_test_partial(self, multi_test_task: ArcTask) -> None:
        predictions = [
            [[[3]]],  # test 0: correct
            [[[0]]],  # test 1: wrong
        ]
        result = evaluate_task(multi_test_task, predictions)
        assert result.solved is False
        assert result.partial_score == 0.5

    def test_task_without_outputs_raises(self) -> None:
        task = ArcTask(
            task_id="no_out",
            train=[GridPair(input=[[0]], output=[[1]])],
            test=[TestInput(input=[[2]])],
        )
        with pytest.raises(ValueError, match="no test outputs"):
            evaluate_task(task, [])

    def test_similarity_tracked(self, simple_task: ArcTask) -> None:
        # Predict a grid that partially matches
        # Expected: [[3, 2], [2, 3]], Predicted: [[3, 0], [2, 3]]
        # Matches: [0][0]=3, [1][0]=2, [1][1]=3 -> 3 of 4 cells
        predictions = [
            [[[3, 0], [2, 3]]],
        ]
        result = evaluate_task(simple_task, predictions)
        assert result.similarity_scores[0] == pytest.approx(0.75)


# --- EvalReport tests ---


class TestEvalReport:
    """Tests for aggregate evaluation reports."""

    def test_accuracy(self) -> None:
        report = EvalReport(
            dataset_name="test",
            results={
                "t1": TaskResult(task_id="t1", num_test=1, correct=[True]),
                "t2": TaskResult(task_id="t2", num_test=1, correct=[False]),
            },
        )
        assert report.accuracy == 0.5
        assert report.num_solved == 1

    def test_empty_report(self) -> None:
        report = EvalReport(dataset_name="empty")
        assert report.accuracy == 0.0
        assert report.num_tasks == 0

    def test_summary_format(self) -> None:
        report = EvalReport(
            dataset_name="test",
            results={
                "t1": TaskResult(task_id="t1", num_test=1, correct=[True]),
            },
        )
        s = report.summary()
        assert "test" in s
        assert "1/1" in s

    def test_detailed_report(self) -> None:
        report = EvalReport(
            dataset_name="test",
            results={
                "t1": TaskResult(
                    task_id="t1",
                    num_test=1,
                    correct=[True],
                    similarity_scores=[1.0],
                ),
            },
        )
        detail = report.detailed_report()
        assert "SOLVED" in detail


# --- evaluate_dataset tests ---


class TestEvaluateDataset:
    """Tests for evaluating across a dataset."""

    def test_evaluate_dataset(self, simple_task: ArcTask) -> None:
        dataset = ArcDataset(
            name="test",
            tasks={"test_001": simple_task},
        )
        predictions = {
            "test_001": [
                [[[3, 2], [2, 3]]],  # correct
            ],
        }
        report = evaluate_dataset(dataset, predictions)
        assert report.num_solved == 1
        assert report.accuracy == 1.0

    def test_missing_predictions(self, simple_task: ArcTask) -> None:
        dataset = ArcDataset(
            name="test",
            tasks={"test_001": simple_task},
        )
        report = evaluate_dataset(dataset, {})
        assert report.num_solved == 0
