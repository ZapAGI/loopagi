"""Tests for the memory agent module."""

from loopagi.agents.memory_agent import MEMORY_KEYWORDS, MEMORY_ROLE


def test_memory_role_is_string():
    """Role prompt must be a non-empty string."""
    assert isinstance(MEMORY_ROLE, str)
    assert len(MEMORY_ROLE) > 50


def test_memory_keywords_is_list():
    """Keywords must be a non-empty list of strings."""
    assert isinstance(MEMORY_KEYWORDS, list)
    assert len(MEMORY_KEYWORDS) > 5
    assert all(isinstance(k, str) for k in MEMORY_KEYWORDS)


def test_memory_keywords_contain_core_terms():
    """Core memory terms must be present."""
    core = {"remember", "recall", "memory", "forget"}
    assert core.issubset(set(MEMORY_KEYWORDS))


def test_memory_role_mentions_long_term():
    """Role should mention long-term memory."""
    assert "long-term" in MEMORY_ROLE.lower()


def test_memory_role_mentions_relevance():
    """Role should instruct agent to rank by relevance."""
    assert "relevance" in MEMORY_ROLE.lower() or "relevant" in MEMORY_ROLE.lower()
