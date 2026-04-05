"""Tests for loopagi.arc.few_shot module."""

from __future__ import annotations

import pytest

from loopagi.arc.arc_loader import ArcTask, GridPair, TestInput
from loopagi.arc.few_shot import (
    FewShotContext,
    FewShotExample,
    build_few_shot_context,
)
from loopagi.arc.task_similarity import TaskIndex, extract_features


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
            GridPair(input=[[1]], output=[[1, 1], [1, 1]]),
            GridPair(input=[[2]], output=[[2, 2], [2, 2]]),
        ],
        test=[TestInput(input=[[3]])],
    )


@pytest.fixture
def small_index(
    identity_task: ArcTask,
    mirror_task: ArcTask,
    scale_task: ArcTask,
) -> TaskIndex:
    index = TaskIndex()
    for task in [identity_task, mirror_task, scale_task]:
        index.add(extract_features(task))
    return index


# --- FewShotContext Tests ---


class TestFewShotContext:
    def test_empty_context(self) -> None:
        ctx = FewShotContext()
        assert ctx.num_examples == 0
        assert ctx.format_for_hypothesis() == ""
        assert ctx.format_for_synthesis() == ""

    def test_context_with_examples(self) -> None:
        ctx = FewShotContext(examples=[
            FewShotExample(
                task_id="t1",
                similarity=0.85,
                perception_summary="summary",
                consistent_patterns=["output_same_shape_as_input"],
                sample_pair="  In: 12\n  Out: 21",
            ),
        ])
        assert ctx.num_examples == 1

        hyp_text = ctx.format_for_hypothesis()
        assert "Similar tasks" in hyp_text
        assert "85%" in hyp_text
        assert "output_same_shape_as_input" in hyp_text

        synth_text = ctx.format_for_synthesis()
        assert "Hints" in synth_text
        assert "85%" in synth_text


# --- build_few_shot_context Tests ---


class TestBuildFewShotContext:
    def test_build_without_dataset(
        self,
        identity_task: ArcTask,
        small_index: TaskIndex,
    ) -> None:
        ctx = build_few_shot_context(
            identity_task, small_index, dataset=None, k=2,
        )
        assert ctx.num_examples == 2
        task_ids = {ex.task_id for ex in ctx.examples}
        assert "identity" not in task_ids

    def test_build_has_feature_patterns(
        self,
        scale_task: ArcTask,
        small_index: TaskIndex,
    ) -> None:
        ctx = build_few_shot_context(
            scale_task, small_index, dataset=None, k=2,
        )
        for ex in ctx.examples:
            assert len(ex.consistent_patterns) > 0

    def test_hypothesis_format_nonempty(
        self,
        identity_task: ArcTask,
        small_index: TaskIndex,
    ) -> None:
        ctx = build_few_shot_context(
            identity_task, small_index, dataset=None, k=2,
        )
        text = ctx.format_for_hypothesis()
        assert "Similar tasks" in text

    def test_synthesis_format_nonempty(
        self,
        identity_task: ArcTask,
        small_index: TaskIndex,
    ) -> None:
        ctx = build_few_shot_context(
            identity_task, small_index, dataset=None, k=2,
        )
        text = ctx.format_for_synthesis()
        assert "Hints" in text


# --- Integration with real data ---


class TestFewShotRealData:
    def test_build_with_real_dataset(self) -> None:
        from loopagi.arc.arc_loader import load_default_datasets
        from loopagi.arc.task_similarity import build_index

        datasets = load_default_datasets(validate=False)
        if "training" not in datasets:
            pytest.skip("Training data not available")

        ds = datasets["training"]
        index = build_index(ds, max_tasks=50)
        task = ds.get_task(ds.task_ids()[0])

        ctx = build_few_shot_context(task, index, dataset=ds, k=3)
        assert ctx.num_examples == 3

        # With dataset, we should have perception-based patterns
        for ex in ctx.examples:
            assert ex.task_id != task.task_id
            assert ex.similarity >= 0.0
