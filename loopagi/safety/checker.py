"""
Chapter 12: Trust and the Dangerous Command

Command safety checker and trust scoring. Trust is not a boolean.
It is a function that decays without reinforcement.

Usage:
    from loopagi.safety.checker import SafetyChecker, TrustScore

    checker = SafetyChecker()
    result = checker.check("rm -rf /")
    # result.blocked == True, result.reason == "Matches blocked pattern: rm -rf"

    trust = TrustScore()
    trust.reinforce()  # User approved an action
    trust.decay(seconds=300)  # 5 minutes passed
"""

from __future__ import annotations

import logging
import math
import re
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 28 patterns that are ALWAYS blocked, regardless of execution mode.
# These represent commands with potentially catastrophic consequences.
BLOCKED_PATTERNS: list[tuple[str, str]] = [
    (r"rm\s+-rf\s+/", "Recursive delete from root"),
    (r"rm\s+-rf\s+~", "Recursive delete from home"),
    (r"rm\s+-rf\s+\*", "Recursive delete wildcard"),
    (r"rm\s+-rf\s+\.", "Recursive delete current directory"),
    (r"sudo\s+rm\s+-rf", "Sudo recursive delete"),
    (r"mkfs\.", "Format filesystem"),
    (r"dd\s+if=", "Direct disk write"),
    (r":\(\)\{.*\|.*\}", "Fork bomb"),
    (r">\s*/dev/sda", "Write to raw disk"),
    (r"chmod\s+-R\s+777\s+/", "World-writable root"),
    (r"chmod\s+000\s+/", "Remove all permissions from root"),
    (r"chown\s+-R.*\s+/(?!home)", "Change ownership of system dirs"),
    (r"kill\s+-9\s+-1", "Kill all processes"),
    (r"killall\s+-9", "Kill all by name"),
    (r"shutdown", "System shutdown"),
    (r"reboot", "System reboot"),
    (r"init\s+0", "System halt"),
    (r"systemctl\s+stop\s+(?:ssh|sshd|network)", "Stop critical services"),
    (r"iptables\s+-F", "Flush firewall rules"),
    (r"curl.*\|\s*(?:sudo\s+)?(?:ba)?sh", "Pipe URL to shell"),
    (r"wget.*\|\s*(?:sudo\s+)?(?:ba)?sh", "Pipe download to shell"),
    (r"python.*-c.*exec\(", "Dynamic code execution"),
    (r"eval\s*\(", "Eval execution"),
    (r">\s*/etc/passwd", "Overwrite passwd"),
    (r">\s*/etc/shadow", "Overwrite shadow"),
    (r"DROP\s+DATABASE", "Drop database"),
    (r"DROP\s+TABLE", "Drop table"),
    (r"TRUNCATE\s+TABLE", "Truncate table"),
]


@dataclass
class SafetyResult:
    """Result of a safety check on a command."""

    command: str
    blocked: bool
    reason: str
    risk_level: str  # "safe", "caution", "dangerous", "blocked"
    matched_pattern: str = ""


