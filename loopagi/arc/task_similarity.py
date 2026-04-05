"""ARC-AGI Task Similarity Engine.

Computes feature vectors from ARC tasks and finds the most similar
solved tasks to use as few-shot examples in the refinement loop.

This is the RAG component of the ARC solver: instead of retrieving
text documents, we retrieve similar solved tasks.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loopagi.arc.grid_objects import find_objects
from loopagi.arc.grid_ops import (
    background_color,
    count_by_color,
    grid_shape,
    symmetry_report,
    unique_colors,
)
from loopagi.arc.perceiver import analyze_pair

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import ArcDataset, ArcTask, Grid

logger = logging.getLogger(__name__)


@dataclass
class TaskFeatures:
    """Feature vector extracted from an ARC task for similarity matching."""

    task_id: str

    # Grid dimension features
    avg_input_rows: float = 0.0
    avg_input_cols: float = 0.0
    avg_output_rows: float = 0.0
    avg_output_cols: float = 0.0

    # Shape relationship
    shape_changes: bool = False
    row_ratio: float = 1.0
    col_ratio: float = 1.0

    # Color features
    num_input_colors: float = 0.0
    num_output_colors: float = 0.0
    colors_added: int = 0
    colors_removed: int = 0

    # Object features
    avg_input_objects: float = 0.0
    avg_output_objects: float = 0.0
    object_count_delta: float = 0.0

    # Symmetry features
    input_has_symmetry: bool = False
    output_has_symmetry: bool = False
    gains_symmetry: bool = False

    # Structural features
    num_train_pairs: int = 0
    num_test_inputs: int = 0

    def to_vector(self) -> list[float]:
        """Convert features to a numeric vector for distance computation."""
        return [
            self.avg_input_rows / 30.0,
            self.avg_input_cols / 30.0,
            self.avg_output_rows / 30.0,
            self.avg_output_cols / 30.0,
            1.0 if self.shape_changes else 0.0,
            min(self.row_ratio, 5.0) / 5.0,
            min(self.col_ratio, 5.0) / 5.0,
            self.num_input_colors / 10.0,
            self.num_output_colors / 10.0,
            min(self.colors_added, 5) / 5.0,
            min(self.colors_removed, 5) / 5.0,
            min(self.avg_input_objects, 20) / 20.0,
            min(self.avg_output_objects, 20) / 20.0,
            min(abs(self.object_count_delta), 10) / 10.0,
            1.0 if self.input_has_symmetry else 0.0,
            1.0 if self.output_has_symmetry else 0.0,
            1.0 if self.gains_symmetry else 0.0,
            self.num_train_pairs / 10.0,
        ]


def extract_features(task: ArcTask) -> TaskFeatures:
    """Extract a feature vector from an ARC task.

    Uses the Perceiver's analysis functions to compute features
    from training pairs.
    """
    features = TaskFeatures(task_id=task.task_id)
    features.num_train_pairs = task.num_train
    features.num_test_inputs = task.num_test

    if not task.train:
        return features

    # Analyze all training pairs
    pair_analyses = [analyze_pair(p.input, p.output) for p in task.train]

    # Grid dimensions
    inp_rows = [pa.input_analysis.shape[0] for pa in pair_analyses]
    inp_cols = [pa.input_analysis.shape[1] for pa in pair_analyses]
    out_rows = [pa.output_analysis.shape[0] for pa in pair_analyses]
    out_cols = [pa.output_analysis.shape[1] for pa in pair_analyses]

    features.avg_input_rows = sum(inp_rows) / len(inp_rows)
    features.avg_input_cols = sum(inp_cols) / len(inp_cols)
    features.avg_output_rows = sum(out_rows) / len(out_rows)
    features.avg_output_cols = sum(out_cols) / len(out_cols)

    # Shape changes
    features.shape_changes = any(pa.shape_changed for pa in pair_analyses)
    if features.avg_input_rows > 0:
        features.row_ratio = features.avg_output_rows / features.avg_input_rows
    if features.avg_input_cols > 0:
        features.col_ratio = features.avg_output_cols / features.avg_input_cols

    # Colors
    inp_colors = [pa.input_analysis.num_colors for pa in pair_analyses]
    out_colors = [pa.output_analysis.num_colors for pa in pair_analyses]
    features.num_input_colors = sum(inp_colors) / len(inp_colors)
    features.num_output_colors = sum(out_colors) / len(out_colors)
    features.colors_added = sum(len(pa.colors_added) for pa in pair_analyses)
    features.colors_removed = sum(len(pa.colors_removed) for pa in pair_analyses)

    # Objects
    inp_objs = [pa.input_analysis.num_objects for pa in pair_analyses]
    out_objs = [pa.output_analysis.num_objects for pa in pair_analyses]
    features.avg_input_objects = sum(inp_objs) / len(inp_objs)
    features.avg_output_objects = sum(out_objs) / len(out_objs)
    features.object_count_delta = features.avg_output_objects - features.avg_input_objects

    # Symmetry
    features.input_has_symmetry = any(
        any(pa.input_analysis.symmetry.values()) for pa in pair_analyses
    )
    features.output_has_symmetry = any(
        any(pa.output_analysis.symmetry.values()) for pa in pair_analyses
    )
    features.gains_symmetry = (
        not features.input_has_symmetry and features.output_has_symmetry
    )

    return features


def cosine_distance(a: list[float], b: list[float]) -> float:
    """Compute cosine distance between two vectors. Returns 0.0-2.0."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 1.0
    similarity = dot / (norm_a * norm_b)
    return 1.0 - similarity


