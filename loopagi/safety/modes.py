"""
Chapter 11: God in the Loop

Execution modes: Turbo (autonomous) and Careful (approval required).
The god in the loop is not a supervisor. It is a participant in the
emergence of something greater than either mind alone.

Usage:
    from loopagi.safety.modes import ExecutionMode, ModeManager

    manager = ModeManager()
    manager.set_mode(ExecutionMode.CAREFUL)

    if manager.requires_approval("rm -rf /tmp/test"):
        approved = manager.request_approval("Delete /tmp/test directory?")
        if approved:
            # proceed
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Callable

logger = logging.getLogger(__name__)


class ExecutionMode(str, Enum):
    """
    The two modes of agent execution.

    TURBO: Autonomous execution. The agent acts without asking.
           Safe commands run automatically. Dangerous commands are
           always blocked regardless of mode.

    CAREFUL: Every command requires human approval. The agent
             proposes actions and waits for confirmation. This
             is the "god in the loop" at its most literal.
    """

    TURBO = "turbo"
    CAREFUL = "careful"


class ModeManager:
    """
    Manages execution mode and approval workflows.

    In Turbo mode, safe operations proceed automatically.
    In Careful mode, every action requires explicit approval.
    Dangerous operations are ALWAYS blocked in both modes.

    The evolution of control: as the agent grows more capable,
    the nature of approval transforms. The human's role shifts
    from safeguard to collaborator.
    """

    def __init__(
        self,
        mode: ExecutionMode = ExecutionMode.TURBO,
        approval_callback: Callable[[str], bool] | None = None,
    ) -> None:
        self._mode = mode
        self._approval_callback = approval_callback or self._default_approval
        self._approval_history: list[dict] = []
        logger.info("ModeManager initialized in %s mode", mode.value.upper())

    @property
    def mode(self) -> ExecutionMode:
        return self._mode

    def set_mode(self, mode: ExecutionMode) -> None:
        """Switch execution mode."""
        old = self._mode
        self._mode = mode
        logger.info("Mode changed: %s -> %s", old.value.upper(), mode.value.upper())

    def toggle(self) -> ExecutionMode:
        """Toggle between Turbo and Careful modes."""
        new_mode = (
            ExecutionMode.CAREFUL if self._mode == ExecutionMode.TURBO
            else ExecutionMode.TURBO
        )
        self.set_mode(new_mode)
        return new_mode

    def requires_approval(self, action: str) -> bool:
        """
        Check if an action requires human approval.

        In CAREFUL mode: everything requires approval.
        In TURBO mode: only potentially destructive actions require approval.
        """
        if self._mode == ExecutionMode.CAREFUL:
            return True

        # In TURBO mode, check if the action is potentially destructive
        from loopagi.safety.checker import SafetyChecker

        checker = SafetyChecker()
        return not checker.is_safe(action)

    def request_approval(self, description: str) -> bool:
        """
        Request human approval for an action.

        Uses the configured approval callback (defaults to terminal input).
        """
        logger.info("Requesting approval: %s", description)
        approved = self._approval_callback(description)
        self._approval_history.append({
            "description": description,
            "approved": approved,
            "mode": self._mode.value,
        })
        if approved:
            logger.info("Action APPROVED: %s", description[:60])
        else:
            logger.info("Action DENIED: %s", description[:60])
        return approved

    @staticmethod
    def _default_approval(description: str) -> bool:
        """Default approval callback: prompt in terminal."""
        try:
            response = input(f"\n[APPROVAL REQUIRED] {description}\nApprove? (y/n): ")
            return response.strip().lower() in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False

    def __repr__(self) -> str:
        return f"ModeManager(mode={self._mode.value})"
