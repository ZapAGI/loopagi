"""Tests for the documenter agent module."""

from loopagi.agents.documenter import DOCUMENTER_KEYWORDS, DOCUMENTER_ROLE


def test_documenter_role_is_string():
    """Role prompt must be a non-empty string."""
    assert isinstance(DOCUMENTER_ROLE, str)
    assert len(DOCUMENTER_ROLE) > 50


def test_documenter_keywords_is_list():
    """Keywords must be a non-empty list of strings."""
    assert isinstance(DOCUMENTER_KEYWORDS, list)
    assert len(DOCUMENTER_KEYWORDS) > 5
    assert all(isinstance(k, str) for k in DOCUMENTER_KEYWORDS)


def test_documenter_keywords_contain_core_terms():
    """Core documentation terms must be present."""
    core = {"readme", "docstring", "changelog", "document"}
    assert core.issubset(set(DOCUMENTER_KEYWORDS))


def test_documenter_role_mentions_readme():
    """Role should mention README generation."""
    assert "readme" in DOCUMENTER_ROLE.lower()


def test_documenter_role_mentions_docstrings():
    """Role should mention docstring generation."""
    assert "docstring" in DOCUMENTER_ROLE.lower()
