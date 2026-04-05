"""
Chapter 16: Dual-Language Architecture

Why a single language is never sufficient for AGI.

This module explores the architectural pattern of combining a
systems language with a high-level AI language. The book discusses
this as a general design principle: performance-critical components
(TUI, audio, networking) in a compiled language, AI logic in Python.

The companion code is Python-only. This chapter teaches the
architectural thinking, not the implementation of the compiled layer.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LanguageProfile:
    """Profile of a programming language for AGI components."""

    name: str
    strengths: list[str]
    weaknesses: list[str]
    best_for: list[str]
    startup_time_ms: float
    memory_safety: bool
    gc_pauses: bool


RUST = LanguageProfile(
    name="Rust",
    strengths=[
        "Zero-cost abstractions",
        "Memory safety without garbage collector",
        "Predictable latency (no GC pauses)",
        "Native performance (C/C++ level)",
        "Fearless concurrency",
        "Rich type system",
    ],
    weaknesses=[
        "Slower iteration cycle",
        "Steeper learning curve",
        "Smaller ML ecosystem",
        "Compile times",
    ],
    best_for=[
        "TUI / real-time interface",
        "Audio processing pipeline",
        "gRPC server",
        "State management",
        "Biometric processing",
        "System integration",
    ],
    startup_time_ms=0.5,
    memory_safety=True,
    gc_pauses=False,
)

PYTHON = LanguageProfile(
    name="Python",
    strengths=[
        "Rapid prototyping",
        "Richest ML/AI ecosystem",
        "LangChain, LangGraph integration",
        "Dynamic typing for agent logic",
        "Huge community and libraries",
        "Interactive development (REPL, notebooks)",
    ],
    weaknesses=[
        "GIL limits true parallelism",
        "Slower execution speed",
        "GC pauses possible",
        "Memory usage higher",
    ],
    best_for=[
        "Agent orchestration logic",
        "LLM integration (Ollama, LangChain)",
        "RAG pipelines",
        "Tool implementations",
        "Code generation/execution",
        "Knowledge management",
    ],
    startup_time_ms=50.0,
    memory_safety=False,
    gc_pauses=True,
)


@dataclass
class BridgePattern:
    """A pattern for bridging two languages in an AGI system."""

    name: str
    direction: str  # "system_to_ai" or "ai_to_system" or "bidirectional"
    protocol: str
    description: str


BRIDGE_PATTERNS: list[BridgePattern] = [
    BridgePattern(
        name="gRPC Service",
        direction="bidirectional",
        protocol="gRPC + Protocol Buffers",
        description="Typed RPC calls between system layer and AI layer",
    ),
    BridgePattern(
        name="Shared Memory / IPC",
        direction="bidirectional",
        protocol="Apache Arrow IPC",
        description="Zero-copy data sharing for large state objects",
    ),
    BridgePattern(
        name="Message Queue",
        direction="bidirectional",
        protocol="Redis / RabbitMQ / ZMQ",
        description="Async message passing for decoupled communication",
    ),
    BridgePattern(
        name="REST API",
        direction="bidirectional",
        protocol="HTTP + JSON",
        description="Simple synchronous communication (highest latency)",
    ),
    BridgePattern(
        name="Event Stream",
        direction="ai_to_system",
        protocol="SSE / WebSocket / gRPC streaming",
        description="Real-time agent activity updates for UI display",
    ),
]


def demo() -> None:
    """Display the dual-language architecture rationale."""
    print("Chapter 16: Dual-Language Architecture")
    print("=" * 60)

    for lang in [RUST, PYTHON]:
        print(f"\n{lang.name}")
        print("-" * 30)
        print(f"  Startup: {lang.startup_time_ms}ms")
        print(f"  Memory safety: {lang.memory_safety}")
        print(f"  GC pauses: {lang.gc_pauses}")
        print("\n  Strengths:")
        for s in lang.strengths:
            print(f"    + {s}")
        print("\n  Best for:")
        for b in lang.best_for:
            print(f"    - {b}")

    print("\n\nBridge Patterns: How Two Languages Become One System")
    print("-" * 50)
    for pattern in BRIDGE_PATTERNS:
        print(f"\n  {pattern.name} ({pattern.protocol})")
        print(f"    Direction: {pattern.direction}")
        print(f"    {pattern.description}")

    print("\n\nArchitecture Decision Record Pattern:")
    print("-" * 50)
    print("  Decision: Use a compiled language for the system layer,")
    print("            Python for AI agent logic")
    print("  Context:  AGI needs both real-time performance and rapid AI iteration")
    print("  Rationale: The AI ecosystem lives in Python. Performance-critical")
    print("             components (TUI, audio, networking) benefit from compilation.")
    print("  Consequence: Two codebases, one system, zero compromise")
    print()
    print("  'The body and the mind require different materials.")
    print("   The bridge between them is the architecture.'")
    print()
    print("  NOTE: The companion code is Python-only. The book discusses")
    print("  dual-language architecture as a design principle. The compiled")
    print("  layer is an exercise left to the ambitious reader.")


if __name__ == "__main__":
    demo()
