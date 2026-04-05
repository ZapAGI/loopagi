"""Tests for loopagi.tools_edit module."""

from __future__ import annotations

from pathlib import Path

from loopagi.tools.edit import EditTool


class TestEditToolReplace:
    """Tests for find-and-replace editing."""

    def test_replace_single(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("hello world\nhello again\n")
        tool = EditTool()
        result = tool.execute(action="replace", path=str(f), old="hello", new="goodbye", count=1)
        assert result.success
        assert "1 occurrence" in result.output
        assert f.read_text() == "goodbye world\nhello again\n"

    def test_replace_all(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("hello world\nhello again\n")
        tool = EditTool()
        result = tool.execute(action="replace", path=str(f), old="hello", new="goodbye", count=0)
        assert result.success
        assert "2 occurrence" in result.output
        assert f.read_text() == "goodbye world\ngoodbye again\n"

    def test_replace_not_found(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("hello world\n")
        tool = EditTool()
        result = tool.execute(action="replace", path=str(f), old="xyz", new="abc")
        assert not result.success
        assert "not found" in result.error.lower()

    def test_replace_missing_file(self) -> None:
        tool = EditTool()
        result = tool.execute(action="replace", path="/nonexistent/file.py", old="a", new="b")
        assert not result.success

    def test_replace_no_path(self) -> None:
        tool = EditTool()
        result = tool.execute(action="replace", path="", old="a", new="b")
        assert not result.success

    def test_replace_no_old(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("hello\n")
        tool = EditTool()
        result = tool.execute(action="replace", path=str(f), old="", new="b")
        assert not result.success


class TestEditToolInsert:
    """Tests for line insertion."""

    def test_insert_at_line(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("line1\nline2\nline3\n")
        tool = EditTool()
        result = tool.execute(action="insert", path=str(f), line=2, content="inserted")
        assert result.success
        lines = f.read_text().splitlines()
        assert lines[1] == "inserted"
        assert len(lines) == 4

    def test_insert_at_beginning(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("line1\nline2\n")
        tool = EditTool()
        result = tool.execute(action="insert", path=str(f), line=1, content="header")
        assert result.success
        assert f.read_text().startswith("header")

    def test_insert_no_content(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("hello\n")
        tool = EditTool()
        result = tool.execute(action="insert", path=str(f), line=1, content="")
        assert not result.success


class TestEditToolDeleteLines:
    """Tests for line deletion."""

    def test_delete_single_line(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("line1\nline2\nline3\n")
        tool = EditTool()
        result = tool.execute(action="delete_lines", path=str(f), start=2, end=2)
        assert result.success
        lines = f.read_text().splitlines()
        assert len(lines) == 2
        assert "line2" not in lines

    def test_delete_range(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("line1\nline2\nline3\nline4\n")
        tool = EditTool()
        result = tool.execute(action="delete_lines", path=str(f), start=2, end=3)
        assert result.success
        lines = f.read_text().splitlines()
        assert len(lines) == 2
        assert lines == ["line1", "line4"]

    def test_delete_invalid_range(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("hello\n")
        tool = EditTool()
        result = tool.execute(action="delete_lines", path=str(f), start=3, end=1)
        assert not result.success


class TestEditToolPatch:
    """Tests for multi-edit patch."""

    def test_apply_multiple_edits(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("hello world\nfoo bar\n")
        tool = EditTool()
        edits = [
            {"old": "hello", "new": "goodbye"},
            {"old": "foo", "new": "baz"},
        ]
        result = tool.execute(action="patch", path=str(f), edits=edits)
        assert result.success
        assert "2/2" in result.output
        content = f.read_text()
        assert "goodbye" in content
        assert "baz" in content

    def test_partial_patch(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("hello world\n")
        tool = EditTool()
        edits = [
            {"old": "hello", "new": "goodbye"},
            {"old": "nonexistent", "new": "xxx"},
        ]
        result = tool.execute(action="patch", path=str(f), edits=edits)
        assert result.success
        assert "1/2" in result.output


class TestEditToolDiff:
    """Tests for diff generation."""

    def test_show_diff(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("hello world\n")
        tool = EditTool()
        result = tool.execute(
            action="diff", path=str(f),
            old_content="hello world\n",
            new_content="goodbye world\n",
        )
        assert result.success
        assert "-hello" in result.output or "hello" in result.output

    def test_no_diff(self, tmp_path: Path) -> None:
        tool = EditTool()
        result = tool.execute(
            action="diff", path="test.py",
            old_content="same\n",
            new_content="same\n",
        )
        assert result.success
        assert "no differences" in result.output.lower()

    def test_unknown_action(self) -> None:
        tool = EditTool()
        result = tool.execute(action="unknown_action")
        assert not result.success
