"""Tests for loopagi.arc.arc_loader module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from loopagi.arc.arc_loader import (
    ArcDataset,
    ArcTask,
    GridPair,
    TestInput,
    ValidationError,
    load_combined_json,
    load_default_datasets,
    load_task_directory,
    load_task_file,
    load_task_from_dict,
    validate_grid,
)


# --- Fixtures ---


@pytest.fixture
def simple_task_dict() -> dict:
    """A minimal valid ARC task dictionary."""
    return {
        "train": [
            {
                "input": [[0, 1], [1, 0]],
                "output": [[1, 0], [0, 1]],
            },
            {
                "input": [[2, 3], [3, 2]],
                "output": [[3, 2], [2, 3]],
            },
        ],
        "test": [
            {
                "input": [[4, 5], [5, 4]],
                "output": [[5, 4], [4, 5]],
            },
        ],
    }


@pytest.fixture
def task_no_test_output() -> dict:
    """A task dict where test pairs have no output (eval challenge format)."""
    return {
        "train": [
            {"input": [[1, 2], [3, 4]], "output": [[4, 3], [2, 1]]},
        ],
        "test": [
            {"input": [[5, 6], [7, 8]]},
        ],
    }


@pytest.fixture
def tmp_task_file(simple_task_dict: dict) -> Path:
    """Write a task to a temporary JSON file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", prefix="abc123_", delete=False
    ) as f:
        json.dump(simple_task_dict, f)
        return Path(f.name)


