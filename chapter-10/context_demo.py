"""
Chapter 10: Context Engine Demo

The context engine provides agents with situational awareness:
- Rules: project-level conventions (.looprules)
- Actions: ring buffer of recent system activity
- Repo Map: structural overview of the codebase

Context is not data. It is relevance.
"""

from __future__ import annotations

from pathlib import Path

from loopagi.knowledge.context import ActionTracker, ActionType, RepoMap, RulesParser


def demo_rules() -> None:
    """Demonstrate the .looprules parser."""
    print("Context Engine: Rules Parser")
    print("=" * 50)

    rules_file = Path(__file__).parent / "rules_example.looprules"
    rules = RulesParser.parse(rules_file)

    print(f"\nParsed {len(rules)} rules from {rules_file.name}:")
    for rule in rules:
        print(f"  [{rule.section}] {rule.content}")

    # Format for prompt injection
    prompt_text = RulesParser.format_for_prompt(rules, max_chars=500)
    print(f"\nFormatted for prompt injection ({len(prompt_text)} chars):")
    print(prompt_text)


def demo_action_tracker() -> None:
    """Demonstrate the action tracker ring buffer."""
    print("\n\nContext Engine: Action Tracker")
    print("=" * 50)

    tracker = ActionTracker(max_actions=10)

    # Simulate a sequence of actions
    actions = [
        (ActionType.FILE_READ, "Read main.py"),
        (ActionType.AGENT_DELEGATION, "Delegated to coder: write fibonacci"),
        (ActionType.CODE_EXEC, "Executed: python main.py"),
        (ActionType.FILE_WRITE, "Wrote tests/test_main.py"),
        (ActionType.SHELL_COMMAND, "Ran: pytest tests/"),
        (ActionType.TOOL_CALL, "Called: git_status"),
        (ActionType.MEMORY_STORE, "Stored: user prefers pytest"),
        (ActionType.RAG_QUERY, "Queried: how does FastAPI routing work?"),
        (ActionType.ERROR, "ImportError: module 'foo' not found"),
        (ActionType.FILE_WRITE, "Fixed import in main.py"),
    ]

    for action_type, desc in actions:
        tracker.record(action_type, desc)

    print(f"\nTracked {tracker.count} actions")
    print("\nRecent actions (formatted for prompt):")
    print(tracker.format_for_prompt(max_items=5))


def demo_repo_map() -> None:
    """Demonstrate the repository map generator."""
    print("\n\nContext Engine: Repository Map")
    print("=" * 50)

    # Map the loopagi package itself
    loopagi_path = Path(__file__).parent.parent / "loopagi"
    if not loopagi_path.exists():
        print(f"  (loopagi/ not found at {loopagi_path}, skipping)")
        return

    repo_map = RepoMap(loopagi_path)
    map_text = repo_map.generate()
    print(f"\n{map_text}")


def demo() -> None:
    """Run all context engine demonstrations."""
    demo_rules()
    demo_action_tracker()
    demo_repo_map()

    print("\n" + "=" * 50)
    print("The context engine gives agents situational awareness.")
    print("Rules define the project. Actions show what happened.")
    print("The repo map reveals the structure.")
    print("Together: context is not data. It is relevance.")


if __name__ == "__main__":
    demo()
