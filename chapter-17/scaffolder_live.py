"""
Chapter 17: Live Scaffolder - Generate AND Run

Unlike the basic scaffolder that just creates files, this one:
1. Generates a complete project structure
2. Installs dependencies
3. Runs the tests
4. Reports results

This is what a real scaffolder does: it proves the generated
project actually works before handing it to you.

Supports: Python (uv), Rust (cargo), Go (go), TypeScript (pnpm)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scaffolder import SCAFFOLDS, scaffold_project  # noqa: E402


@dataclass
class ScaffoldTestResult:
    """Result from scaffolding and testing a project."""

    language: str
    project_dir: str
    files_created: int
    init_success: bool
    init_output: str
    init_time_s: float
    test_success: bool
    test_output: str
    test_time_s: float
    run_success: bool
    run_output: str
    errors: list[str] = field(default_factory=list)


def check_tool(cmd: str) -> bool:
    """Check if a command-line tool is available."""
    return shutil.which(cmd) is not None


def run_cmd(
    cmd: str,
    cwd: str,
    timeout: int = 60,
) -> tuple[bool, str, float]:
    """Run a command and return (success, output, elapsed_seconds)."""
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        elapsed = time.time() - start
        output = result.stdout.strip()
        if result.returncode != 0:
            output = result.stderr.strip() or output
        return result.returncode == 0, output, elapsed
    except subprocess.TimeoutExpired:
        return False, f"Timeout after {timeout}s", time.time() - start
    except OSError as e:
        return False, str(e), time.time() - start


def scaffold_and_test(
    language: str,
    name: str = "test-project",
    base_dir: Path | None = None,
    cleanup: bool = True,
) -> ScaffoldTestResult:
    """
    Generate a project scaffold and verify it works.

    1. Creates the project in a temp directory
    2. Runs the init command (install deps)
    3. Runs the test command
    4. Runs the run command
    5. Reports results
    """
    scaffold = SCAFFOLDS.get(language)
    if not scaffold:
        return ScaffoldTestResult(
            language=language,
            project_dir="",
            files_created=0,
            init_success=False,
            init_output=f"Unsupported language: {language}",
            init_time_s=0,
            test_success=False,
            test_output="",
            test_time_s=0,
            run_success=False,
            run_output="",
            errors=[f"No scaffold for '{language}'"],
        )

    # Check if the required tool is available
    tool = scaffold.package_manager.split()[0]
    if not check_tool(tool):
        return ScaffoldTestResult(
            language=language,
            project_dir="",
            files_created=0,
            init_success=False,
            init_output=f"Tool not found: {tool}",
            init_time_s=0,
            test_success=False,
            test_output="",
            test_time_s=0,
            run_success=False,
            run_output="",
            errors=[f"'{tool}' not installed. Install it to test {language} scaffolds."],
        )

    # Create project
    tmp_base = base_dir or Path(tempfile.mkdtemp(prefix="scaffold_"))
    project_dir = scaffold_project(language, name, output_dir=tmp_base)
    files_created = sum(1 for _ in project_dir.rglob("*") if _.is_file())

    result = ScaffoldTestResult(
        language=language,
        project_dir=str(project_dir),
        files_created=files_created,
        init_success=False,
        init_output="",
        init_time_s=0,
        test_success=False,
        test_output="",
        test_time_s=0,
        run_success=False,
        run_output="",
    )

    # Init (install deps)
    ok, out, elapsed = run_cmd(scaffold.init_command, str(project_dir))
    result.init_success = ok
    result.init_output = out[:500]
    result.init_time_s = elapsed
    if not ok:
        result.errors.append(f"Init failed: {out[:200]}")

    # Test
    ok, out, elapsed = run_cmd(scaffold.test_command, str(project_dir))
    result.test_success = ok
    result.test_output = out[:500]
    result.test_time_s = elapsed
    if not ok:
        result.errors.append(f"Tests failed: {out[:200]}")

    # Run
    ok, out, elapsed = run_cmd(scaffold.run_command, str(project_dir), timeout=10)
    result.run_success = ok
    result.run_output = out[:500]
    if not ok and "timeout" not in out.lower():
        result.errors.append(f"Run failed: {out[:200]}")

    # Cleanup
    if cleanup and base_dir is None:
        shutil.rmtree(tmp_base, ignore_errors=True)

    return result


def demo() -> None:
    """Scaffold projects for all available languages and test them."""
    print("Chapter 17: Live Scaffolder - Generate AND Run")
    print("=" * 60)
    print()

    # Check which tools are available
    tools = {
        "python": "uv",
        "rust": "cargo",
        "go": "go",
        "typescript": "pnpm",
        "java": "gradle",
    }

    print("Tool Availability:")
    available = []
    for lang, tool in tools.items():
        found = check_tool(tool)
        status = "FOUND" if found else "NOT FOUND"
        print(f"  {lang:<12} {tool:<8} {status}")
        if found:
            available.append(lang)

    if not available:
        print("\n  No supported tools found. Install uv, cargo, go, or pnpm.")
        return

    print(f"\nTesting {len(available)} language(s): {', '.join(available)}")
    print()

    results = []
    for lang in available:
        print(f"{'─' * 60}")
        print(f"  {SCAFFOLDS[lang].name}")
        print(f"{'─' * 60}")

        print("  Scaffolding...", end=" ", flush=True)
        result = scaffold_and_test(lang, name=f"demo-{lang}")

        print(f"{result.files_created} files created")
        print(f"  Init:  {'PASS' if result.init_success else 'FAIL'} ({result.init_time_s:.1f}s)")
        print(f"  Tests: {'PASS' if result.test_success else 'FAIL'} ({result.test_time_s:.1f}s)")
        print(f"  Run:   {'PASS' if result.run_success else 'FAIL'}")

        if result.errors:
            for err in result.errors:
                print(f"  Error: {err[:80]}")

        if result.test_success and result.test_output:
            # Show test output snippet
            lines = result.test_output.splitlines()
            for line in lines[-3:]:
                if line.strip():
                    print(f"  > {line.strip()}")

        results.append(result)
        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\n  {'Language':<12} {'Files':<8} {'Init':<8} {'Tests':<8} {'Run'}")
    print(f"  {'-'*12} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

    for r in results:
        print(
            f"  {r.language:<12} {r.files_created:<8} "
            f"{'PASS' if r.init_success else 'FAIL':<8} "
            f"{'PASS' if r.test_success else 'FAIL':<8} "
            f"{'PASS' if r.run_success else 'FAIL'}"
        )

    total = len(results)
    passing = sum(1 for r in results if r.test_success)
    print(f"\n  {passing}/{total} languages scaffolded and tested successfully.")
    print()
    print("A real scaffolder does not just create files.")
    print("It proves they work.")


if __name__ == "__main__":
    demo()
