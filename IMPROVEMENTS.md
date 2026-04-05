# LoopAGI Companion Code - Complete Audit & Improvements

**Audited:** March 18, 2026
**Branch:** `feature/audit-and-arc-agi`
**Auditor:** Alexandros Karales + Cascade AI

---

## Current State Summary

| Metric | Value |
|--------|-------|
| Python files | 89 |
| LoopAGI modules | 22 (4,800 LOC) |
| Chapter examples | 47 |
| Tests | 305 passing |
| Lint errors | 0 (ruff) |
| Agents | 7 |
| Tools | 7 |
| CLI commands | 20+ |

---

## Priority 1: Architecture Improvements

### 1.1 Agent Memory Is Session-Only

**Problem:** Each agent's conversation history lives in a Python list. When the CLI exits, all history is lost. The `/remember` command uses Qdrant, but agent conversation context does not persist between sessions.

**Fix:** Wire `MemoryStore` into `Agent.invoke()` so that relevant memories are automatically injected into the system prompt. On CLI startup, load the last N memories for each agent.

**Files:** `loopagi/agent.py`, `loopagi/cli.py`
**Effort:** Medium
**Impact:** High (continuity across sessions is a killer feature)

### 1.2 Router Has No Learning

**Problem:** The keyword router uses hardcoded patterns. If the user consistently overrides routing decisions, the router does not learn from it.

**Fix:** Add a `RoutingFeedback` mechanism: when the user says "no, send this to the coder instead," record the (task, intended_agent) pair. Over time, build a simple TF-IDF classifier from these corrections that supplements keyword matching.

**Files:** `loopagi/router.py`
**Effort:** Medium
**Impact:** Medium (makes the system feel adaptive)

### 1.3 Pipeline Has No Code Execution

**Problem:** The quality pipeline (plan -> code -> test -> review) generates code and tests, but never actually RUNS the tests. The tester writes pytest code, the reviewer reads it, but nobody executes it.

**Fix:** Add a `PipelineExecutor` stage after the tester that writes the code to a temp file, runs `pytest`, and feeds the real test results back to the reviewer. This closes the loop between generated tests and actual execution.

**Files:** `loopagi/pipeline.py`, `loopagi/tools_python.py`
**Effort:** High
**Impact:** Very High (transforms the pipeline from "generates tests" to "verifies code works")

### 1.4 No Streaming Output

**Problem:** All agent responses appear at once after the full inference completes. For longer responses (especially pipeline runs), the user stares at a blank screen for 10+ seconds.

**Fix:** Use `ChatOllama` streaming mode. Print tokens as they arrive. This requires changes to `Agent.invoke()` to yield chunks.

**Files:** `loopagi/agent.py`, `loopagi/cli.py`
**Effort:** Medium
**Impact:** High (dramatically improves perceived responsiveness)

### 1.5 CLI Is 768 Lines in One File

**Problem:** `cli.py` at 768 lines handles command parsing, tool execution, context management, memory, pipeline, git, export, and the main loop. This violates the project's own `.looprules` (modules under 300 lines).

**Fix:** Split into:
- `cli.py` - main loop + argument parsing (~150 lines)
- `cli_commands.py` - slash command handlers (~300 lines)
- `cli_tools.py` - tool command wrappers (~150 lines)
- `cli_context.py` - context/memory/export (~150 lines)

**Files:** `loopagi/cli.py`
**Effort:** Medium
**Impact:** Medium (maintainability, follows own rules)

---

## Priority 2: Missing Features

### 2.1 No Agent-to-Agent Communication

**Problem:** Agents can only be invoked by the router or pipeline. They cannot delegate to each other. The coder cannot ask the researcher for help mid-task.

**Fix:** Add `Agent.delegate(target_agent, message)` that routes through the event bus. The CLI shows delegations in the output.

**Files:** `loopagi/agent.py`, `loopagi/events.py`, `loopagi/router.py`
**Effort:** High
**Impact:** High (enables emergent multi-step reasoning)

### 2.2 No Conversation Branching

**Problem:** The conversation is linear. The user cannot say "go back to what the planner said" or "try a different approach."

**Fix:** Store conversation as a tree (not a list). Add `/branch` and `/switch` commands. Session-as-git already versions everything, so branches map naturally to git branches.

**Files:** `loopagi/cli.py`, `loopagi/session.py`
**Effort:** High
**Impact:** Medium

### 2.3 No Config File

**Problem:** Model, mode, and preferences are CLI arguments only. The user must type `--model qwen3:8b` every time.

**Fix:** Add `~/.config/loopagi/config.toml` with defaults:
```toml
[defaults]
model = "qwen3:8b"
mode = "Turbo"
verbose = false

[safety]
blocked_patterns_file = ""
trust_initial = 0.5
```

**Files:** `loopagi/cli.py` (new: `loopagi/config.py`)
**Effort:** Low
**Impact:** Medium

### 2.4 No Tool Result Caching

**Problem:** Running `/search def invoke` twice does the same grep both times. File reads are not cached. This wastes time in tight loops.

**Fix:** Add a TTL cache (30-second default) for tool results. Invalidate on file writes.

**Files:** `loopagi/tools.py`
**Effort:** Low
**Impact:** Low-Medium

---

## Priority 3: Test Coverage Gaps

### 3.1 No Tests for CLI (the largest module)

**Problem:** `cli.py` is 768 lines with 20+ commands but has ZERO dedicated unit tests. The `test_e2e.py` tests mock the entire system, but individual command handlers are untested.

