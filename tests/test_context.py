"""Tests for loopagi.context module."""

from __future__ import annotations

from pathlib import Path

from loopagi.knowledge.context import ActionTracker, ActionType, RepoMap, Rule, RulesParser


class TestRulesParser:
    """Tests for the .looprules parser."""

    def test_parse_empty_file(self, tmp_path: Path) -> None:
        rules_file = tmp_path / ".looprules"
        rules_file.write_text("", encoding="utf-8")
        rules = RulesParser.parse(rules_file)
        assert rules == []

    def test_parse_missing_file(self, tmp_path: Path) -> None:
        rules = RulesParser.parse(tmp_path / "nonexistent")
        assert rules == []

    def test_parse_rules(self, tmp_path: Path) -> None:
        rules_file = tmp_path / ".looprules"
        content = "## Code Style\n- Use type hints\n- Follow PEP 8\n\n## Testing\n- Use pytest\n"
        rules_file.write_text(content, encoding="utf-8")
        rules = RulesParser.parse(rules_file)
        assert len(rules) == 3
        assert rules[0].section == "Code Style"
        assert rules[0].content == "Use type hints"
        assert rules[2].section == "Testing"

    def test_merge_project_overrides_global(self) -> None:
        project = [Rule(section="Style", content="tabs", source="project")]
        global_rules = [
            Rule(section="Style", content="spaces", source="global"),
            Rule(section="Testing", content="pytest", source="global"),
        ]
        merged = RulesParser.merge(project, global_rules)
        assert len(merged) == 2
        assert merged[0].content == "tabs"
        assert merged[1].section == "Testing"

    def test_format_for_prompt(self) -> None:
        rules = [
            Rule(section="Style", content="Use type hints", source="project"),
            Rule(section="Style", content="PEP 8", source="project"),
        ]
        text = RulesParser.format_for_prompt(rules)
        assert "PROJECT RULES:" in text
        assert "Use type hints" in text

    def test_format_empty(self) -> None:
        assert RulesParser.format_for_prompt([]) == ""


class TestActionTracker:
    """Tests for the ActionTracker."""

    def test_record_and_recent(self) -> None:
        tracker = ActionTracker(max_actions=5)
        tracker.record(ActionType.FILE_WRITE, "Created main.py")
        tracker.record(ActionType.SHELL_COMMAND, "Ran pytest")
        assert tracker.count == 2
        recent = tracker.recent(10)
        assert len(recent) == 2

    def test_ring_buffer_limit(self) -> None:
        tracker = ActionTracker(max_actions=3)
        for i in range(10):
            tracker.record("file_write", f"Action {i}")
        assert tracker.count == 3

    def test_format_for_prompt(self) -> None:
        tracker = ActionTracker()
        tracker.record(ActionType.FILE_WRITE, "Created test.py")
        text = tracker.format_for_prompt()
        assert "RECENT ACTIONS:" in text
        assert "file_write" in text

    def test_clear(self) -> None:
        tracker = ActionTracker()
        tracker.record(ActionType.ERROR, "something failed")
        tracker.clear()
        assert tracker.count == 0

    def test_string_action_type(self) -> None:
        tracker = ActionTracker()
        tracker.record("code_exec", "ran script")
        assert tracker.count == 1


class TestRepoMap:
    """Tests for the RepoMap."""

    def test_scan_directory(self, tmp_path: Path) -> None:
        # Create a simple Python file
        py_file = tmp_path / "main.py"
        py_file.write_text("import os\n\ndef hello():\n    pass\n\nclass Foo:\n    pass\n")

        repo_map = RepoMap(tmp_path)
        nodes = repo_map.scan()
        assert "main.py" in nodes
        assert "hello" in nodes["main.py"].functions
        assert "Foo" in nodes["main.py"].classes
        assert "os" in nodes["main.py"].imports

    def test_generate_output(self, tmp_path: Path) -> None:
        py_file = tmp_path / "app.py"
        py_file.write_text("def run():\n    pass\n")

        repo_map = RepoMap(tmp_path)
        output = repo_map.generate()
        assert "REPOSITORY MAP" in output
        assert "app.py" in output
        assert "run" in output

    def test_empty_directory(self, tmp_path: Path) -> None:
        repo_map = RepoMap(tmp_path)
        nodes = repo_map.scan()
        assert len(nodes) == 0
