"""Tests for the knowledge agent module."""

from loopagi.agents.knowledge_agent import KNOWLEDGE_KEYWORDS, KNOWLEDGE_ROLE


def test_knowledge_role_is_string():
    """Role prompt must be a non-empty string."""
    assert isinstance(KNOWLEDGE_ROLE, str)
    assert len(KNOWLEDGE_ROLE) > 50


def test_knowledge_keywords_is_list():
    """Keywords must be a non-empty list of strings."""
    assert isinstance(KNOWLEDGE_KEYWORDS, list)
    assert len(KNOWLEDGE_KEYWORDS) > 5
    assert all(isinstance(k, str) for k in KNOWLEDGE_KEYWORDS)


def test_knowledge_keywords_contain_core_terms():
    """Core knowledge terms must be present."""
    core = {"knowledge", "ingest", "rag"}
    assert core.issubset(set(KNOWLEDGE_KEYWORDS))


def test_knowledge_role_mentions_rag():
    """Role should mention RAG."""
    assert "rag" in KNOWLEDGE_ROLE.lower()


def test_knowledge_role_mentions_cite():
    """Role should instruct agent to cite sources."""
    assert "cite" in KNOWLEDGE_ROLE.lower()
