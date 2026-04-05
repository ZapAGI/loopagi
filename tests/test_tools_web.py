"""Tests for loopagi.tools_web module (WebSearchTool)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from loopagi.tools.web import WebSearchTool, _TextExtractor


class TestTextExtractor:
    """Tests for the HTML text extractor."""

    def test_basic_html(self) -> None:
        extractor = _TextExtractor()
        extractor.feed("<html><body><p>Hello world</p></body></html>")
        assert "Hello world" in extractor.get_text()

    def test_strips_script_tags(self) -> None:
        extractor = _TextExtractor()
        extractor.feed(
            "<html><body><script>var x = 1;</script>"
            "<p>Visible text</p></body></html>"
        )
        text = extractor.get_text()
        assert "Visible text" in text
        assert "var x" not in text

    def test_strips_style_tags(self) -> None:
        extractor = _TextExtractor()
        extractor.feed(
            "<html><body><style>.red{color:red}</style>"
            "<p>Content</p></body></html>"
        )
        text = extractor.get_text()
        assert "Content" in text
        assert "color" not in text

    def test_strips_noscript_tags(self) -> None:
        extractor = _TextExtractor()
        extractor.feed(
            "<html><body><noscript>Enable JS</noscript>"
            "<p>Main</p></body></html>"
        )
        text = extractor.get_text()
        assert "Main" in text
        assert "Enable JS" not in text

    def test_empty_html(self) -> None:
        extractor = _TextExtractor()
        extractor.feed("")
        assert extractor.get_text() == ""

    def test_nested_tags(self) -> None:
        extractor = _TextExtractor()
        extractor.feed(
            "<div><span>Nested</span> <em>content</em></div>"
        )
        text = extractor.get_text()
        assert "Nested" in text
        assert "content" in text


class TestWebSearchToolMeta:
    """Tests for WebSearchTool metadata and basic validation."""

    def test_name(self) -> None:
        tool = WebSearchTool()
        assert tool.name == "web"

    def test_description(self) -> None:
        tool = WebSearchTool()
        assert len(tool.description) > 0

    def test_unknown_action(self) -> None:
        tool = WebSearchTool()
        result = tool.execute(action="crawl")
        assert not result.success
        assert "Unknown action" in result.error

    def test_search_empty_query(self) -> None:
        tool = WebSearchTool()
        result = tool.execute(action="search", query="")
        assert not result.success
        assert "query required" in result.error.lower()

    def test_fetch_empty_url(self) -> None:
        tool = WebSearchTool()
        result = tool.execute(action="fetch", url="")
        assert not result.success
        assert "URL required" in result.error


class TestWebSearchToolSearch:
    """Tests for search functionality with mocked network."""

    @patch("loopagi.tools.web.urllib.request.urlopen")
    def test_search_returns_results(self, mock_urlopen: MagicMock) -> None:
        html = (
            '<html><body>'
            '<a rel="nofollow" href="https://example.com">Example</a>'
            '<td class="result-snippet">A test snippet</td>'
            '</body></html>'
        )
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode("utf-8")
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        tool = WebSearchTool()
        result = tool.execute(action="search", query="test query")
        assert result.success
        assert "Example" in result.output

    @patch("loopagi.tools.web.urllib.request.urlopen")
    def test_search_no_results(self, mock_urlopen: MagicMock) -> None:
        html = "<html><body>No results</body></html>"
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode("utf-8")
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        tool = WebSearchTool()
        result = tool.execute(action="search", query="xyznonexistent")
        assert result.success
        assert "No results" in result.output

    @patch("loopagi.tools.web.urllib.request.urlopen")
    def test_search_network_error(self, mock_urlopen: MagicMock) -> None:
        import urllib.error

        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        tool = WebSearchTool()
        result = tool.execute(action="search", query="test")
        assert not result.success
        assert "Network error" in result.error


class TestWebSearchToolFetch:
    """Tests for URL fetch functionality with mocked network."""

    @patch("loopagi.tools.web.urllib.request.urlopen")
    def test_fetch_extracts_text(self, mock_urlopen: MagicMock) -> None:
        html = (
            "<html><head><title>Test Page</title></head>"
            "<body><h1>Hello</h1><p>World content here</p></body></html>"
        )
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode("utf-8")
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        tool = WebSearchTool()
        result = tool.execute(action="fetch", url="https://example.com")
        assert result.success
        assert "Hello" in result.output
        assert "World content" in result.output

    @patch("loopagi.tools.web.urllib.request.urlopen")
    def test_fetch_truncates_long_content(
        self, mock_urlopen: MagicMock,
    ) -> None:
        html = "<html><body>" + "A" * 10000 + "</body></html>"
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode("utf-8")
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        tool = WebSearchTool()
        result = tool.execute(
            action="fetch", url="https://example.com", max_chars=100,
        )
        assert result.success
        assert "truncated" in result.output

    @patch("loopagi.tools.web.urllib.request.urlopen")
    def test_fetch_adds_https_prefix(
        self, mock_urlopen: MagicMock,
    ) -> None:
        html = "<html><body><p>Auto prefix</p></body></html>"
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode("utf-8")
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        tool = WebSearchTool()
        result = tool.execute(action="fetch", url="example.com")
        assert result.success
        assert result.metadata.get("url") == "https://example.com"

    @patch("loopagi.tools.web.urllib.request.urlopen")
    def test_fetch_network_error(self, mock_urlopen: MagicMock) -> None:
        import urllib.error

        mock_urlopen.side_effect = urllib.error.URLError("Timeout")

        tool = WebSearchTool()
        result = tool.execute(
            action="fetch", url="https://unreachable.test",
        )
        assert not result.success
        assert "Fetch error" in result.error


class TestParseDdgResults:
    """Tests for DuckDuckGo HTML result parsing."""

    def test_parses_result_links(self) -> None:
        html = (
            '<a rel="nofollow" href="https://site1.com">Site One</a>'
            '<td class="result-snippet">First snippet</td>'
            '<a rel="nofollow" href="https://site2.com">Site Two</a>'
            '<td class="result-snippet">Second snippet</td>'
        )
        results = WebSearchTool._parse_ddg_results(html, max_results=5)
        assert len(results) == 2
        assert results[0][0] == "Site One"
        assert results[0][1] == "https://site1.com"
        assert results[0][2] == "First snippet"

    def test_respects_max_results(self) -> None:
        html = ""
        for i in range(10):
            html += (
                f'<a rel="nofollow" href="https://site{i}.com">'
                f"Site {i}</a>"
            )
        results = WebSearchTool._parse_ddg_results(html, max_results=3)
        assert len(results) <= 3

    def test_skips_duckduckgo_links(self) -> None:
        html = (
            '<a rel="nofollow" '
            'href="https://duckduckgo.com/internal">DDG</a>'
            '<a rel="nofollow" '
            'href="https://example.com">Example</a>'
        )
        results = WebSearchTool._parse_ddg_results(html, max_results=5)
        urls = [r[1] for r in results]
        assert not any("duckduckgo.com" in u for u in urls)

    def test_empty_html(self) -> None:
        results = WebSearchTool._parse_ddg_results("", max_results=5)
        assert results == []

    def test_cleans_html_from_snippets(self) -> None:
        html = (
            '<a rel="nofollow" href="https://test.com">Test</a>'
            '<td class="result-snippet">'
            "<b>Bold</b> normal text</td>"
        )
        results = WebSearchTool._parse_ddg_results(html, max_results=5)
        assert len(results) == 1
        assert "<b>" not in results[0][2]
        assert "Bold" in results[0][2]
