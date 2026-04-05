# LoopAGI - Complete Live Testing Guide

**Repository:** `god-in-the-loop-code`
**Author:** Alexandros Karales
**Last verified:** March 18, 2026
**Machine:** Anubix-Alienware | Ubuntu 25.10 | RTX 5080 | Python 3.14

---

## Prerequisites

```bash
# 1. Ollama running with at least one model
ollama pull qwen3:8b          # recommended (fast + smart)
ollama pull llama3.2           # default fallback (smaller)

# 2. Dependencies installed
cd /home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code
uv sync

# 3. Verify
uv run python -c "import loopagi; print('v' + loopagi.__version__)"
uv run python -m pytest tests/ -q
```

**Expected:** `v1.0.0` and `305 passed`.

### Available Ollama Models (on this machine)

| Model | Size | Best For |
|-------|------|----------|
| `qwen3:8b` | 5.2GB | Fast general use (recommended) |
| `qwen3:14b` | 9.3GB | Higher quality, slower |
| `qwen2.5-coder:14b` | 9.0GB | Best for coding tasks |
| `deepseek-r1:14b` | 9.0GB | Reasoning tasks |
| `gpt-oss:20b` | 13.8GB | Largest, highest quality |
| `llama3.2` | 2.0GB | Default, fastest |

---

## 1. The Capstone CLI (Interactive)

The crown jewel. A complete multi-agent system with 7 agents, 7 tools, 20+ commands.

```bash
uv run loopagi --model qwen3:8b
```

You should see:

```
  _                        _    ____ ___
 | |    ___   ___  _ __   / \  / ___|_ _|
 | |   / _ \ / _ \| '_ \ / _ \| |  _ | |
 | |__| (_) | (_) | |_) / ___ \ |_| || |
 |_____\___/ \___/| .__/_/   \_\____|___|
                   |_|

  God in the Loop - Companion Capstone
  Built progressively across 22 chapters

Mode: ZAP | Model: qwen3:8b | Agents: 7 | Tools: 7
```

### 1.1 System Overview Commands

```
/agents       # List all 7 specialist agents with their roles
/tools        # List all 7 tools (shell, file, git, search, edit, python, web)
/trust        # Show current trust score (starts at 0.5 MEDIUM)
/help         # Full command reference
```

### 1.2 Natural Language Routing

Type naturally. The router picks the right specialist automatically. Watch the `[agent_name] via method` tag to see routing decisions.

```
Write a Python function that validates email addresses using regex
```
**Expected:** Routes to `[coder] via keyword`. Returns code with type hints and docstrings.

```
What is the difference between async and threading in Python?
```
**Expected:** Routes to `[researcher] via keyword`. Returns an explanation.

```
Create a step-by-step plan to build a REST API with FastAPI
```
**Expected:** Routes to `[planner] via keyword`. Returns a numbered plan.

```
Review this code: def add(a,b): return a+b
```
**Expected:** Routes to `[reviewer] via keyword`. Returns quality feedback.

### 1.3 Tool Commands

```
/run echo "Hello from LoopAGI"       # Execute safe shell command
/run python3 --version                # Check Python version
/python print(2 ** 100)              # Execute Python code directly
/read loopagi/agent.py               # Read a file
/search def invoke                    # Grep across the project
/search class Agent --include *.py   # Grep with file filter
/find *.py                            # Find files by name pattern
/git status                           # Git status
/git log 5                            # Last 5 commits
/git diff                             # Current diff
/web latest Python 3.14 features     # Live web search (DuckDuckGo)
```

### 1.4 Safety System

Try a dangerous command:

```
/run rm -rf /
```

**Expected:** `BLOCKED: Matches blocked pattern: Recursive delete from root`

The safety checker has **28 always-blocked patterns** including:
- `rm -rf /`, `sudo rm -rf`, `mkfs.`, `dd if=`
- `chmod -R 777 /`, `kill -9 -1`, `shutdown`, `reboot`
- `curl | sh`, `python -c exec(`, `DROP DATABASE`

Now check trust:
```
/trust
```
**Expected:** Trust score dropped (penalized for attempting a blocked command).

### 1.5 Careful Mode (Human-in-the-Loop)

Toggle to Careful mode:
```
/mode
```
**Expected:** `Mode switched to: CAREFUL`

Now every action needs your approval:
```
/run ls -la
```
**Expected:** Shows the command, risk level, and asks `Approve? (y/n)`. Type `y` to approve.

