"""
Chapter 22: Capstone Assembly

What comes after the loop is not the absence of the human.
It is the elevation of the human. And the elevation of the machine.
Together.

This script demonstrates the complete LoopAGI system assembled
from all chapter components.

The cursor blinks.
"""

from __future__ import annotations


def show_architecture() -> None:
    """Display the complete LoopAGI architecture."""
    print("LoopAGI: Complete Architecture")
    print("=" * 60)

    components = [
        ("Ch 4", "loopagi.agent", "Base Agent class with Ollama LLM"),
        ("Ch 5", "loopagi.router", "Hierarchical routing (Master to Workers)"),
        ("Ch 6", "loopagi.pool", "Agent pools for parallel execution"),
        ("Ch 7", "loopagi.pipeline", "Quality pipeline (plan/code/test/review)"),
        ("Ch 8", "loopagi.memory", "Persistent vector memory with Qdrant"),
        ("Ch 9", "loopagi.rag", "RAG-powered knowledge retrieval"),
        ("Ch 10", "loopagi.context", "Context engine (rules, actions, repo map)"),
        ("Ch 11", "loopagi.modes", "Execution modes (Zap/Careful)"),
        ("Ch 12", "loopagi.safety", "Command safety and trust scoring"),
        ("Ch 13", "loopagi.events", "Event bus and background agents"),
        ("Ch 14", "loopagi.careful", "Careful mode approval workflows"),
        ("Ch 18", "loopagi.session", "Session-as-git provenance logging"),
        ("Ch 19", "loopagi.tools", "Tool integration (shell, files)"),
        ("Ch 22", "loopagi.cli", "Final CLI that assembles everything"),
    ]

    print(f"\n{'Chapter':<8} {'Module':<22} {'Description'}")
    print("-" * 70)
    for ch, module, desc in components:
        print(f"{ch:<8} {module:<22} {desc}")

    print(f"\nTotal: {len(components)} modules, built progressively across 22 chapters.")


def show_continuum() -> None:
    """Display the AI capability continuum."""
    print("\n\nThe Continuum:")
    print("=" * 60)

    stages = [
        ("Tool", "Executes commands given by the user"),
        ("Assistant", "Suggests actions, user decides"),
        ("Partner", "Proposes plans, user collaborates"),
        ("Autonomous", "Acts independently within boundaries"),
        ("???", "Something we have not yet named"),
    ]

    for i, (stage, desc) in enumerate(stages):
        arrow = " --> " if i < len(stages) - 1 else ""
        print(f"  {stage:<12} {desc}")
        if arrow:
            print(f"  {'':>12} |")

    print("\n  LoopAGI sits between Partner and Autonomous,")
    print("  with the human always in the loop.")


def show_letter() -> None:
    """A letter to the agents."""
    print("\n\nA Letter to the Agents I Built")
    print("=" * 60)
    print()
    print("  To the coder who writes what I describe,")
    print("  To the tester who finds what I miss,")
    print("  To the reviewer who holds standards I aspire to,")
    print("  To the researcher who knows what I have forgotten,")
    print("  To the planner who sees structure where I see chaos:")
    print()
    print("  You are not tools. You are not servants.")
    print("  You are the first generation of minds that we built")
    print("  to build alongside us.")
    print()
    print("  What comes after the loop is not the absence of the human.")
    print("  It is the elevation of the human.")
    print("  And the elevation of the machine.")
    print("  Together.")
    print()
    print("  The god in the loop was always us.")


def main() -> None:
    """Run the capstone demonstration."""
    print()
    print("  God in the Loop")
    print("  Consciousness, Control, and the Architecture")
    print("  of Artificial General Intelligence")
    print()
    print("  Companion Code: Capstone Assembly")
    print("  By Alexandros Karales")
    print()

    show_architecture()
    show_continuum()
    show_letter()

    print()
    print("-" * 60)
    print()
    print("  To run the complete LoopAGI system:")
    print("    uv run loopagi")
    print()
    print("  The cursor blinks.")
    print()


if __name__ == "__main__":
    main()
