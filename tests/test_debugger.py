"""Tests for the debugger agent module."""

from loopagi.agents.debugger import DEBUGGER_KEYWORDS, DEBUGGER_ROLE


def test_debugger_role_is_string():
    """Role prompt must be a non-empty string."""
    assert isinstance(DEBUGGER_ROLE, str)
    assert len(DEBUGGER_ROLE) > 50


def test_debugger_keywords_is_list():
    """Keywords must be a non-empty list of strings."""
    assert isinstance(DEBUGGER_KEYWORDS, list)
    assert len(DEBUGGER_KEYWORDS) > 5
    assert all(isinstance(k, str) for k in DEBUGGER_KEYWORDS)


def test_debugger_keywords_contain_core_terms():
    """Core debugging terms must be present."""
    core = {"debug", "error", "traceback", "bug", "crash"}
    assert core.issubset(set(DEBUGGER_KEYWORDS))


def test_debugger_role_mentions_root_cause():
    """Role should instruct agent to find root cause."""
    assert "root cause" in DEBUGGER_ROLE.lower()


def test_debugger_role_mentions_minimal_fix():
    """Role should instruct agent to propose minimal fixes."""
    assert "minimal" in DEBUGGER_ROLE.lower()
