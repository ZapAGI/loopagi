"""Tests for loopagi.tools_search module."""

from __future__ import annotations

from pathlib import Path

from loopagi.tools.search import SearchTool


class TestSearchToolGrep:
    """Tests for content search (grep)."""

    def test_grep_finds_match(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("def hello():\n    return 'world'\n")
        tool = SearchTool(cwd=str(tmp_path))
        result = tool.execute(action="grep", pattern="hello", path=".")
        assert result.success
        assert "hello" in result.output

    def test_grep_no_match(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("def hello(): pass\n")
        tool = SearchTool(cwd=str(tmp_path))
        result = tool.execute(action="grep", pattern="nonexistent_xyz", path=".")
        assert result.success
        assert "no matches" in result.output.lower()

    def test_grep_empty_pattern(self, tmp_path: Path) -> None:
        tool = SearchTool(cwd=str(tmp_path))
        result = tool.execute(action="grep", pattern="", path=".")
        assert not result.success

    def test_grep_with_includes(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("target_word\n")
        (tmp_path / "readme.md").write_text("target_word\n")
        tool = SearchTool(cwd=str(tmp_path))
        result = tool.execute(action="grep", pattern="target_word", path=".", includes="*.py")
        assert result.success
        assert "main.py" in result.output


class TestSearchToolFind:
    """Tests for file name search."""

    def test_find_existing_file(self, tmp_path: Path) -> None:
        (tmp_path / "config.toml").write_text("[project]\n")
        tool = SearchTool(cwd=str(tmp_path))
        result = tool.execute(action="find", pattern="config", path=".")
        assert result.success
        assert "config" in result.output

    def test_find_no_match(self, tmp_path: Path) -> None:
        tool = SearchTool(cwd=str(tmp_path))
        result = tool.execute(action="find", pattern="nonexistent_xyz_file", path=".")
        assert result.success
        assert "no matches" in result.output.lower()

    def test_find_empty_pattern(self, tmp_path: Path) -> None:
        tool = SearchTool(cwd=str(tmp_path))
        result = tool.execute(action="find", pattern="", path=".")
        assert not result.success


class TestSearchToolSymbols:
    """Tests for Python symbol search."""

    def test_find_functions(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("def hello():\n    pass\n\ndef goodbye():\n    pass\n")
        tool = SearchTool(cwd=str(tmp_path))
        result = tool.execute(action="symbols", path=".", symbol_type="function")
        assert result.success
        assert "hello" in result.output
        assert "goodbye" in result.output

    def test_find_classes(self, tmp_path: Path) -> None:
        (tmp_path / "models.py").write_text("class User:\n    pass\n\nclass Order:\n    pass\n")
        tool = SearchTool(cwd=str(tmp_path))
        result = tool.execute(action="symbols", path=".", symbol_type="class")
        assert result.success
        assert "User" in result.output
        assert "Order" in result.output

    def test_find_all_symbols(self, tmp_path: Path) -> None:
        (tmp_path / "mixed.py").write_text("class Foo:\n    pass\n\ndef bar():\n    pass\n")
        tool = SearchTool(cwd=str(tmp_path))
        result = tool.execute(action="symbols", path=".", symbol_type="all")
        assert result.success
        assert "Foo" in result.output
        assert "bar" in result.output

    def test_empty_directory(self, tmp_path: Path) -> None:
        tool = SearchTool(cwd=str(tmp_path))
        result = tool.execute(action="symbols", path=".")
        assert result.success
        assert "no symbols" in result.output.lower()

    def test_unknown_action(self, tmp_path: Path) -> None:
        tool = SearchTool(cwd=str(tmp_path))
        result = tool.execute(action="unknown_action")
        assert not result.success

    def test_name(self) -> None:
        tool = SearchTool()
        assert tool.name == "search"
