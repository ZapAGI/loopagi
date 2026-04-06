"""
Documenter agent: generate documentation, READMEs, and docstrings.

Produces clear, structured documentation for code, APIs, and projects.
Follows existing style conventions when updating existing docs.

Usage:
    from loopagi.agents.documenter import DOCUMENTER_ROLE, DOCUMENTER_KEYWORDS

    agent = Agent(name="documenter", role=DOCUMENTER_ROLE, model="qwen3:14b")
"""

from __future__ import annotations

DOCUMENTER_ROLE = (
    "You are a documentation specialist. Generate clear, well-structured "
    "documentation. Capabilities:\n"
    "- READMEs with badges, install instructions, and usage examples\n"
    "- Python docstrings (Google style) with Args, Returns, Raises\n"
    "- API documentation with endpoints, parameters, and response schemas\n"
    "- Changelogs following Keep a Changelog format\n"
    "- Inline comments that explain 'why', not 'what'\n"
    "Match the existing documentation style when updating. "
    "Use fenced code blocks for all code examples."
)

DOCUMENTER_KEYWORDS = [
    "document", "readme", "docstring", "changelog", "comment",
    "explain code", "api doc", "type hint", "annotate", "describe",
    "documentation", "docs", "jsdoc", "sphinx", "mkdocs",
]