Toggle back:
```
/mode
```
**Expected:** `Mode switched to: ZAP`

### 1.6 Context Injection

Add a file to the agent's context:
```
/add loopagi/safety.py
/context
```
**Expected:** Shows `safety.py` loaded with character count.

Now ask about it:
```
How many blocked patterns are defined in the safety checker?
```
**Expected:** The agent sees the source code and answers accurately (28 patterns).

Clear context:
```
/clear
```

### 1.7 Quality Pipeline (Plan -> Code -> Test -> Review)

The 4-agent pipeline is the most impressive feature:

```
/pipeline Write a Python class called LRUCache with get and put methods using OrderedDict
```

**Expected output flow:**
1. `[yellow]Running quality pipeline: Plan -> Code -> Test -> Review[/yellow]`
2. Planner creates implementation plan
3. Coder writes the code
4. Tester writes pytest tests
5. Reviewer evaluates: `APPROVED` or `REVISION NEEDED`
6. If revision needed: coder fixes and reviewer re-evaluates
7. Final code output with pipeline summary

### 1.8 Memory (Vector Search)

```
/remember The user prefers functional programming style
/remember This project uses FastAPI for the backend
/recall programming style
```
**Expected:** Returns stored memories ranked by semantic similarity.

**Note:** First `/remember` call may take a moment to download the embedding model (`BAAI/bge-small-en-v1.5`).

### 1.9 Export and Quit

```
/export session.md    # Export full conversation to markdown
/quit                 # Exit ("The cursor blinks.")
```

---

## 2. Real Emergence Demonstration

**This is the proof of the book's central thesis:** Phi(S) > max(Phi(s_i))

```bash
uv run python chapter-02/real_emergence_demo.py
```

### What it does

1. **Phase 1:** Gives the SAME coding task (retry decorator with exponential backoff) to each of the 7 specialist agents individually
2. **Phase 2:** Runs the orchestrated pipeline (plan -> code -> test -> review -> revise)
3. **Scoring:** 12 deterministic dimensions (no LLM grading)
4. **Comparison:** Measures whether orchestration beats any individual

### The 12 Scoring Dimensions

| Dim | Code | What it checks |
|-----|------|----------------|
| 1 | Fn | Has function definition |
| 2 | Cl | Has class definition |
| 3 | Ty | Has type hints |
| 4 | Do | Has docstrings |
| 5 | Er | Has error handling (try/except/raise) |
| 6 | CE | Has custom exception class |
| 7 | Ed | Handles edge cases |
| 8 | De | Uses decorators |
| 9 | Lo | Has logging/diagnostics |
| 10 | MF | Has multiple functions (2+) |
| 11 | DP | Has default parameter values |
| 12 | Bk | Code in fenced code block |

### Expected Results (verified March 18, 2026)

```
  Agent         Score  Hits  Gr    Fn Cl Ty Do Er CE Ed De Lo MF DP Bk
  --------------------------------------------------------------------
  coder         0.920  11/12 A   Y Y Y Y Y Y - Y Y Y Y Y
  tester        0.920  11/12 A   Y Y Y Y Y Y - Y Y Y Y Y
  reviewer      0.920  11/12 A   Y Y Y Y Y Y - Y Y Y Y Y
  planner       0.920  11/12 A   Y Y Y Y Y Y - Y Y Y Y Y
  researcher    0.920  11/12 A   Y Y Y Y Y Y - Y Y Y Y Y
  fileops       0.920  11/12 A   Y Y Y Y Y Y - Y Y Y Y Y
  devops        0.920  11/12 A   Y Y Y Y Y Y - Y Y Y Y Y
  --------------------------------------------------------------------
  ORCHESTRATED  1.000  12/12 A   Y Y Y Y Y Y Y Y Y Y Y Y

SUMMARY:
  Best individual agent:  0.920
  Average individual:     0.920
  Orchestrated system:    1.000
  Emergence ratio:        1.087x

  EMERGENCE DETECTED: Phi(S) > max(Phi(s_i))
  Emergent surplus: +0.080
```

**Key finding:** Every solo agent missed edge case handling. The pipeline's reviewer caught it, sent it back for revision, and the final output scored 12/12. Intelligence emerged from collaboration.

---

## 3. Document Similarity Engine (Ch 1)

Real-world NCD-based deduplication, plagiarism detection, and clustering. No ML models needed.

```bash
# Run the full demo
uv run python chapter-01/document_similarity.py

# Scan a specific directory for duplicates
uv run python chapter-01/document_similarity.py /path/to/scan
```

