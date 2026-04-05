"""
Chapter 19: Tool Integration Demo

An agent with access to infrastructure is an agent that can build.
System integration as a form of embodiment: the agent that can
touch the world.
"""

from __future__ import annotations

from loopagi.tools.base import FileTool, ShellTool, ToolRegistry


def demo() -> None:
    """Demonstrate the tool registry and tool execution."""
    print("Chapter 19: Tool Integration")
    print("=" * 60)

    registry = ToolRegistry()
    registry.register(ShellTool(timeout=10))
    registry.register(FileTool())

    print("\nRegistered tools:")
    for tool in registry.list_tools():
        print(f"  - {tool['name']}: {tool['description']}")

    # Demonstrate shell tool
    print("\n\nShell Tool Demos:")
    print("-" * 50)

    shell_commands = [
        ("Safe command", {"command": "echo 'Hello from LoopAGI!'"}),
        ("List files", {"command": "ls -la /tmp 2>/dev/null | head -5"}),
        ("Python version", {"command": "python3 --version"}),
        ("Blocked command", {"command": "rm -rf /"}),
    ]

    for label, kwargs in shell_commands:
        result = registry.execute("shell", **kwargs)
        if result.success:
            status = "OK"
        elif "blocked" in result.error.lower():
            status = "BLOCKED"
        else:
            status = "FAIL"
        output = result.output.strip()[:60] if result.output else result.error[:60]
        print(f"  [{status:>7}] {label}: {output}")

    # Demonstrate file tool
    print("\n\nFile Tool Demos:")
    print("-" * 50)

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = str(Path(tmpdir) / "test.py")

        # Write a file
        result = registry.execute(
            "file",
            action="write",
            path=test_file,
            content='def hello():\n    return "Hello from LoopAGI!"\n',
        )
        print(f"  [{'OK' if result.success else 'FAIL':>7}] Write: {result.output[:50]}")

        # Read it back
        result = registry.execute("file", action="read", path=test_file)
        print(f"  [{'OK' if result.success else 'FAIL':>7}] Read: {result.output.strip()[:50]}")

        # Check existence
        result = registry.execute("file", action="exists", path=test_file)
        print(f"  [{'OK' if result.success else 'FAIL':>7}] Exists: {result.output}")

        # List directory
        result = registry.execute("file", action="list", path=tmpdir)
        print(f"  [{'OK' if result.success else 'FAIL':>7}] List: {result.output.strip()[:50]}")

    print()
    print("Tools give agents the ability to interact with the world.")
    print("Embodiment is not about having a body.")
    print("It is about having consequences in the physical world.")


if __name__ == "__main__":
    demo()
