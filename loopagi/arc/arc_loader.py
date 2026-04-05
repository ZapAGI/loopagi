"""ARC-AGI task loader.

Loads ARC-AGI-2 tasks from individual JSON files or combined challenge JSONs.
Validates grid structure, dimensions, and value ranges.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias

logger = logging.getLogger(__name__)

# Type aliases for clarity
Grid: TypeAlias = list[list[int]]

# ARC-AGI constraints
MIN_GRID_SIZE = 1
MAX_GRID_SIZE = 30
MIN_CELL_VALUE = 0
MAX_CELL_VALUE = 9


@dataclass(frozen=True)
class GridPair:
    """A single input/output grid pair."""

    input: Grid
    output: Grid

    @property
    def input_shape(self) -> tuple[int, int]:
        """Return (rows, cols) of the input grid."""
        if not self.input:
            return (0, 0)
        return (len(self.input), len(self.input[0]))

    @property
    def output_shape(self) -> tuple[int, int]:
        """Return (rows, cols) of the output grid."""
        if not self.output:
            return (0, 0)
        return (len(self.output), len(self.output[0]))


@dataclass(frozen=True)
class TestInput:
    """A test input grid (output may or may not be available)."""

    input: Grid
    output: Grid | None = None

    @property
    def input_shape(self) -> tuple[int, int]:
        """Return (rows, cols) of the input grid."""
        if not self.input:
            return (0, 0)
        return (len(self.input), len(self.input[0]))


@dataclass
class ArcTask:
    """A single ARC-AGI task with training pairs and test inputs."""

    task_id: str
    train: list[GridPair] = field(default_factory=list)
    test: list[TestInput] = field(default_factory=list)

    @property
    def num_train(self) -> int:
        return len(self.train)

    @property
    def num_test(self) -> int:
        return len(self.test)

    @property
    def has_test_outputs(self) -> bool:
        """Check if test outputs are available (for training/eval sets)."""
        return all(t.output is not None for t in self.test)

    def summary(self) -> str:
        """Return a brief summary of the task."""
        train_shapes = [
            f"{p.input_shape}->{p.output_shape}" for p in self.train
        ]
        test_shapes = [f"{t.input_shape}" for t in self.test]
        return (
            f"Task {self.task_id}: "
            f"{self.num_train} train ({', '.join(train_shapes)}), "
            f"{self.num_test} test ({', '.join(test_shapes)})"
        )


@dataclass
class ArcDataset:
    """A collection of ARC tasks (training set, eval set, etc.)."""

    name: str
    tasks: dict[str, ArcTask] = field(default_factory=dict)

    @property
    def num_tasks(self) -> int:
        return len(self.tasks)

    def get_task(self, task_id: str) -> ArcTask:
        """Get a task by ID. Raises KeyError if not found."""
        return self.tasks[task_id]

    def task_ids(self) -> list[str]:
        """Return sorted list of task IDs."""
        return sorted(self.tasks.keys())

    def summary(self) -> str:
        """Return a brief summary of the dataset."""
        if not self.tasks:
            return f"Dataset '{self.name}': empty"
        train_counts = [t.num_train for t in self.tasks.values()]
        test_counts = [t.num_test for t in self.tasks.values()]
        has_outputs = sum(
            1 for t in self.tasks.values() if t.has_test_outputs
        )
        return (
            f"Dataset '{self.name}': {self.num_tasks} tasks, "
            f"train pairs: {min(train_counts)}-{max(train_counts)}, "
            f"test inputs: {min(test_counts)}-{max(test_counts)}, "
            f"test outputs available: {has_outputs}/{self.num_tasks}"
        )


class ValidationError(Exception):
    """Raised when ARC task data fails validation."""


def validate_grid(grid: object, label: str = "grid") -> Grid:
    """Validate a grid is a rectangular matrix of ints 0-9, within size limits.

    Args:
        grid: The data to validate as a grid.
        label: Human-readable label for error messages.

    Returns:
        The validated grid.

    Raises:
        ValidationError: If the grid is invalid.
    """
    if not isinstance(grid, list) or not grid:
        raise ValidationError(f"{label}: must be a non-empty list of lists")

    rows = len(grid)
    if rows < MIN_GRID_SIZE or rows > MAX_GRID_SIZE:
        raise ValidationError(
            f"{label}: row count {rows} outside [{MIN_GRID_SIZE}, {MAX_GRID_SIZE}]"
        )

    cols = None
    for i, row in enumerate(grid):
        if not isinstance(row, list):
            raise ValidationError(f"{label}: row {i} is not a list")
        if cols is None:
            cols = len(row)
            if cols < MIN_GRID_SIZE or cols > MAX_GRID_SIZE:
                raise ValidationError(
                    f"{label}: col count {cols} outside [{MIN_GRID_SIZE}, {MAX_GRID_SIZE}]"
                )
        elif len(row) != cols:
            raise ValidationError(
                f"{label}: row {i} has {len(row)} cols, expected {cols}"
            )
        for j, val in enumerate(row):
            if not isinstance(val, int) or val < MIN_CELL_VALUE or val > MAX_CELL_VALUE:
                raise ValidationError(
                    f"{label}: cell [{i}][{j}] = {val!r} not in [{MIN_CELL_VALUE}, {MAX_CELL_VALUE}]"
                )

    return grid


def load_task_from_dict(task_id: str, data: dict, validate: bool = True) -> ArcTask:
    """Load an ARC task from a parsed JSON dictionary.

    Args:
        task_id: Unique identifier for the task.
        data: Dictionary with 'train' and 'test' keys.
        validate: Whether to validate grid contents.

    Returns:
        An ArcTask instance.

    Raises:
        ValidationError: If validation is enabled and data is invalid.
    """
    if "train" not in data:
        raise ValidationError(f"Task {task_id}: missing 'train' key")
    if "test" not in data:
        raise ValidationError(f"Task {task_id}: missing 'test' key")

    train_pairs: list[GridPair] = []
    for i, pair in enumerate(data["train"]):
        inp = pair.get("input")
        out = pair.get("output")
        if inp is None or out is None:
            raise ValidationError(
                f"Task {task_id}: train pair {i} missing input or output"
            )
        if validate:
            inp = validate_grid(inp, f"Task {task_id} train[{i}].input")
            out = validate_grid(out, f"Task {task_id} train[{i}].output")
        train_pairs.append(GridPair(input=inp, output=out))

    test_inputs: list[TestInput] = []
    for i, pair in enumerate(data["test"]):
        inp = pair.get("input")
        if inp is None:
            raise ValidationError(
                f"Task {task_id}: test pair {i} missing input"
            )
        if validate:
            inp = validate_grid(inp, f"Task {task_id} test[{i}].input")
        out = pair.get("output")
        if out is not None and validate:
            out = validate_grid(out, f"Task {task_id} test[{i}].output")
        test_inputs.append(TestInput(input=inp, output=out))

    return ArcTask(task_id=task_id, train=train_pairs, test=test_inputs)


def load_task_file(path: Path, validate: bool = True) -> ArcTask:
    """Load a single ARC task from an individual JSON file.

    The task ID is derived from the filename (without .json extension).

    Args:
        path: Path to the JSON file.
        validate: Whether to validate grid contents.

    Returns:
        An ArcTask instance.
    """
    path = Path(path)
    task_id = path.stem
    logger.debug(f"Loading task {task_id} from {path}")

    with open(path) as f:
        data = json.load(f)

    return load_task_from_dict(task_id, data, validate=validate)


def load_combined_json(path: Path, validate: bool = True) -> ArcDataset:
    """Load tasks from a combined challenges JSON (Kaggle format).

    The combined JSON maps task_id -> {train: [...], test: [...]}.

    Args:
        path: Path to the combined JSON file.
        validate: Whether to validate grid contents.

    Returns:
        An ArcDataset instance.
    """
    path = Path(path)
    name = path.stem.replace("arc-agi_", "").replace("_challenges", "")
    logger.info(f"Loading combined dataset from {path}")

    with open(path) as f:
        data = json.load(f)

    tasks: dict[str, ArcTask] = {}
    for task_id, task_data in data.items():
        tasks[task_id] = load_task_from_dict(task_id, task_data, validate=validate)

    dataset = ArcDataset(name=name, tasks=tasks)
    logger.info(dataset.summary())
    return dataset


def load_task_directory(directory: Path, validate: bool = True) -> ArcDataset:
    """Load all ARC tasks from a directory of individual JSON files.

    Args:
        directory: Path to the directory containing .json task files.
        validate: Whether to validate grid contents.

    Returns:
        An ArcDataset instance.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory}")

    name = directory.name
    logger.info(f"Loading tasks from directory {directory}")

    tasks: dict[str, ArcTask] = {}
    json_files = sorted(directory.glob("*.json"))
    for path in json_files:
        task = load_task_file(path, validate=validate)
        tasks[task.task_id] = task

    dataset = ArcDataset(name=name, tasks=tasks)
    logger.info(dataset.summary())
    return dataset