**Fix:** Create `tests/test_cli.py` with tests for each slash command handler using mocked tools and agents.

**Effort:** Medium
**Impact:** High (cli.py is the most complex module)

### 3.2 No Tests for Memory Module

**Problem:** `loopagi/memory.py` has no dedicated test file. It is only tested indirectly through integration tests.

**Fix:** Create `tests/test_memory.py` with mocked Qdrant client.

**Effort:** Medium
**Impact:** Medium

### 3.3 No Tests for RAG Module

**Problem:** `loopagi/rag.py` (443 lines, the largest non-CLI module) has no dedicated tests.

**Fix:** Create `tests/test_rag.py` with mocked Qdrant and LLM.

**Effort:** Medium
**Impact:** High (rag.py is the most complex algorithmic module)

### 3.4 Async Tests Missing

**Problem:** `Agent.ainvoke()` and `AgentPool.execute_parallel()` use async, but no tests exercise the async paths.

**Fix:** Add async tests using `pytest-asyncio`.

**Effort:** Low
**Impact:** Medium

---

## Priority 4: Chapter Example Improvements

### 4.1 Chapters Without Real Interactivity

| Chapter | File | Issue | Suggested Fix |
|---------|------|-------|---------------|
| Ch 3 | `kardashev_scale.py` | Print-only visualization | Add matplotlib plot generation |
| Ch 3 | `scenario_2035.py` | Static text output | Add interactive scenario selector |
| Ch 3 | `unification_argument.py` | Just prints text | Add argument graph with networkx |
| Ch 15 | `local_first.py` | Just checks tool existence | Add performance benchmark (local vs API latency) |
| Ch 16 | `dual_language.py` | Conceptual only | Add real gRPC client/server stub |
| Ch 20 | `agent_kernel.py` | Simulated kernel | Add real process spawning with multiprocessing |
| Ch 21 | `emergence_thesis.py` | Random number simulation | Link to real_emergence_demo.py results |
| Ch 22 | `capstone.py` | Prints architecture | Add system health check that verifies all modules load |
| Ch 22 | `letter_to_agents.py` | Just prints text | Fine as-is (thematic) |

### 4.2 Missing Chapter Examples

| Chapter | Topic | What's Missing |
|---------|-------|----------------|
| Ch 8 | Memory | No demo of session resume across CLI restarts |
| Ch 9 | RAG | No comparison of chunking strategies (fixed vs semantic) |
| Ch 10 | Context | No `rules_example.looprules` file (demo references it) |
| Ch 13 | Events | No demo of event-driven auto-fix (scanner finds issue, coder fixes) |
| Ch 19 | Docker | `docker_agent.py` requires Docker; no fallback |

---

## Priority 5: Code Quality

### 5.1 Inline Imports

Several modules use inline imports to avoid circular dependencies:
- `loopagi/modes.py:99` imports `SafetyChecker` inline
- `loopagi/rag.py:181` imports `uuid` inline
- `loopagi/rag.py:338` imports Qdrant models inline
- `loopagi/rag.py:417` imports `re` inline
- `loopagi/cli.py` imports `MemoryStore` and `QualityPipeline` inline

**Fix:** Restructure imports. Use TYPE_CHECKING for type annotations. Move lazy imports to a centralized pattern.

### 5.2 Inconsistent Error Handling

- `tools_web.py` catches broad `Exception` in two places
- `session.py:262` silently catches all git commit errors
- `memory.py` does not handle Qdrant connection failures gracefully

**Fix:** Use specific exception types. Log errors. Return structured error results.

### 5.3 Magic Numbers

- `router.py:91` keyword threshold 0.3 hardcoded
- `safety.py:164` decay rate 0.001 hardcoded
- `agent.py:40` max_history 20 hardcoded
- `rag.py:87-88` chunk_size 500, overlap 50 hardcoded

**Fix:** Move to dataclass configs or module-level constants with documentation.

---

## Priority 6: Documentation

### 6.1 Missing API Documentation

No module has a generated API reference. Readers who want to extend LoopAGI have to read source code.

**Fix:** Add `docs/` directory with auto-generated API docs using `pdoc` or `mkdocs`.

### 6.2 No Architecture Diagram

The README describes the architecture in text. A visual diagram (D2, Mermaid, or TikZ) would help.

**Fix:** Add `docs/architecture.d2` or `docs/architecture.mermaid`.

### 6.3 Chapter READMEs Are Thin

Most chapter READMEs are 3-5 lines. They should explain what the reader learns, what to run, and what to look for in the output.

---

## Implementation Roadmap

### Phase 1 (Immediate, 1-2 days)
- [ ] 1.3: Pipeline code execution (highest impact)
- [ ] 3.1: CLI tests
- [ ] 3.3: RAG tests
- [ ] 4.2: Missing `rules_example.looprules`
- [ ] 5.3: Extract magic numbers to constants

### Phase 2 (Near-term, 3-5 days)
- [ ] 1.1: Persistent agent memory
- [ ] 1.4: Streaming output
- [ ] 1.5: Split cli.py
- [ ] 2.3: Config file
- [ ] 3.2: Memory tests

### Phase 3 (Medium-term, 1-2 weeks)
- [ ] 1.2: Router learning
- [ ] 2.1: Agent-to-agent communication
- [ ] 2.2: Conversation branching
- [ ] 4.1: Interactive chapter improvements
- [ ] 6.1: API documentation

---

*God in the Loop - Companion Code Audit*
*Copyright 2026 Alexandros Karales. All Rights Reserved.*
