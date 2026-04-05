"""Tests for loopagi.pipeline module."""

from __future__ import annotations

from loopagi.core.pipeline import PipelineResult, PipelineStage, StageResult


class TestPipelineStage:
    """Tests for PipelineStage enum."""

    def test_values(self) -> None:
        assert PipelineStage.PLAN.value == "plan"
        assert PipelineStage.CODE.value == "code"
        assert PipelineStage.TEST.value == "test"
        assert PipelineStage.REVIEW.value == "review"

    def test_all_stages(self) -> None:
        stages = list(PipelineStage)
        assert len(stages) == 4


class TestStageResult:
    """Tests for StageResult dataclass."""

    def test_defaults(self) -> None:
        r = StageResult(stage=PipelineStage.CODE, agent_name="coder", output="code here")
        assert r.passed is True
        assert r.feedback == ""

    def test_failed_stage(self) -> None:
        r = StageResult(
            stage=PipelineStage.REVIEW,
            agent_name="reviewer",
            output="REVISION NEEDED",
            passed=False,
            feedback="Missing type hints",
        )
        assert not r.passed
        assert "type hints" in r.feedback


class TestPipelineResult:
    """Tests for PipelineResult dataclass."""

    def test_empty_result(self) -> None:
        r = PipelineResult(task="test task")
        assert r.task == "test task"
        assert r.stages == []
        assert r.final_code == ""
        assert r.iterations == 0
        assert not r.success

    def test_summary(self) -> None:
        r = PipelineResult(task="test", iterations=2, success=True)
        r.stages = [
            StageResult(stage=PipelineStage.PLAN, agent_name="planner", output="plan"),
            StageResult(stage=PipelineStage.CODE, agent_name="coder", output="code"),
            StageResult(stage=PipelineStage.TEST, agent_name="tester", output="tests"),
            StageResult(
                stage=PipelineStage.REVIEW, agent_name="reviewer",
                output="APPROVED", passed=True,
            ),
        ]
        summary = r.summary
        assert "PASS" in summary
        assert "iterations=2" in summary
        assert "success=True" in summary

    def test_failed_summary(self) -> None:
        r = PipelineResult(task="test", iterations=3, success=False)
        r.stages = [
            StageResult(
                stage=PipelineStage.REVIEW, agent_name="reviewer",
                output="bad", passed=False,
            ),
        ]
        summary = r.summary
        assert "FAIL" in summary
        assert "success=False" in summary
