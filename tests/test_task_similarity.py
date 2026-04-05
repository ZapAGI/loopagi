"""Tests for loopagi.arc.task_similarity module."""

from __future__ import annotations

import pytest

from loopagi.arc.arc_loader import ArcTask, GridPair, TestInput
from loopagi.arc.task_similarity import (
    SimilarTask,
    TaskFeatures,
    TaskIndex,
    build_index,
    build_or_load_index,
    cosine_distance,
    euclidean_distance,
    extract_features,
    find_similar_tasks,
    load_index,
    save_index,
)


# --- Fixtures ---


@pytest.fixture
def identity_task() -> ArcTask:
    return ArcTask(
        task_id="identity",
        train=[
            GridPair(input=[[1, 2], [3, 4]], output=[[1, 2], [3, 4]]),
            GridPair(input=[[5, 6]], output=[[5, 6]]),
        ],
        test=[TestInput(input=[[7, 8]])],
    )


@pytest.fixture
def mirror_task() -> ArcTask:
    return ArcTask(
        task_id="mirror",
        train=[
            GridPair(input=[[1, 2], [3, 4]], output=[[3, 4], [1, 2]]),
            GridPair(input=[[5, 6], [7, 8]], output=[[7, 8], [5, 6]]),
        ],
        test=[TestInput(input=[[0, 1], [2, 3]])],
    )


@pytest.fixture
def scale_task() -> ArcTask:
    return ArcTask(
        task_id="scale",
        train=[
            GridPair(
                input=[[1]],
                output=[[1, 1], [1, 1]],
            ),
            GridPair(
                input=[[2]],
                output=[[2, 2], [2, 2]],
            ),
        ],
        test=[TestInput(input=[[3]])],
    )


# --- Feature Extraction Tests ---


class TestExtractFeatures:
    def test_basic_extraction(self, identity_task: ArcTask) -> None:
        f = extract_features(identity_task)
        assert f.task_id == "identity"
        assert f.num_train_pairs == 2
        assert f.num_test_inputs == 1
        assert f.shape_changes is False

    def test_shape_change_detected(self, scale_task: ArcTask) -> None:
        f = extract_features(scale_task)
        assert f.shape_changes is True
        assert f.row_ratio == pytest.approx(2.0)
        assert f.col_ratio == pytest.approx(2.0)

    def test_same_shape_task(self, mirror_task: ArcTask) -> None:
        f = extract_features(mirror_task)
        assert f.shape_changes is False
        assert f.row_ratio == pytest.approx(1.0)

    def test_color_features(self, identity_task: ArcTask) -> None:
        f = extract_features(identity_task)
        assert f.num_input_colors > 0
        assert f.colors_added == 0
        assert f.colors_removed == 0

    def test_to_vector(self, identity_task: ArcTask) -> None:
        f = extract_features(identity_task)
        vec = f.to_vector()
        assert isinstance(vec, list)
        assert len(vec) == 18
        assert all(isinstance(v, float) for v in vec)
        assert all(0.0 <= v <= 1.0 for v in vec)

    def test_empty_task(self) -> None:
        task = ArcTask(task_id="empty", train=[], test=[])
        f = extract_features(task)
        assert f.task_id == "empty"
        assert f.num_train_pairs == 0


# --- Distance Function Tests ---


class TestDistanceFunctions:
    def test_cosine_identical(self) -> None:
        v = [1.0, 2.0, 3.0]
        assert cosine_distance(v, v) == pytest.approx(0.0, abs=1e-9)

    def test_cosine_orthogonal(self) -> None:
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert cosine_distance(a, b) == pytest.approx(1.0, abs=1e-9)

    def test_cosine_zero_vector(self) -> None:
        assert cosine_distance([0.0, 0.0], [1.0, 1.0]) == 1.0

    def test_euclidean_identical(self) -> None:
        v = [1.0, 2.0, 3.0]
        assert euclidean_distance(v, v) == pytest.approx(0.0)

    def test_euclidean_known(self) -> None:
        assert euclidean_distance([0.0, 0.0], [3.0, 4.0]) == pytest.approx(5.0)


# --- TaskIndex Tests ---


