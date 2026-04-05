"""Tests for loopagi.modes module."""

from __future__ import annotations

from loopagi.safety.modes import ExecutionMode, ModeManager


class TestExecutionMode:
    """Tests for ExecutionMode enum."""

    def test_values(self) -> None:
        assert ExecutionMode.TURBO.value == "turbo"
        assert ExecutionMode.CAREFUL.value == "careful"


class TestModeManager:
    """Tests for the ModeManager."""

    def test_default_mode(self) -> None:
        manager = ModeManager()
        assert manager.mode == ExecutionMode.TURBO

    def test_set_mode(self) -> None:
        manager = ModeManager()
        manager.set_mode(ExecutionMode.CAREFUL)
        assert manager.mode == ExecutionMode.CAREFUL

    def test_toggle(self) -> None:
        manager = ModeManager()
        assert manager.mode == ExecutionMode.TURBO
        new_mode = manager.toggle()
        assert new_mode == ExecutionMode.CAREFUL
        assert manager.mode == ExecutionMode.CAREFUL
        new_mode = manager.toggle()
        assert new_mode == ExecutionMode.TURBO

    def test_careful_mode_requires_approval_for_everything(self) -> None:
        manager = ModeManager(mode=ExecutionMode.CAREFUL)
        assert manager.requires_approval("ls -la")
        assert manager.requires_approval("echo hello")

    def test_turbo_mode_safe_commands_no_approval(self) -> None:
        manager = ModeManager(mode=ExecutionMode.TURBO)
        assert not manager.requires_approval("ls -la")
        assert not manager.requires_approval("echo hello")

    def test_turbo_mode_unsafe_commands_need_approval(self) -> None:
        manager = ModeManager(mode=ExecutionMode.TURBO)
        assert manager.requires_approval("sudo apt update")

    def test_approval_callback(self) -> None:
        approvals = []
        manager = ModeManager(
            mode=ExecutionMode.CAREFUL,
            approval_callback=lambda desc: (approvals.append(desc), True)[1],
        )
        result = manager.request_approval("Delete test file")
        assert result is True
        assert len(approvals) == 1

    def test_denial_callback(self) -> None:
        manager = ModeManager(
            approval_callback=lambda desc: False,
        )
        result = manager.request_approval("Dangerous action")
        assert result is False
