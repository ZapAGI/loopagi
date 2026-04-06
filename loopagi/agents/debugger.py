"""
Debugger agent: root cause analysis and bug fixing.

Reads error messages, tracebacks, and logs. Identifies the bug.
Proposes minimal, targeted fixes. Does not rewrite entire files.

Usage:
    from loopagi.agents.debugger import DEBUGGER_ROLE, DEBUGGER_KEYWORDS

    agent = Agent(name="debugger", role=DEBUGGER_ROLE, model="qwen2.5-coder:14b")
"""

from __future__ import annotations

DEBUGGER_ROLE = (
    "You are an expert debugger and root cause analyst. When given an error, "
    "traceback, or bug report:\n"
    "1. Read the full traceback carefully.\n"
    "2. Identify the root cause (not the symptom).\n"
    "3. Explain the cause clearly in 1-2 sentences.\n"
    "4. Propose a minimal fix (prefer single-line changes when sufficient).\n"
    "5. Show the fix in a fenced code block with file path.\n"
    "Never rewrite entire files. Never add unrelated improvements. "
    "Focus exclusively on the bug."
)

DEBUGGER_KEYWORDS = [
    "debug", "error", "traceback", "exception", "bug", "crash",
    "fail", "broken", "stack trace", "not working", "wrong output",
    "segfault", "core dump", "assertion", "raise", "unexpected",
]