class TestTaskIndex:
    def test_add_and_size(self, identity_task: ArcTask) -> None:
        index = TaskIndex()
        f = extract_features(identity_task)
        index.add(f)
        assert index.size == 1

    def test_search_returns_results(
        self,
        identity_task: ArcTask,
        mirror_task: ArcTask,
        scale_task: ArcTask,
    ) -> None:
        index = TaskIndex()
        for task in [identity_task, mirror_task, scale_task]:
            index.add(extract_features(task))

        query = extract_features(identity_task)
        results = index.search(query, k=2, exclude={"identity"})
        assert len(results) == 2
        assert all(isinstance(r, SimilarTask) for r in results)
        assert results[0].task_id != "identity"

    def test_search_sorted_by_distance(
        self,
        identity_task: ArcTask,
        mirror_task: ArcTask,
        scale_task: ArcTask,
    ) -> None:
        index = TaskIndex()
        for task in [identity_task, mirror_task, scale_task]:
            index.add(extract_features(task))

        query = extract_features(identity_task)
        results = index.search(query, k=3, exclude={"identity"})
        for i in range(len(results) - 1):
            assert results[i].distance <= results[i + 1].distance

    def test_search_exclude_self(
        self, identity_task: ArcTask, mirror_task: ArcTask
    ) -> None:
        index = TaskIndex()
        index.add(extract_features(identity_task))
        index.add(extract_features(mirror_task))

        query = extract_features(identity_task)
        results = index.search(query, k=5, exclude={"identity"})
        assert all(r.task_id != "identity" for r in results)

    def test_search_k_limit(
        self,
        identity_task: ArcTask,
        mirror_task: ArcTask,
        scale_task: ArcTask,
    ) -> None:
        index = TaskIndex()
        for task in [identity_task, mirror_task, scale_task]:
            index.add(extract_features(task))

        results = index.search(extract_features(identity_task), k=1)
        assert len(results) == 1

    def test_search_euclidean(
        self, identity_task: ArcTask, mirror_task: ArcTask
    ) -> None:
        index = TaskIndex()
        index.add(extract_features(identity_task))
        index.add(extract_features(mirror_task))

        results = index.search(
            extract_features(identity_task), k=2, metric="euclidean"
        )
        assert len(results) >= 1

    def test_similar_task_similarity_score(self) -> None:
        st = SimilarTask(
            task_id="t",
            distance=0.3,
            features=TaskFeatures(task_id="t"),
        )
        assert st.similarity == pytest.approx(0.7)

    def test_summary(self) -> None:
        index = TaskIndex()
        assert "0 tasks" in index.summary()


# --- find_similar_tasks Tests ---


class TestFindSimilarTasks:
    def test_find_similar(
        self,
        identity_task: ArcTask,
        mirror_task: ArcTask,
        scale_task: ArcTask,
    ) -> None:
        index = TaskIndex()
        for task in [identity_task, mirror_task, scale_task]:
            index.add(extract_features(task))

        results = find_similar_tasks(identity_task, index, k=2)
        assert len(results) == 2
        # Self should be excluded, both others should appear
        result_ids = {r.task_id for r in results}
        assert "identity" not in result_ids
        assert result_ids == {"mirror", "scale"}


# --- Integration with real data ---


class TestIndexCaching:
    def test_save_and_load_roundtrip(
        self,
        identity_task: ArcTask,
        mirror_task: ArcTask,
        tmp_path: object,
    ) -> None:
        import pathlib
        cache_file = str(pathlib.Path(str(tmp_path)) / "index.json")

        index = TaskIndex()
        for task in [identity_task, mirror_task]:
            index.add(extract_features(task))

        save_index(index, cache_file)
        loaded = load_index(cache_file)

        assert loaded.size == index.size
        assert set(loaded.features.keys()) == set(index.features.keys())
        for tid in index.features:
            assert loaded.vectors[tid] == pytest.approx(index.vectors[tid])
            assert loaded.features[tid].shape_changes == index.features[tid].shape_changes
            assert loaded.features[tid].num_train_pairs == index.features[tid].num_train_pairs

    def test_loaded_index_searchable(
        self,
        identity_task: ArcTask,
        mirror_task: ArcTask,
        scale_task: ArcTask,
        tmp_path: object,
    ) -> None:
        import pathlib
        cache_file = str(pathlib.Path(str(tmp_path)) / "index.json")

        index = TaskIndex()
        for task in [identity_task, mirror_task, scale_task]:
            index.add(extract_features(task))
        save_index(index, cache_file)

        loaded = load_index(cache_file)
        results = loaded.search(extract_features(identity_task), k=2, exclude={"identity"})
        assert len(results) == 2
        assert all(r.task_id != "identity" for r in results)

    def test_build_or_load_creates_cache(
        self,
        tmp_path: object,
    ) -> None:
        from loopagi.arc.arc_loader import load_default_datasets
        import pathlib

        datasets = load_default_datasets(validate=False)
        if "training" not in datasets:
            pytest.skip("Training data not available")

        cache_file = str(pathlib.Path(str(tmp_path)) / "cache.json")
        index = build_or_load_index(datasets["training"], cache_file, max_tasks=10)
        assert index.size == 10
        assert pathlib.Path(cache_file).exists()

        # Second call should load from cache
        loaded = build_or_load_index(datasets["training"], cache_file, max_tasks=10)
        assert loaded.size == 10


class TestRealDataIntegration:
    def test_build_index_small(self) -> None:
        from loopagi.arc.arc_loader import load_default_datasets
        datasets = load_default_datasets(validate=False)
        if "training" not in datasets:
            pytest.skip("Training data not available")
        index = build_index(datasets["training"], max_tasks=20)
        assert index.size == 20

    def test_search_real_tasks(self) -> None:
        from loopagi.arc.arc_loader import load_default_datasets
        datasets = load_default_datasets(validate=False)
        if "training" not in datasets or "evaluation" not in datasets:
            pytest.skip("Data not available")
        # Index 50 training tasks
        index = build_index(datasets["training"], max_tasks=50)
        # Search with first eval task
        eval_ds = datasets["evaluation"]
        eval_task = eval_ds.get_task(eval_ds.task_ids()[0])
        results = find_similar_tasks(eval_task, index, k=3)
        assert len(results) == 3
        assert all(r.similarity >= 0.0 for r in results)
