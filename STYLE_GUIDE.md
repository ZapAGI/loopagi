# LoopAGI Book 2 - Style Guide

## Engineering Manual Style (Knuth Tradition)

This is NOT Volume 1. No stories. No philosophy. No narrative vignettes.
Every page earns its place with code, algorithms, or architecture.

---

## Core Principles

1. **Code first.** Show the implementation, then explain it.
2. **Every chapter ships code.** No chapter exists without a module, tests, and benchmarks.
3. **Algorithms over analogies.** Use Big-O notation, data structures, flowcharts.
4. **Show the tests.** Every function gets tested. The tests ARE the specification.
5. **Measure everything.** Benchmarks, latency numbers, accuracy scores.
6. **No hand-waving.** If you cannot show the code, do not claim the capability.

## Chapter Structure

Every chapter follows this exact template:

```
1. Problem Statement (2-3 sentences: what we are building and why)
2. Interface Design (the public API before implementation)
3. Implementation (the code, walked through section by section)
4. Tests (pytest tests that serve as living specification)
5. Benchmarks (performance measurements where applicable)
6. Configuration (TOML config options for this component)
7. Integration (how this module connects to the rest of LoopAGI)
```

## Formatting Rules

- NEVER use em dashes. Use commas, colons, or parentheses.
- Use fenced code blocks with language hints for ALL code
- Use type hints on every function signature shown
- Use docstrings on every class and public method shown
- Tables for comparisons (never inline lists of options)
- Numbered lists for sequential steps
- Bullet lists for non-sequential items
- Bold for first use of a technical term

## Code Style in the Book

- Python 3.12+ features only
- Type hints required on all function signatures
- Docstrings required on all classes and public methods
- PEP 8 compliance
- 100 character line limit
- dataclasses for data containers
- Enum for string constants
- pathlib.Path over os.path
- f-strings over .format()
- match/case over if/elif chains where applicable

## What NOT to Include

- Personal anecdotes or stories
- Philosophical reflections
- Narrative vignettes or fictional scenarios
- Historical references (unless directly relevant to an algorithm)
- Motivational content
- References to God in the Loop themes (that was Vol 1)

## What TO Include

- Algorithm pseudocode before Python implementation
- Complexity analysis (time and space)
- Sequence diagrams for multi-agent interactions (Mermaid)
- Architecture diagrams (D2 or Mermaid)
- Benchmark tables with real numbers
- Error handling patterns
- Edge cases and how they are handled
- Configuration examples

## Tone

- Technical and precise
- Third person for descriptions ("The router selects...")
- Imperative for instructions ("Create a new file...")
- Present tense for behavior ("The agent returns...")
- No hedging ("This might work" -> "This handles X by Y")

---

*LoopAGI: The Engineering Manual - Copyright 2026 Alexandros Karales. MIT License.*
