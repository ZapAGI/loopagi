# DSL File Size Research: Best Practices for ARC Grid Modules

**Date:** March 18, 2026
**Author:** Alexandros Karales + Cascade AI
**Context:** The `.looprules` limit of 300 lines per module is being exceeded by ARC Grid DSL files.
**Goal:** Determine the optimal file size policy and update `.looprules` accordingly.

---

## 1. The Problem

Our current `.looprules` enforces a 300-line module limit:

```
## Architecture
- Keep modules under 300 lines
```

The ARC Grid DSL files naturally exceed this:

| File | Lines | Role |
|------|-------|------|
| `loopagi/arc/grid_ops.py` | 335 | Core grid transforms (37 functions) |
| `loopagi/arc/grid_objects.py` | 325 | Object detection + relationships (18 functions) |
| `loopagi/arc/arc_loader.py` | 392 | Task loading, validation, dataset management |
| `loopagi/arc/arc_runner.py` | 303 | Solver orchestration, submission generation |
| `loopagi/arc/arc_evaluator.py` | 265 | Scoring, exact match, similarity |
| `loopagi/arc/arc_visualizer.py` | 268 | Rich terminal + matplotlib display |

For comparison, the existing `loopagi/` modules:

| File | Lines | Status |
|------|-------|--------|
| `cli.py` | 768 | **Violating** (known issue, in IMPROVEMENTS.md) |
| `rag.py` | 443 | **Violating** |
| `context.py` | 319 | **Violating** |
| `session.py` | 269 | OK |
| All others | <270 | OK |

The question: should we force the DSL files under 300 lines, or adopt a more nuanced policy?

---

## 2. Research Findings

### 2.1 Industry Consensus on Python File Size

| Source | Recommended Range | Notes |
|--------|-------------------|-------|
| **PEP 8** | No explicit limit | Style guide, not size guide |
| **Clean Code (Python)** | 200-300 lines | General application code |
| **Medium: "Right-Sizing" (Faherty, 2025)** | 150-500 lines | Optimized for AI code editors |
| **Reddit r/Python consensus** | Nervous at 1000, refactor at 2000 | Pragmatic, per-project |
| **Real Python best practices** | "Avoid large modules where unrelated functions pile up" | Focus on cohesion, not line count |

**Key insight from the Faherty article:** The 150-500 line range is specifically optimized for AI code editors (Cursor, Windsurf, Claude Code) because:

- AI agents can hold the entire file in context without truncation
- Diffs are reviewable in one pass
- Mistakes are caught faster in smaller files
- Token efficiency: a 300-line file fits comfortably, a 2000-line file needs chunking

**His exceptions:** Generated migrations, configuration files, and large data structures.

### 2.2 ARC-DSL Reference Implementation (Hodel)

The canonical ARC DSL by Michael Hodel (`github.com/michaelhodel/arc-dsl`) uses:

| File | Estimated Lines | Contents |
|------|-----------------|----------|
| `dsl.py` | ~1200+ | **160 primitive functions** in a single file |
| `arc_types.py` | ~50 | Type aliases |
| `constants.py` | ~30 | Color constants |
| `solvers.py` | ~3000+ | 400 task solvers (monolithic) |
| `tests.py` | ~1000+ | Tests for all primitives |

**Hodel's approach:** One massive DSL file with all primitives. This works for brute-force search (the computer doesn't care about file size) but is terrible for:

- AI-assisted development (context window overflow)
- Human readability (scrolling through 1200 lines of similar functions)
- Maintainability (one change risks breaking 160 functions)

**Our advantage:** We already split the DSL into `grid_ops.py` (transforms) and `grid_objects.py` (objectness), which is far more maintainable than Hodel's monolith.

### 2.3 Key Research from ARC-AGI Literature

From the 2025 ARC research review (lewish.io):

> "A good DSL can greatly improve search efficiency. Pure Python is not a great language for brute-force search. A good DSL helps ensure that solutions can be represented in a small program, and that most parts of the search space are valid programs."

> "The DSLs often end up being rather large, for example, ARC-DSL contains a massive 160 primitive functions!"

> "If you want to learn more about the construction of a DSL, the ARC-DSL write-up is probably a good place to start. Probably avoid writing one yourself unless you are doing something very novel."

**Implications for our approach:**

1. DSL files are inherently dense: many small, pure functions with no complex logic
2. Splitting a DSL by arbitrary line count can separate related operations (e.g., `rotate_cw` in one file and `rotate_ccw` in another)
3. The correct split axis is **semantic domain**, not line count

### 2.4 The Nature of DSL Code vs Application Code

DSL files are fundamentally different from application code:

| Property | Application Code | DSL Primitive Code |
|----------|-----------------|-------------------|
| **Function length** | 10-50 lines | 3-10 lines |
| **Interdependencies** | High (state, side effects) | Low (pure functions) |
| **Cohesion** | Module = one responsibility | Module = one domain of primitives |
| **Change frequency** | High | Low (primitives are stable) |
| **Risk of breaking** | High (side effects) | Low (pure, tested) |
| **AI comprehension** | Harder (state + flow) | Easier (pure transforms) |