@pytest.fixture
def tmp_task_dir(simple_task_dict: dict) -> Path:
    """Create a temporary directory with multiple task files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, task_id in enumerate(["aaa111", "bbb222", "ccc333"]):
            path = Path(tmpdir) / f"{task_id}.json"
            # Vary the task slightly
            task = simple_task_dict.copy()
            path.write_text(json.dumps(task))
        yield Path(tmpdir)


@pytest.fixture
def tmp_combined_json(simple_task_dict: dict) -> Path:
    """Create a combined challenges JSON file."""
    combined = {
        "task_001": simple_task_dict,
        "task_002": simple_task_dict,
    }
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        prefix="arc-agi_test_challenges",
        delete=False,
    ) as f:
        json.dump(combined, f)
        return Path(f.name)


# --- validate_grid tests ---


class TestValidateGrid:
    """Tests for the validate_grid function."""

    def test_valid_2x2_grid(self) -> None:
        grid = [[0, 1], [2, 3]]
        result = validate_grid(grid)
        assert result == grid

    def test_valid_1x1_grid(self) -> None:
        grid = [[0]]
        assert validate_grid(grid) == grid

    def test_valid_max_values(self) -> None:
        grid = [[9, 9], [9, 9]]
        assert validate_grid(grid) == grid

    def test_empty_grid_raises(self) -> None:
        with pytest.raises(ValidationError, match="non-empty list"):
            validate_grid([])

    def test_non_list_raises(self) -> None:
        with pytest.raises(ValidationError, match="non-empty list"):
            validate_grid("not a grid")

    def test_non_list_row_raises(self) -> None:
        with pytest.raises(ValidationError, match="row 0 is not a list"):
            validate_grid(["not a row"])

    def test_jagged_grid_raises(self) -> None:
        with pytest.raises(ValidationError, match="row 1 has 3 cols"):
            validate_grid([[0, 1], [0, 1, 2]])

    def test_value_too_high_raises(self) -> None:
        with pytest.raises(ValidationError, match="not in"):
            validate_grid([[0, 10]])

    def test_value_too_low_raises(self) -> None:
        with pytest.raises(ValidationError, match="not in"):
            validate_grid([[-1, 0]])

    def test_non_int_value_raises(self) -> None:
        with pytest.raises(ValidationError, match="not in"):
            validate_grid([[0.5, 1]])

    def test_oversized_grid_raises(self) -> None:
        big = [[0] * 31]
        with pytest.raises(ValidationError, match="col count 31"):
            validate_grid(big)

    def test_too_many_rows_raises(self) -> None:
        big = [[0]] * 31
        with pytest.raises(ValidationError, match="row count 31"):
            validate_grid(big)

    def test_label_in_error_message(self) -> None:
        with pytest.raises(ValidationError, match="my_grid"):
            validate_grid([], label="my_grid")


# --- load_task_from_dict tests ---


class TestLoadTaskFromDict:
    """Tests for loading a task from a dictionary."""

    def test_basic_load(self, simple_task_dict: dict) -> None:
        task = load_task_from_dict("test_id", simple_task_dict)
        assert task.task_id == "test_id"
        assert task.num_train == 2
        assert task.num_test == 1

    def test_train_pairs_correct(self, simple_task_dict: dict) -> None:
        task = load_task_from_dict("test_id", simple_task_dict)
        assert task.train[0].input == [[0, 1], [1, 0]]
        assert task.train[0].output == [[1, 0], [0, 1]]

    def test_test_output_present(self, simple_task_dict: dict) -> None:
        task = load_task_from_dict("test_id", simple_task_dict)
        assert task.has_test_outputs is True
        assert task.test[0].output == [[5, 4], [4, 5]]

    def test_test_output_absent(self, task_no_test_output: dict) -> None:
        task = load_task_from_dict("test_id", task_no_test_output)
        assert task.has_test_outputs is False
        assert task.test[0].output is None

    def test_missing_train_key_raises(self) -> None:
        with pytest.raises(ValidationError, match="missing 'train'"):
            load_task_from_dict("t", {"test": []})

    def test_missing_test_key_raises(self) -> None:
        with pytest.raises(ValidationError, match="missing 'test'"):
            load_task_from_dict("t", {"train": []})

    def test_skip_validation(self) -> None:
        bad_data = {
            "train": [{"input": [[99]], "output": [[99]]}],
            "test": [{"input": [[99]]}],
        }
        task = load_task_from_dict("t", bad_data, validate=False)
        assert task.train[0].input == [[99]]

    def test_summary(self, simple_task_dict: dict) -> None:
        task = load_task_from_dict("abc", simple_task_dict)
        s = task.summary()
        assert "abc" in s
        assert "2 train" in s


# --- GridPair and TestInput tests ---


class TestDataClasses:
    """Tests for GridPair and TestInput dataclasses."""

    def test_grid_pair_shape(self) -> None:
        pair = GridPair(input=[[0, 1, 2]], output=[[3], [4]])
        assert pair.input_shape == (1, 3)
        assert pair.output_shape == (2, 1)

    def test_test_input_shape(self) -> None:
        ti = TestInput(input=[[0, 1], [2, 3], [4, 5]])
        assert ti.input_shape == (3, 2)

    def test_empty_grid_shape(self) -> None:
        pair = GridPair(input=[], output=[])
        assert pair.input_shape == (0, 0)
        assert pair.output_shape == (0, 0)


# --- File and directory loading tests ---


class TestFileLoading:
    """Tests for loading from files and directories."""

    def test_load_task_file(self, tmp_task_file: Path) -> None:
        task = load_task_file(tmp_task_file)
        assert task.num_train == 2
        # Task ID is derived from filename
        assert task.task_id == tmp_task_file.stem

    def test_load_task_directory(self, tmp_task_dir: Path) -> None:
        dataset = load_task_directory(tmp_task_dir)
        assert dataset.num_tasks == 3
        assert "aaa111" in dataset.task_ids()

    def test_load_combined_json(self, tmp_combined_json: Path) -> None:
        dataset = load_combined_json(tmp_combined_json)
        assert dataset.num_tasks == 2
        assert "task_001" in dataset.task_ids()

    def test_missing_directory_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_task_directory(Path("/nonexistent"))


# --- ArcDataset tests ---


class TestArcDataset:
    """Tests for ArcDataset."""

    def test_get_task(self, simple_task_dict: dict) -> None:
        task = load_task_from_dict("tid", simple_task_dict)
        ds = ArcDataset(name="test", tasks={"tid": task})
        assert ds.get_task("tid").task_id == "tid"

    def test_get_task_missing_raises(self) -> None:
        ds = ArcDataset(name="test")
        with pytest.raises(KeyError):
            ds.get_task("nonexistent")

    def test_summary_empty(self) -> None:
        ds = ArcDataset(name="empty")
        assert "empty" in ds.summary()

    def test_summary_with_tasks(self, simple_task_dict: dict) -> None:
        task = load_task_from_dict("t1", simple_task_dict)
        ds = ArcDataset(name="test", tasks={"t1": task})
        s = ds.summary()
        assert "1 tasks" in s
        assert "test" in s


# --- Integration: load real data ---


class TestDefaultDatasets:
    """Tests that load the actual ARC-AGI-2 data if available."""

    def test_load_default_training(self) -> None:
        datasets = load_default_datasets(validate=False)
        if "training" in datasets:
            assert datasets["training"].num_tasks == 1000
        else:
            pytest.skip("Training data not available")

    def test_load_default_evaluation(self) -> None:
        datasets = load_default_datasets(validate=False)
        if "evaluation" in datasets:
            assert datasets["evaluation"].num_tasks == 120
        else:
            pytest.skip("Evaluation data not available")

    def test_training_task_structure(self) -> None:
        datasets = load_default_datasets(validate=False)
        if "training" not in datasets:
            pytest.skip("Training data not available")
        ds = datasets["training"]
        task = ds.get_task(ds.task_ids()[0])
        assert task.num_train >= 1
        assert task.num_test >= 1

    def test_eval_task_has_outputs(self) -> None:
        datasets = load_default_datasets(validate=False)
        if "evaluation" not in datasets:
            pytest.skip("Evaluation data not available")
        ds = datasets["evaluation"]
        task = ds.get_task(ds.task_ids()[0])
        # Eval tasks from the repo should have outputs
        assert task.has_test_outputs is True