def euclidean_distance(a: list[float], b: list[float]) -> float:
    """Compute Euclidean distance between two vectors."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


@dataclass
class SimilarTask:
    """A task retrieved by similarity search."""

    task_id: str
    distance: float
    features: TaskFeatures

    @property
    def similarity(self) -> float:
        """Convert distance to similarity score (0.0-1.0)."""
        return max(0.0, 1.0 - self.distance)


@dataclass
class TaskIndex:
    """Index of task features for fast similarity search."""

    features: dict[str, TaskFeatures] = field(default_factory=dict)
    vectors: dict[str, list[float]] = field(default_factory=dict)

    @property
    def size(self) -> int:
        return len(self.features)

    def add(self, task_features: TaskFeatures) -> None:
        """Add a task to the index."""
        self.features[task_features.task_id] = task_features
        self.vectors[task_features.task_id] = task_features.to_vector()

    def search(
        self,
        query: TaskFeatures,
        k: int = 5,
        exclude: set[str] | None = None,
        metric: str = "cosine",
    ) -> list[SimilarTask]:
        """Find the k most similar tasks to the query.

        Args:
            query: Feature vector of the query task.
            k: Number of results to return.
            exclude: Task IDs to exclude from results.
            metric: Distance metric ('cosine' or 'euclidean').

        Returns:
            List of SimilarTask sorted by distance (ascending).
        """
        exclude = exclude or set()
        query_vec = query.to_vector()
        dist_fn = cosine_distance if metric == "cosine" else euclidean_distance

        results: list[SimilarTask] = []
        for task_id, vec in self.vectors.items():
            if task_id in exclude:
                continue
            dist = dist_fn(query_vec, vec)
            results.append(SimilarTask(
                task_id=task_id,
                distance=dist,
                features=self.features[task_id],
            ))

        results.sort(key=lambda r: r.distance)
        return results[:k]

    def summary(self) -> str:
        return f"TaskIndex: {self.size} tasks indexed"


def build_index(dataset: ArcDataset, max_tasks: int | None = None) -> TaskIndex:
    """Build a similarity index from an ARC dataset.

    Args:
        dataset: The ARC dataset to index.
        max_tasks: Optional limit on number of tasks to index.

    Returns:
        TaskIndex ready for similarity search.
    """
    index = TaskIndex()
    task_ids = dataset.task_ids()

    if max_tasks:
        task_ids = task_ids[:max_tasks]

    logger.info("Building task index for %d tasks...", len(task_ids))

    for i, task_id in enumerate(task_ids):
        task = dataset.get_task(task_id)
        features = extract_features(task)
        index.add(features)

        if (i + 1) % 100 == 0:
            logger.info("Indexed %d/%d tasks", i + 1, len(task_ids))

    logger.info(index.summary())
    return index


def save_index(index: TaskIndex, path: str) -> None:
    """Save a TaskIndex to disk as JSON.

    Args:
        path: File path to write the index to.
    """
    import json

    data: dict = {}
    for task_id, features in index.features.items():
        data[task_id] = {
            "vector": index.vectors[task_id],
            "shape_changes": features.shape_changes,
            "num_train_pairs": features.num_train_pairs,
            "avg_input_rows": features.avg_input_rows,
            "avg_input_cols": features.avg_input_cols,
            "avg_output_rows": features.avg_output_rows,
            "avg_output_cols": features.avg_output_cols,
            "row_ratio": features.row_ratio,
            "col_ratio": features.col_ratio,
            "num_input_colors": features.num_input_colors,
            "num_output_colors": features.num_output_colors,
            "colors_added": features.colors_added,
            "colors_removed": features.colors_removed,
            "avg_input_objects": features.avg_input_objects,
            "avg_output_objects": features.avg_output_objects,
            "object_count_delta": features.object_count_delta,
            "input_has_symmetry": features.input_has_symmetry,
            "output_has_symmetry": features.output_has_symmetry,
            "gains_symmetry": features.gains_symmetry,
            "num_test_inputs": features.num_test_inputs,
        }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=None, separators=(",", ":"))

    logger.info("Saved index (%d tasks) to %s", index.size, path)


def load_index(path: str) -> TaskIndex:
    """Load a TaskIndex from a JSON file on disk.

    Args:
        path: File path to read the index from.

    Returns:
        Reconstructed TaskIndex.
    """
    import json

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    index = TaskIndex()
    for task_id, entry in data.items():
        features = TaskFeatures(
            task_id=task_id,
            avg_input_rows=entry["avg_input_rows"],
            avg_input_cols=entry["avg_input_cols"],
            avg_output_rows=entry["avg_output_rows"],
            avg_output_cols=entry["avg_output_cols"],
            shape_changes=entry["shape_changes"],
            row_ratio=entry["row_ratio"],
            col_ratio=entry["col_ratio"],
            num_input_colors=entry["num_input_colors"],
            num_output_colors=entry["num_output_colors"],
            colors_added=entry["colors_added"],
            colors_removed=entry["colors_removed"],
            avg_input_objects=entry["avg_input_objects"],
            avg_output_objects=entry["avg_output_objects"],
            object_count_delta=entry["object_count_delta"],
            input_has_symmetry=entry["input_has_symmetry"],
            output_has_symmetry=entry["output_has_symmetry"],
            gains_symmetry=entry["gains_symmetry"],
            num_train_pairs=entry["num_train_pairs"],
            num_test_inputs=entry["num_test_inputs"],
        )
        index.features[task_id] = features
        index.vectors[task_id] = entry["vector"]

    logger.info("Loaded index (%d tasks) from %s", index.size, path)
    return index


def build_or_load_index(
    dataset: ArcDataset,
    cache_path: str,
    max_tasks: int | None = None,
) -> TaskIndex:
    """Build a task index or load from cache if available.

    Args:
        dataset: The ARC dataset to index.
        cache_path: Path to the cache file.
        max_tasks: Optional limit on number of tasks.

    Returns:
        TaskIndex ready for similarity search.
    """
    from pathlib import Path

    cache = Path(cache_path)
    if cache.exists():
        logger.info("Loading cached index from %s", cache_path)
        return load_index(cache_path)

    index = build_index(dataset, max_tasks=max_tasks)
    cache.parent.mkdir(parents=True, exist_ok=True)
    save_index(index, cache_path)
    return index


def find_similar_tasks(
    task: ArcTask,
    index: TaskIndex,
    k: int = 3,
) -> list[SimilarTask]:
    """Find the most similar tasks in the index to a given task.

    Args:
        task: The query task.
        index: The pre-built task index.
        k: Number of similar tasks to retrieve.

    Returns:
        List of SimilarTask sorted by similarity (most similar first).
    """
    query_features = extract_features(task)
    return index.search(
        query_features,
        k=k,
        exclude={task.task_id},
    )