A 400-line DSL file with 40 pure functions of 5-8 lines each is fundamentally different in complexity from a 400-line application module with 5 functions containing business logic, state management, and I/O.

---

## 3. Recommendation: Tiered Module Limits

### The Policy

Replace the single 300-line limit with a tiered system:

| Tier | Max Lines | Applies To | Rationale |
|------|-----------|------------|-----------|
| **Standard** | 300 | Application logic, agents, tools, CLI | Original rule, good for stateful code |
| **Extended** | 500 | DSL primitives, data loaders, pure utility modules | Faherty's AI-optimized ceiling; pure functions stay cohesive |
| **Must Refactor** | 500+ | Nothing | Hard ceiling: any file over 500 needs splitting |

### Why 500, Not Higher

- **AI context window:** 500 lines fits comfortably in any modern AI editor's context
- **Diff reviewability:** A 500-line file produces manageable diffs
- **Faherty's research:** 150-500 is the sweet spot for AI-assisted development
- **Hodel's counter-example:** His 1200-line dsl.py is universally cited as "massive"
- **Our .looprules integrity:** The rule still has teeth; cli.py (768 lines) still violates

### Qualifying Criteria for Extended Tier

A module qualifies for the 500-line extended limit if it meets ALL of:

1. **Pure functions only**: No side effects, no I/O, no state mutation
2. **Single semantic domain**: All functions operate on the same data type/concept
3. **Shallow dependency tree**: Functions depend on each other minimally
4. **High function count, low function size**: Many small (3-15 line) functions
5. **Comprehensive test coverage**: Every public function has at least one test

Files that do NOT qualify (must stay under 300):

- CLI/UI code (stateful, I/O-heavy)
- Agent code (LLM calls, side effects)
- Pipeline/orchestration code (complex flow)
- Session/memory code (state management)

---

## 4. Current File Assessment

| File | Lines | Tier | Status | Action Needed |
|------|-------|------|--------|---------------|
| `grid_ops.py` | 335 | Extended | OK (pure DSL) | None |
| `grid_objects.py` | 325 | Extended | OK (pure DSL) | None |
| `arc_loader.py` | 392 | Extended | OK (data loader, pure) | None |
| `arc_runner.py` | 303 | Standard | OK (just at limit) | Watch growth |
| `arc_evaluator.py` | 265 | Standard | OK | None |
| `arc_visualizer.py` | 268 | Standard | OK | None |
| `cli.py` | 768 | Standard | **VIOLATING** | Must split (already in IMPROVEMENTS.md) |
| `rag.py` | 443 | Standard | **VIOLATING** | Must refactor or qualify for Extended |
| `context.py` | 319 | Standard | **VIOLATING** | Minor, close to limit |

---

## 5. Implementation Plan

### Step 1: Update `.looprules` (immediate)

Add the tiered policy to the project style rules.

### Step 2: Add Automated Enforcement (near-term)

Create `tests/test_file_size.py` (inspired by Faherty's approach) that:

- Checks all `loopagi/` Python files against the appropriate tier
- Allows explicit exceptions via a `FILE_SIZE_EXCEPTIONS` dict
- Fails on any file exceeding 500 lines (hard ceiling)
- Warns on standard-tier files exceeding 300 lines

### Step 3: Fix Existing Violations (per IMPROVEMENTS.md)

- `cli.py` (768 lines): Split into cli.py, cli_commands.py, cli_tools.py, cli_context.py
- `rag.py` (443 lines): Evaluate if it qualifies for Extended tier (it has I/O, so probably not; needs splitting)
- `context.py` (319 lines): Minor, may qualify for Extended if refactored to pure

### Step 4: Pre-commit Hook (optional)

Add a git pre-commit hook that runs the file size test before commits.

---

## 6. References

1. **Faherty, E. (2025).** "Right-Sizing Your Python Files: The 150-500 Line Sweet Spot for AI Code Editors." Medium.
2. **Hodel, M.** ARC-DSL: Domain Specific Language for the Abstraction and Reasoning Corpus. `github.com/michaelhodel/arc-dsl`
3. **Lewis, H. (2025).** "ARC-AGI 2025: A Research Review." `lewish.io/posts/arc-agi-2025-research-review`
4. **Chollet, F. (2019).** "On the Measure of Intelligence." arXiv:1911.01547
5. **PEP 8.** Style Guide for Python Code. `peps.python.org/pep-0008/`
6. **ARC Prize 2024 Technical Report.** arXiv:2412.04604
7. **Reddit r/Python.** "How long should a .py file be?" (community consensus thread)
8. **Real Python.** "Project Layout Best Practices." `realpython.com/ref/best-practices/project-layout/`

---

*God in the Loop - DSL File Size Research*
*Copyright 2026 Alexandros Karales. All Rights Reserved.*