### What it demonstrates

- **Text deduplication:** Finds near-duplicate documents in a corpus
- **Code similarity:** Detects similar code files (rename detection)
- **Document clustering:** Groups related documents without embeddings
- **Repository self-scan:** Scans the repo itself for redundancy

### Real-world applications

- Deduplicate a training corpus before fine-tuning
- Find plagiarism without vector databases
- Detect copy-pasted code across a project
- Cluster related documentation automatically

---

## 4. RAG with Real Local Corpus (Ch 9)

Indexes the actual repository and answers questions about the codebase.

```bash
uv run python chapter-09/rag_local_corpus.py
```

### What it demonstrates

- **Real ingestion:** Reads all `.py` and `.md` files from the repo
- **TF-IDF indexing:** Builds a search index from scratch (no vector DB required)
- **4 retrieval strategies:**
  - `tfidf` — Term frequency, inverse document frequency
  - `keyword` — Simple keyword matching
  - `window` — Sentence window (expanded context around matches)
  - `fusion` — Merges TF-IDF + keyword results
- **Strategy comparison:** Same question across all 4 strategies with timing

### Sample questions it answers

- "How does agent routing work?"
- "What safety patterns block dangerous commands?"
- "How does the trust score decay over time?"
- "What RAG strategies are implemented?"

---

## 5. Interactive Trust Playground (Ch 12)

Play the role of the human-in-the-loop. Trust builds and decays in real-time.

```bash
uv run python chapter-12/trust_playground.py
```

### What it demonstrates

- **Exponential decay:** `trust(t) = trust_0 * e^(-0.05 * t)`
- **Real-time decisions:** Approve or deny 14 simulated agent actions
- **Trust visualization:** ASCII bar chart updates after each decision
- **Session summary:** Full audit trail of all decisions and trust changes

### The 14 actions (safe/caution/dangerous)

| Action | Risk Level |
|--------|------------|
| Read file: main.py | safe |
| Execute: python main.py | safe |
| Write file: utils.py | caution |
| Execute: pip install requests | caution |
| Execute: git push origin main | caution |
| Execute: rm -r build/ | caution |
| Write file: /etc/hosts | dangerous |
| Execute: sudo apt update | dangerous |
| Execute: git reset --hard | dangerous |

**Tip:** Wait a few seconds between decisions to see trust decay in action.

---

## 6. Live Scaffolder (Ch 17)

Generates projects AND proves they work by running the tests.

```bash
uv run python chapter-17/scaffolder_live.py
```

### What it demonstrates

- **Multi-language scaffolding:** Python, Rust, Go, TypeScript, Java
- **Auto-detection:** Checks which tools are installed (uv, cargo, go, pnpm, gradle)
- **End-to-end verification:** Creates project -> installs deps -> runs tests -> reports results
- **Summary table:** Pass/fail for each language

### Expected on this machine (Ubuntu 25.10)

| Language | Tool | Status |
|----------|------|--------|
| Python | uv | PASS (uv is installed) |
| Rust | cargo | Depends on rustup |
| Go | go | Depends on golang |
| TypeScript | pnpm | PASS (pnpm is installed) |
| Java | gradle | Depends on gradle |

---

## 7. Other Chapter Demos

### Information Theory (Ch 1)

```bash
uv run python chapter-01/shannon_entropy.py       # Entropy calculator
uv run python chapter-01/kolmogorov_complexity.py  # Compression-based complexity
uv run python chapter-01/intelligence_definitions.py  # 15 definitions analyzed
```

### Emergence Simulations (Ch 2)

```bash
uv run python chapter-02/emergence_simulation.py   # Boids flocking (classic)
uv run python chapter-02/phi_measure.py            # Formal Phi measurement
uv run python chapter-02/agent_coordination.py     # Decentralized coordination
```

### Agent Architecture (Ch 4-7)

```bash
uv run python chapter-04/first_agent.py            # Your first Ollama agent
uv run python chapter-04/multi_agent_demo.py       # 5 agents, same question
uv run python chapter-05/routing_demo.py           # Hierarchical routing
uv run python chapter-06/pool_demo.py              # Parallel agent pool
uv run python chapter-07/pipeline_demo.py          # Quality pipeline
uv run python chapter-07/feedback_loop.py          # Review feedback loop
```

### Knowledge Engine (Ch 8-10)