def load_arc_dataset(
    training_dir: Path | None = None,
    eval_dir: Path | None = None,
    combined_json: Path | None = None,
    data_root: Path | None = None,
    validate: bool = True,
) -> dict[str, ArcDataset]:
    """Load ARC-AGI-2 datasets with flexible path resolution.

    Supports three modes:
    1. Explicit paths: provide training_dir and/or eval_dir
    2. Combined JSON: provide a Kaggle-format combined JSON file
    3. Auto-detect: provide data_root and detect the directory structure

    Args:
        training_dir: Path to directory with training task JSON files.
        eval_dir: Path to directory with evaluation task JSON files.
        combined_json: Path to a combined challenges JSON file.
        data_root: Root directory to auto-detect ARC-AGI-2 structure.
        validate: Whether to validate grid contents.

    Returns:
        Dictionary mapping dataset names to ArcDataset instances.
    """
    datasets: dict[str, ArcDataset] = {}

    if combined_json is not None:
        combined_json = Path(combined_json)
        ds = load_combined_json(combined_json, validate=validate)
        datasets[ds.name] = ds
        return datasets

    if data_root is not None:
        data_root = Path(data_root)
        # Auto-detect ARC-AGI-2 repo structure: data/training/ and data/evaluation/
        for subdir_name in ("training", "evaluation"):
            subdir = data_root / "data" / subdir_name
            if not subdir.is_dir():
                subdir = data_root / subdir_name
            if subdir.is_dir():
                ds = load_task_directory(subdir, validate=validate)
                datasets[subdir_name] = ds
        # Also check for combined JSONs
        for json_path in data_root.glob("arc-agi_*_challenges.json"):
            ds = load_combined_json(json_path, validate=validate)
            if ds.name not in datasets:
                datasets[ds.name] = ds
        return datasets

    if training_dir is not None:
        datasets["training"] = load_task_directory(
            Path(training_dir), validate=validate
        )
    if eval_dir is not None:
        datasets["evaluation"] = load_task_directory(
            Path(eval_dir), validate=validate
        )

    return datasets


# Default data paths relative to the project root
_PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_DATA_ROOT = _PROJECT_ROOT / "chapter-21" / "data" / "ARC-AGI-2"
DEFAULT_COMBINED_EVAL = _PROJECT_ROOT / "chapter-21" / "data" / "arc-agi_evaluation_challenges.json"


def load_default_datasets(validate: bool = True) -> dict[str, ArcDataset]:
    """Load datasets from default locations in the repo.

    Tries the cloned ARC-AGI-2 repo first, then falls back to combined JSONs.

    Returns:
        Dictionary mapping dataset names to ArcDataset instances.
    """
    if DEFAULT_DATA_ROOT.is_dir():
        return load_arc_dataset(data_root=DEFAULT_DATA_ROOT, validate=validate)

    datasets: dict[str, ArcDataset] = {}
    if DEFAULT_COMBINED_EVAL.is_file():
        ds = load_combined_json(DEFAULT_COMBINED_EVAL, validate=validate)
        datasets[ds.name] = ds
    return datasets
