"""Test that Python files respect the tiered module size policy.

Tiered limits (from .looprules):
- Standard tier (300 lines): application logic, agents, tools, CLI, stateful code
- Extended tier (500 lines): DSL primitives, data loaders, pure utility modules
- Hard ceiling: NO file may exceed 500 lines

See DSL_FILE_SIZE_RESEARCH.md for rationale and references.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Project root is three levels up from this test file
PROJECT_ROOT = Path(__file__).parent.parent

# Files explicitly assigned to the Extended tier (500-line max).
# Each must meet ALL criteria: pure functions, single semantic domain,
# shallow deps, high function count, full test coverage.
EXTENDED_TIER_FILES: set[str] = {
    "loopagi/arc/grid_ops.py",
    "loopagi/arc/grid_objects.py",
    "loopagi/arc/arc_loader.py",
    "loopagi/arc/arc_runner.py",
    "loopagi/arc/arc_visualizer.py",
    "loopagi/arc/llm_bridge.py",
    "loopagi/arc/perceiver.py",
    "loopagi/arc/verifier.py",
    "loopagi/arc/task_similarity.py",
    "loopagi/arc/synthesizer.py",
    "loopagi/arc/arc_analytics.py",
    "loopagi/arc/evolver.py",
    "loopagi/arc/mutator.py",
    "loopagi/arc/grid_describer.py",
    "loopagi/arc/solve_improved.py",
    "loopagi/arc/transducer.py",
    "loopagi/arc/llm_evolver.py",
    "loopagi/arc/llm_solver.py",
    "loopagi/arc/nl_evolver.py",
    "loopagi/arc/ttt.py",
    "loopagi/arc/grid_traversal.py",
    "loopagi/arc/augmentation_voter.py",
    "loopagi/arc/ensemble.py",
    "loopagi/arc/diff_refiner.py",
    "loopagi/arc/pass_at_k.py",
    "loopagi/arc/cell_fixer.py",
}

# Files with known violations and a tracked remediation plan.
# Format: {relative_path: (current_lines, issue_tracker_ref)}
# These MUST be listed in IMPROVEMENTS.md with a fix plan.
KNOWN_VIOLATIONS: dict[str, str] = {
    "loopagi/cli.py": "IMPROVEMENTS.md 1.5: split into 4 files",
    "loopagi/knowledge/rag.py": "IMPROVEMENTS.md: evaluate for Extended or split",
    "loopagi/knowledge/context.py": "319 lines, borderline: extract config to constants module",
}

# Tier limits
STANDARD_MAX = 300
EXTENDED_MAX = 500
HARD_CEILING = 500


def _count_code_lines(filepath: Path) -> int:
    """Count non-blank, non-comment lines in a Python file."""
    count = 0
    with open(filepath, encoding="utf-8") as f:
        in_docstring = False
        for line in f:
            stripped = line.strip()
            # Track triple-quote docstrings
            if '"""' in stripped or "'''" in stripped:
                quote = '"""' if '"""' in stripped else "'''"
                occurrences = stripped.count(quote)
                if occurrences == 1:
                    in_docstring = not in_docstring
                    continue
                # Single-line docstring (open + close on same line)
                if occurrences >= 2:
                    continue
            if in_docstring:
                continue
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue
            count += 1
    return count


def _count_total_lines(filepath: Path) -> int:
    """Count total lines in a file (used for the hard ceiling)."""
    with open(filepath, encoding="utf-8") as f:
        return sum(1 for _ in f)


def _get_python_files() -> list[Path]:
    """Get all Python files in loopagi/ package."""
    loopagi_dir = PROJECT_ROOT / "loopagi"
    return sorted(loopagi_dir.rglob("*.py"))


def _relative(path: Path) -> str:
    """Get path relative to project root."""
    return str(path.relative_to(PROJECT_ROOT))


class TestFileSizeHardCeiling:
    """No file may exceed 500 total lines, ever."""

    def test_no_file_exceeds_hard_ceiling(self) -> None:
        violations: list[str] = []
        for py_file in _get_python_files():
            rel = _relative(py_file)
            if rel in KNOWN_VIOLATIONS:
                continue
            total = _count_total_lines(py_file)
            if total > HARD_CEILING:
                violations.append(f"{rel}: {total} lines (max {HARD_CEILING})")
        if violations:
            msg = "Files exceeding hard ceiling:\n" + "\n".join(violations)
            pytest.fail(msg)


class TestFileSizeStandardTier:
    """Standard-tier files must stay under 300 total lines."""

    def test_standard_tier_files(self) -> None:
        violations: list[str] = []
        for py_file in _get_python_files():
            rel = _relative(py_file)
            if rel in EXTENDED_TIER_FILES:
                continue
            if rel in KNOWN_VIOLATIONS:
                continue
            total = _count_total_lines(py_file)
            if total > STANDARD_MAX:
                violations.append(
                    f"{rel}: {total} lines (standard max {STANDARD_MAX}). "
                    f"Add to EXTENDED_TIER_FILES if it qualifies, or refactor."
                )
        if violations:
            msg = "Standard-tier files exceeding limit:\n" + "\n".join(violations)
            pytest.fail(msg)


class TestFileSizeExtendedTier:
    """Extended-tier files must stay under 500 total lines."""

    def test_extended_tier_files(self) -> None:
        violations: list[str] = []
        for py_file in _get_python_files():
            rel = _relative(py_file)
            if rel not in EXTENDED_TIER_FILES:
                continue
            total = _count_total_lines(py_file)
            if total > EXTENDED_MAX:
                violations.append(f"{rel}: {total} lines (extended max {EXTENDED_MAX})")
        if violations:
            msg = "Extended-tier files exceeding limit:\n" + "\n".join(violations)
            pytest.fail(msg)


class TestKnownViolations:
    """Track known violations: they must exist and have a remediation note."""

    def test_known_violations_still_exist(self) -> None:
        """Verify known violations are real. Remove entries once fixed."""
        for rel, reason in KNOWN_VIOLATIONS.items():
            filepath = PROJECT_ROOT / rel
            if not filepath.exists():
                pytest.fail(
                    f"Known violation {rel} no longer exists. "
                    f"Remove from KNOWN_VIOLATIONS."
                )
            total = _count_total_lines(filepath)
            if total <= STANDARD_MAX:
                pytest.fail(
                    f"Known violation {rel} is now {total} lines "
                    f"(under {STANDARD_MAX}). Remove from KNOWN_VIOLATIONS."
                )

    def test_known_violations_have_reason(self) -> None:
        """Every known violation must document its remediation plan."""
        for rel, reason in KNOWN_VIOLATIONS.items():
            assert reason, f"Known violation {rel} has no remediation reason"


class TestFileSizeSummary:
    """Informational: print a summary of all file sizes (always passes)."""

    def test_print_summary(self, capsys: pytest.CaptureFixture[str]) -> None:
        lines: list[str] = ["\n=== Module Size Report ==="]
        for py_file in _get_python_files():
            rel = _relative(py_file)
            if rel.endswith("__init__.py") or rel.endswith("__main__.py"):
                continue
            total = _count_total_lines(py_file)
            tier = "EXT" if rel in EXTENDED_TIER_FILES else "STD"
            limit = EXTENDED_MAX if tier == "EXT" else STANDARD_MAX
            status = "OK" if total <= limit else "OVER"
            if rel in KNOWN_VIOLATIONS:
                status = "KNOWN"
            lines.append(f"  [{tier}] {status:5s} {total:4d}/{limit} {rel}")
        lines.append("=" * 40)
        print("\n".join(lines))