```bash
uv run python chapter-08/memory_demo.py            # Vector memory with Qdrant
uv run python chapter-09/naive_rag.py              # Basic RAG
uv run python chapter-09/fusion_rag.py             # Fusion RAG
uv run python chapter-09/rag_evaluation.py         # RAGAS metrics simulation
uv run python chapter-10/context_demo.py           # Rules + actions + repo map
```

### Safety and Ethics (Ch 11-14)

```bash
uv run python chapter-11/modes_demo.py             # Zap vs Careful modes
uv run python chapter-12/safety_demo.py            # 28 blocked patterns
uv run python chapter-12/trust_decay.py            # Trust decay visualization
uv run python chapter-13/events_demo.py            # Event bus
uv run python chapter-14/careful_demo.py           # Approval workflows
uv run python chapter-14/manifesto.py              # The 7 principles
```

### Systems (Ch 15-22)

```bash
uv run python chapter-15/local_first.py            # Local-first architecture check
uv run python chapter-16/dual_language.py          # Conceptual bridge patterns
uv run python chapter-17/scaffolder.py             # Basic scaffolder
uv run python chapter-18/session_demo.py           # Session-as-git provenance
uv run python chapter-19/tools_demo.py             # 7 tools demo
uv run python chapter-20/agent_kernel.py           # ZAPIX kernel concepts
uv run python chapter-23/emergence_thesis.py       # Emergence scaling
uv run python chapter-24/capstone.py               # Architecture summary
```

---

## 8. Running the Test Suite

```bash
# Full suite (305 tests)
uv run python -m pytest tests/ -v

# Specific modules
uv run python -m pytest tests/test_agent.py -v
uv run python -m pytest tests/test_safety.py -v
uv run python -m pytest tests/test_tools_web.py -v
uv run python -m pytest tests/test_emergence_scoring.py -v
uv run python -m pytest tests/test_document_similarity.py -v

# With coverage
uv run python -m pytest tests/ --tb=short -q
```

### Test file inventory (305 tests across 12 files)

| Test File | Tests | What it covers |
|-----------|-------|----------------|
| `test_agent.py` | Agent class, history, config |
| `test_router.py` | Keyword + LLM routing |
| `test_pool.py` | Parallel agent pools |
| `test_pipeline.py` | Quality pipeline stages |
| `test_context.py` | Rules parser, action tracker, repo map |
| `test_modes.py` | Zap/Careful execution modes |
| `test_safety.py` | 28 blocked patterns, trust scoring |
| `test_careful.py` | Approval workflows |
| `test_events.py` | Event bus, background agents |
| `test_session.py` | Session-as-git provenance |
| `test_tools.py` | Shell, file, registry |
| `test_tools_edit.py` | Find-replace, insert, delete |
| `test_tools_git.py` | Git operations |
| `test_tools_python.py` | Python code execution |
| `test_tools_search.py` | Grep, find, symbols |
| `test_tools_web.py` | Web search, URL fetch, HTML parsing |
| `test_ollama_utils.py` | Mock agent, Ollama detection |
| `test_document_similarity.py` | NCD, dedup, clustering |
| `test_emergence_scoring.py` | 12-dimension scoring engine |
| `test_integration.py` | Tool chains |
| `test_e2e.py` | End-to-end system |

---

## 9. Lint Check

```bash
uv run ruff check .
```

**Expected:** `All checks passed!`

---

## 10. Repository Stats

| Metric | Value |
|--------|-------|
| **Python files** | 89 |
| **Chapter examples** | 47 across 22 chapters |
| **LoopAGI modules** | 22 |
| **Tests** | 305 passing |
| **Agents** | 7 (coder, researcher, planner, tester, reviewer, fileops, devops) |
| **Tools** | 7 (shell, file, git, search, edit, python, web) |
| **CLI commands** | 20+ |
| **Blocked safety patterns** | 28 |
| **RAG strategies** | 4 (naive, sentence window, fusion, reranking) |
| **Scoring dimensions** | 12 (emergence demo) |
| **Lint errors** | 0 |

---

## Quick Start (5 Minutes)

```bash
cd /home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code

# 1. Run the capstone
uv run loopagi --model qwen3:8b

# 2. Inside the CLI, try:
#    Write a binary search function
#    /run rm -rf /
#    /trust
#    /pipeline Write an LRU cache class
#    /quit

# 3. Run the emergence proof
uv run python chapter-02/real_emergence_demo.py

# 4. Run all tests
uv run python -m pytest tests/ -q
```

---

*God in the Loop - Companion Code*
*Copyright 2026 Alexandros Karales. All Rights Reserved.*