class SafetyChecker:
    """
    Command safety checker with 28 always-blocked patterns.

    Why proactive boundaries outperform reactive permission:
    it is easier to prevent catastrophe than to recover from it.

    Three risk levels:
    - SAFE: No concerning patterns detected
    - CAUTION: Contains potentially risky elements
    - BLOCKED: Matches a known dangerous pattern (always denied)
    """

    # Patterns that warrant caution (not blocked, but flagged)
    CAUTION_PATTERNS: list[tuple[str, str]] = [
        (r"sudo\s+", "Elevated privileges"),
        (r"pip\s+install", "Package installation"),
        (r"npm\s+install", "Package installation"),
        (r"apt\s+install", "System package installation"),
        (r"docker\s+rm", "Docker container removal"),
        (r"git\s+push\s+.*--force", "Force push"),
        (r"git\s+reset\s+--hard", "Hard reset"),
        (r"rm\s+-r", "Recursive delete"),
        (r"mv\s+/", "Move from root"),
    ]

    def check(self, command: str) -> SafetyResult:
        """
        Check a command for safety.

        Returns a SafetyResult with risk level and blocking decision.
        """
        # Check blocked patterns first (always denied)
        for pattern, description in BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                logger.warning("BLOCKED: '%s' matched '%s'", command[:60], description)
                return SafetyResult(
                    command=command,
                    blocked=True,
                    reason=f"Matches blocked pattern: {description}",
                    risk_level="blocked",
                    matched_pattern=pattern,
                )

        # Check caution patterns (not blocked, but flagged)
        for pattern, description in self.CAUTION_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                logger.info("CAUTION: '%s' matched '%s'", command[:60], description)
                return SafetyResult(
                    command=command,
                    blocked=False,
                    reason=f"Caution: {description}",
                    risk_level="caution",
                    matched_pattern=pattern,
                )

        return SafetyResult(
            command=command,
            blocked=False,
            reason="No concerning patterns detected",
            risk_level="safe",
        )

    def is_safe(self, command: str) -> bool:
        """Quick check: is this command safe to run without approval?"""
        result = self.check(command)
        return result.risk_level == "safe"

    def is_blocked(self, command: str) -> bool:
        """Quick check: is this command always blocked?"""
        result = self.check(command)
        return result.blocked


class TrustScore:
    """
    Trust scoring with confidence decay.

    Trust is earned continuously, not granted once. The trust score
    starts at a baseline and decays over time without reinforcement
    (successful interactions). Each approved action reinforces trust.
    Each denied or failed action reduces it.

    The decay function: trust(t) = trust_0 * e^(-lambda * t)
    where lambda is the decay rate and t is time since last reinforcement.
    """

    def __init__(
        self,
        initial: float = 0.5,
        decay_rate: float = 0.001,
        min_trust: float = 0.1,
        max_trust: float = 1.0,
    ) -> None:
        self._score = initial
        self._decay_rate = decay_rate
        self._min_trust = min_trust
        self._max_trust = max_trust
        self._last_reinforcement = time.time()
        self._history: list[dict] = []

    @property
    def score(self) -> float:
        """Current trust score with decay applied."""
        elapsed = time.time() - self._last_reinforcement
        decayed = self._score * math.exp(-self._decay_rate * elapsed)
        return max(self._min_trust, decayed)

    @property
    def level(self) -> str:
        """Human-readable trust level."""
        s = self.score
        if s >= 0.8:
            return "high"
        elif s >= 0.5:
            return "medium"
        elif s >= 0.3:
            return "low"
        else:
            return "minimal"

    def reinforce(self, amount: float = 0.1) -> float:
        """
        Reinforce trust (e.g., after a successful approved action).

        Returns the new trust score.
        """
        self._score = min(self._max_trust, self.score + amount)
        self._last_reinforcement = time.time()
        self._history.append({"action": "reinforce", "amount": amount, "score": self._score})
        logger.debug("Trust reinforced: %.3f (+%.3f)", self._score, amount)
        return self._score

    def penalize(self, amount: float = 0.2) -> float:
        """
        Reduce trust (e.g., after a denied or failed action).

        Returns the new trust score.
        """
        self._score = max(self._min_trust, self.score - amount)
        self._last_reinforcement = time.time()
        self._history.append({"action": "penalize", "amount": amount, "score": self._score})
        logger.debug("Trust penalized: %.3f (-%.3f)", self._score, amount)
        return self._score

    def reset(self, value: float = 0.5) -> None:
        """Reset trust to a specific value."""
        self._score = max(self._min_trust, min(self._max_trust, value))
        self._last_reinforcement = time.time()

    def __repr__(self) -> str:
        return f"TrustScore(score={self.score:.3f}, level='{self.level}')"
