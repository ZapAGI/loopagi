"""Tests for loopagi.arc.arc_runner module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from loopagi.arc.arc_loader import ArcDataset, ArcTask, GridPair, TestInput
from loopagi.arc.arc_runner import (
    IdentitySolver,
    MostCommonOutputSolver,
    RunResult,
    generate_submission,
    run_solver,
)


# --- Fixtures ---


@pytest.fixture
def mirror_task() -> ArcTask:
    """Task where output is a horizontal mirror of input."""
    return ArcTask(
        task_id="mirror_001",
        train=[
            GridPair(input=[[1, 2], [3, 4]], output=[[2, 1], [4, 3]]),
            GridPair(input=[[5, 6], [7, 8]], output=[[6, 5], [8, 7]]),
        ],
        test=[
            TestInput(input=[[0, 1], [2, 3]], output=[[1, 0], [3, 2]]),
        ],
    )


@pytest.fixture
def identity_task() -> ArcTask:
    """Task where output equals input (identity solver wins)."""
    return ArcTask(
        task_id="identity_001",
        train=[
            GridPair(input=[[1, 2]], output=[[1, 2]]),
        ],
        test=[
            TestInput(input=[[3, 4]], output=[[3, 4]]),
        ],
    )


@pytest.fixture
def small_dataset(mirror_task: ArcTask, identity_task: ArcTask) -> ArcDataset:
    """A small dataset with 2 tasks."""
    return ArcDataset(
        name="test_set",
        tasks={
            mirror_task.task_id: mirror_task,
            identity_task.task_id: identity_task,
        },
    )


# --- IdentitySolver tests ---


class TestIdentitySolver:
    """Tests for the identity baseline solver."""

    def test_returns_input(self, mirror_task: ArcTask) -> None:
        solver = IdentitySolver()
        results = solver.solve(mirror_task)
        assert len(results) == 1
        assert results[0][0] == mirror_task.test[0].input

    def test_name(self) -> None:
        assert IdentitySolver().name == "identity"

    def test_identity_task_solved(self, identity_task: ArcTask) -> None:
        solver = IdentitySolver()
        results = solver.solve(identity_task)
        assert results[0][0] == [[3, 4]]


# --- MostCommonOutputSolver tests ---


class TestMostCommonOutputSolver:
    """Tests for the most-common-output baseline solver."""

    def test_returns_training_output(self, mirror_task: ArcTask) -> None:
        solver = MostCommonOutputSolver()
        results = solver.solve(mirror_task)
        assert len(results) == 1
        # Should return one of the training outputs
        training_outputs = [p.output for p in mirror_task.train]
        assert results[0][0] in training_outputs

    def test_name(self) -> None:
        assert MostCommonOutputSolver().name == "most_common_output"


# --- run_solver tests ---


class TestRunSolver:
    """Tests for the run_solver orchestrator."""

    def test_run_identity(self, small_dataset: ArcDataset) -> None:
        solver = IdentitySolver()
        result = run_solver(solver, small_dataset)
        assert len(result.predictions) == 2
        assert len(result.errors) == 0
        assert result.eval_report is not None

    def test_run_with_task_subset(self, small_dataset: ArcDataset) -> None:
        solver = IdentitySolver()
        result = run_solver(
            solver, small_dataset, task_ids=["identity_001"]
        )
        assert len(result.predictions) == 1
        assert "identity_001" in result.predictions

    def test_timing_recorded(self, small_dataset: ArcDataset) -> None:
        solver = IdentitySolver()
        result = run_solver(solver, small_dataset)
        assert result.total_time > 0
        assert result.avg_time > 0

    def test_identity_solves_identity_task(
        self, small_dataset: ArcDataset
    ) -> None:
        solver = IdentitySolver()
        result = run_solver(solver, small_dataset)
        report = result.eval_report
        assert report is not None
        # Identity solver should solve the identity task
        assert report.results["identity_001"].solved is True
        # But not the mirror task
        assert report.results["mirror_001"].solved is False

    def test_missing_task_id(self, small_dataset: ArcDataset) -> None:
        solver = IdentitySolver()
        result = run_solver(
            solver, small_dataset, task_ids=["nonexistent"]
        )
        assert "nonexistent" in result.errors

    def test_summary(self, small_dataset: ArcDataset) -> None:
        solver = IdentitySolver()
        result = run_solver(solver, small_dataset)
        s = result.summary()
        assert "identity" in s
        assert "test_set" in s


# --- generate_submission tests ---


class TestGenerateSubmission:
    """Tests for Kaggle submission.json generation."""

    def test_basic_submission(self) -> None:
        predictions = {
            "task_001": [
                [[[1, 2], [3, 4]], [[5, 6], [7, 8]]],  # 2 attempts
            ],
        }
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = generate_submission(predictions, f.name)
            data = json.loads(Path(f.name).read_text())

        assert "task_001" in data
        assert len(data["task_001"]) == 1
        assert "attempt_1" in data["task_001"][0]
        assert "attempt_2" in data["task_001"][0]

    def test_single_attempt_duplicated(self) -> None:
        predictions = {
            "task_001": [
                [[[1, 2]]],  # Only 1 attempt
            ],
        }
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = generate_submission(predictions, f.name)
            data = json.loads(Path(f.name).read_text())

        # Should have 2 attempts (first duplicated)
        assert "attempt_1" in data["task_001"][0]
        assert "attempt_2" in data["task_001"][0]
        assert data["task_001"][0]["attempt_1"] == data["task_001"][0]["attempt_2"]

    def test_empty_predictions_fallback(self) -> None:
        predictions = {
            "task_001": [
                [],  # No attempts
            ],
        }
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = generate_submission(predictions, f.name)
            data = json.loads(Path(f.name).read_text())

        assert data["task_001"][0]["attempt_1"] == [[0]]


# --- RunResult tests ---


class TestRunResult:
    """Tests for RunResult dataclass."""

    def test_total_time(self) -> None:
        r = RunResult(
            solver_name="test",
            dataset_name="test",
            solve_times={"a": 1.0, "b": 2.0},
        )
        assert r.total_time == 3.0
        assert r.avg_time == 1.5

    def test_empty_times(self) -> None:
        r = RunResult(solver_name="test", dataset_name="test")
        assert r.total_time == 0.0
        assert r.avg_time == 0.0
