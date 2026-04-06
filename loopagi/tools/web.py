"""
Web search tool for LoopAGI agents.

Provides: web search via DuckDuckGo (no API key required),
URL content fetching.
"""

from __future__ import annotations

import logging
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Any

from loopagi.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class _TextExtractor(HTMLParser):
    """Simple HTML to text converter."""

    def __init__(self) -> None:
        super().__init__()
        self._text: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            text = data.strip()
            if text:
                self._text.append(text)

    def get_text(self) -> str:
        return " ".join(self._text)


class WebSearchTool(BaseTool):
    """
    Web search and URL fetching. No API key required.

    Uses DuckDuckGo Lite for search (no tracking, no API key).
    Can also fetch and extract text from any URL.
    """

    name = "web"
    description = "Web search and URL content fetching"

    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout

    def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "search")

        match action:
            case "search":
                return self._search(
                    query=kwargs.get("query", ""),
                    max_results=kwargs.get("max_results", 5),
                )
            case "fetch":
                return self._fetch(
                    url=kwargs.get("url", ""),
                    max_chars=kwargs.get("max_chars", 5000),
                )
            case _:
                return ToolResult(tool=self.name, success=False, error=f"Unknown action: {action}")

    def _search(self, query: str, max_results: int) -> ToolResult:
        """Search the web using DuckDuckGo Lite."""
        if not query:
            return ToolResult(tool=self.name, success=False, error="Search query required")

        try:
            encoded = urllib.parse.urlencode({"q": query})
            url = f"https://lite.duckduckgo.com/lite/?{encoded}"

            req = urllib.request.Request(
                url,
                headers={"User-Agent": "LoopAGI/1.0 (Python)"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            # Parse DuckDuckGo Lite results
            results = self._parse_ddg_results(html, max_results)

            if not results:
                return ToolResult(
                    tool=self.name,
                    success=True,
                    output="No results found.",
                    metadata={"query": query, "results": 0},
                )

            output = f"Search results for: {query}\n\n"
            for i, (title, link, snippet) in enumerate(results, 1):
                output += f"{i}. {title}\n   {link}\n   {snippet}\n\n"

            return ToolResult(
                tool=self.name,
                success=True,
                output=output.strip(),
                metadata={"query": query, "results": len(results)},
            )
        except urllib.error.URLError as e:
            return ToolResult(tool=self.name, success=False, error=f"Network error: {e}")
        except Exception as e:
            return ToolResult(tool=self.name, success=False, error=f"Search failed: {e}")

    def _fetch(self, url: str, max_chars: int) -> ToolResult:
        """Fetch and extract text from a URL."""
        if not url:
            return ToolResult(tool=self.name, success=False, error="URL required")

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "LoopAGI/1.0 (Python)"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            extractor = _TextExtractor()
            extractor.feed(html)
            text = extractor.get_text()

            if len(text) > max_chars:
                text = text[:max_chars] + f"\n\n... (truncated at {max_chars} chars)"

            return ToolResult(
                tool=self.name,
                success=True,
                output=text or "(no text content)",
                metadata={"url": url, "chars": len(text)},
            )
        except urllib.error.URLError as e:
            return ToolResult(tool=self.name, success=False, error=f"Fetch error: {e}")
        except Exception as e:
            return ToolResult(tool=self.name, success=False, error=f"Fetch failed: {e}")

    @staticmethod
    def _parse_ddg_results(html: str, max_results: int) -> list[tuple[str, str, str]]:
        """Parse DuckDuckGo Lite HTML for search results."""
        results = []

        # DuckDuckGo Lite uses simple HTML with links in specific patterns
        # Look for result links and snippets
        link_pattern = re.compile(
            r'<a[^>]+rel="nofollow"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>',
            re.IGNORECASE,
        )
        snippet_pattern = re.compile(
            r'<td[^>]*class="result-snippet"[^>]*>(.*?)</td>',
            re.IGNORECASE | re.DOTALL,
        )

        links = link_pattern.findall(html)
        snippets = snippet_pattern.findall(html)

        for i, (link, title) in enumerate(links):
            if i >= max_results:
                break
            # Skip DuckDuckGo internal links
            if "duckduckgo.com" in link:
                continue
            title = title.strip()
            snippet = ""
            if i < len(snippets):
                # Clean HTML tags from snippet
                snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip()
            if title and link:
                results.append((title, link, snippet))

        return results[:max_results]
