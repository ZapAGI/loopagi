# God in the Loop - Companion Code

**Working Python code for every chapter of *God in the Loop: Consciousness, Control, and the Architecture of Artificial General Intelligence* by Alexandros Karales.**

> **Branch: `book/v1-7-agents`** — 7-agent tutorial capstone (frozen for Volume 1).
> For the full 13-agent system with voice I/O, see branch `book/v2-13-agents`.

---

## The Capstone: LoopAGI (7 Agents)

Across 22 chapters, you progressively build **LoopAGI**, a fully functional multi-agent system. Each chapter contributes a real component:

- **7 specialist agents** with keyword-based routing (Ch 4-5)
- **Agent pools** for parallel execution (Ch 6)
- **Quality pipeline**: plan, code, test, review (Ch 7)
- **Persistent memory** with vector search (Ch 8)
- **RAG-powered knowledge retrieval** with 12 strategies (Ch 9)
- **Context engine** with rules, action tracking, and repo mapping (Ch 10)
- **Human-in-the-loop** execution modes (Ch 11)
- **Command safety** and trust scoring (Ch 12)
- **Event-driven background agents** (Ch 13)
- **Careful mode** with approval workflows (Ch 14)
- **Session-as-git** provenance logging (Ch 18)
- **Tool integration**: shell, files, git, search, web (Ch 19)
- **ARC-AGI** reasoning engine with 5 specialist agents (Ch 21)

### The 7 Agents

| Agent | Role | Keywords |
|-------|------|----------|
| **coder** | Python coding specialist | write, code, implement, function, class |
| **tester** | Test writing specialist | test, assert, coverage, pytest, verify |
| **reviewer** | Code review specialist | review, critique, improve, quality |
| **planner** | Architecture and planning | plan, design, architect, outline |
| **researcher** | Research and explanation | research, explain, compare, analyze |
| **fileops** | File operations | file, directory, move, copy, rename |
| **devops** | Git, CI/CD, infrastructure | git, commit, deploy, docker, ci |

### Progressive Build Map

| Chapter | LoopAGI Module | What You Build |
|---------|---------------|----------------|
| 4 | `loopagi/core/agent.py` | Base Agent class with Ollama LLM |
| 5 | `loopagi/core/router.py` | Hierarchical routing (Master → Workers) |
| 6 | `loopagi/core/pool.py` | Agent pools for parallel execution |
| 7 | `loopagi/core/pipeline.py` | Quality pipeline (plan/code/test/review) |
| 8 | `loopagi/knowledge/memory.py` | Persistent memory with Qdrant vectors |
| 9 | `loopagi/knowledge/rag.py` | RAG-powered knowledge retrieval |
| 10 | `loopagi/knowledge/context.py` | Context engine (rules, actions, repo map) |
| 11 | `loopagi/safety/modes.py` | Execution modes (Turbo/Careful) |
| 12 | `loopagi/safety/checker.py` | Command safety checker and trust scoring |
| 13 | `loopagi/core/events.py` | Event bus and background agents |
| 14 | `loopagi/safety/careful.py` | Careful mode approval workflows |
| 18 | `loopagi/core/session.py` | Session-as-git provenance logging |
| 19 | `loopagi/tools/base.py` | Tool integration (shell, file, registry) |
| 21 | `loopagi/arc/` | ARC-AGI reasoning engine (5 specialists) |
| 22 | `loopagi/cli.py` | Final CLI that assembles everything |

---

## Requirements

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (Python package manager)
- **[Ollama](https://ollama.ai/)** (local LLM inference)
- **Git**
- **GPU** (recommended): NVIDIA RTX 5080 or similar for fast Ollama inference

All code runs locally. No API keys required. No data leaves your machine.
Ollama automatically uses your GPU for inference — no configuration needed.

## Setup

```bash
# Clone the repo and switch to the 7-agent branch
git clone git@github.com:ZapAGI/loopagi.git
cd loopagi
git checkout book/v1-7-agents

# Install dependencies
uv sync

# Install dev dependencies (pytest, ruff)
uv sync --extra dev

# Pull the default Ollama model
ollama pull llama3.2

# (Optional) Pull additional models for better performance
ollama pull qwen3:8b
ollama pull qwen2.5-coder:14b
ollama pull nomic-embed-text
```

## Running Examples

Each chapter has its own directory with self-contained scripts:

```bash
# Run a chapter example
uv run python chapter-04/first_agent.py

# Run a Jupyter notebook (install optional deps first)
uv sync --extra notebooks
uv run jupyter lab
```

## Running the Capstone

```bash
# Interactive CLI (7 agents, keyword routing)
uv run loopagi

# Specify a model (any Ollama model)
uv run loopagi --model qwen3:8b

# Careful mode (requires approval for tool actions)
uv run loopagi --mode careful

# Verbose logging (see routing decisions, agent invocations)
uv run loopagi --verbose
```

## Running Tests

```bash
# Run all tests (1200+ tests)
uv run python -m pytest tests/ --ignore=tests/test_eval_improved.py -v

# Run just the core capstone tests
uv run python -m pytest tests/test_agent.py tests/test_router.py tests/test_tools.py -v

# Run with short output
uv run python -m pytest tests/ --ignore=tests/test_eval_improved.py -q
```

## GPU Notes (NVIDIA RTX 5080)

Ollama handles GPU allocation automatically. Verify GPU is being used:

```bash
# Check Ollama is using your GPU
nvidia-smi   # Should show ollama_llama_server using GPU memory
ollama list   # Shows available models
```

For 16GB VRAM (RTX 5080), recommended model sizes:
- **14b models** (qwen2.5-coder:14b, qwen3:14b): ~9GB VRAM, fits comfortably
- **8b models** (qwen3:8b): ~5GB VRAM, fastest inference
- **2b models** (llama3.2): ~2GB VRAM, good for testing

---

## Repository Structure

```
god-in-the-loop-code/
  loopagi/                  # Capstone MVP - built progressively across chapters
    __init__.py
    cli.py                  # Ch 23: Final CLI assembly
    core/                   # Agent infrastructure
      agent.py              # Ch 4:  Base Agent with Ollama
      router.py             # Ch 5:  Hierarchical routing
      pool.py               # Ch 6:  Agent pools
      pipeline.py           # Ch 7:  Quality pipeline
      events.py             # Ch 13: Event bus & background agents
      session.py            # Ch 18: Session-as-git provenance
      ollama_utils.py       # Ollama helpers & mock agents
    knowledge/              # Memory, RAG, and context
      memory.py             # Ch 8:  Persistent vector memory
      rag.py                # Ch 9:  RAG retrieval
      context.py            # Ch 10: Context engine
    safety/                 # Command safety & execution modes
      modes.py              # Ch 11: Execution modes (Zap/Careful)
      checker.py            # Ch 12: Command safety & trust scoring
      careful.py            # Ch 14: Careful mode approval workflows
    tools/                  # Tool integration
      base.py               # Ch 19: Shell, file, registry
      edit.py               # File editing tool
      git.py                # Git operations tool
      python.py             # Python execution tool
      search.py             # Code search tool
      web.py                # Web search tool
    arc/                    # ARC-AGI challenge modules

  chapter-01/               # Information theory: Shannon entropy, Kolmogorov complexity
  chapter-02/               # Emergence simulation, multi-agent coordination
  chapter-03/               # Kardashev scale, philosophical frameworks
  chapter-04/               # First agent: single Ollama-powered agent
  chapter-05/               # Hierarchy: Master to Worker routing
  chapter-06/               # Agent pools: parallel execution
  chapter-07/               # Quality pipeline: plan/code/test/review chain
  chapter-08/               # Memory: vector store, session persistence
  chapter-09/               # Ragonomics: 12 RAG strategies with evaluation
  chapter-10/               # Context engine: rules, actions, repo map
  chapter-11/               # God in the loop: execution mode demo
  chapter-12/               # Trust: safety patterns, confidence decay
  chapter-13/               # Ethics: event-driven background agents
  chapter-14/               # Careful mode: approval workflow patterns
  chapter-15/               # Innovation: local-first architecture
  chapter-16/               # Dual-language: Arrow Flight gRPC client
  chapter-17/               # Scaffolding: project generation for 5 languages
  chapter-18/               # Session-as-git: provenance logging
  chapter-19/               # Docker agent: service orchestration
  chapter-20/               # ZAPIX: agent kernel concepts
  chapter-21/               # ARC Challenge: overview (see chapter-22/ for code)
  chapter-22/               # Building the Reasoning Engine: ARC solver code
  chapter-23/               # Emergence thesis: complexity simulations
  chapter-24/               # Capstone assembly: the complete LoopAGI

  tests/                    # 1200+ tests for all capstone modules
  pyproject.toml
  README.md
```

---

## Chapter-by-Chapter Guide

### Part I: The Problem with Intelligence

**Chapter 1** - Information theory foundations. Shannon entropy calculator, Kolmogorov complexity estimator, intelligence definition comparison.

**Chapter 2** - Emergence simulation. Watch simple agents produce emergent behavior. Multi-agent coordination without a central controller.

**Chapter 3** - Kardashev scale visualization. Philosophical framework diagrams. The 2035 scenario model.

### Part II: The Architecture of Minds

**Chapter 4** - Build your first agent. A single Ollama-powered specialist that can answer questions and use tools. This becomes `loopagi/core/agent.py`.

**Chapter 5** - Add hierarchical routing. A Master agent routes tasks to specialist Workers. This becomes `loopagi/core/router.py`.

**Chapter 6** - Add agent pools. Run multiple instances of the same agent in parallel. This becomes `loopagi/core/pool.py`.

**Chapter 7** - Build the quality pipeline. Chain planner, coder, tester, and reviewer agents. This becomes `loopagi/core/pipeline.py`.

**Chapter 8** - Add persistent memory. Vector-based memory storage with Qdrant. Session resume. This becomes `loopagi/knowledge/memory.py`.

### Part III: The Knowledge Engine

**Chapter 9** - Ragonomics. Implement 12 RAG strategies from Naive to Adaptive. Evaluation with RAGAS metrics. Decision matrix tool. This becomes `loopagi/knowledge/rag.py`.

**Chapter 10** - Build the context engine. Rules parser, action tracker, code indexer, repository map. This becomes `loopagi/knowledge/context.py`.

### Part IV: The Human in the Loop

**Chapter 11** - Implement execution modes. Zap (autonomous) vs. Careful (approval required). This becomes `loopagi/safety/modes.py`.

**Chapter 12** - Build the safety layer. 28 blocked command patterns, confidence decay scoring, trust functions. This becomes `loopagi/safety/checker.py`.

**Chapter 13** - Event-driven architecture. Background agents that monitor, scan, and respond to events. This becomes `loopagi/core/events.py`.

**Chapter 14** - Careful mode implementation. Approval workflows, friction-by-design, the manifesto in code. This becomes `loopagi/safety/careful.py`.

### Part V: The Machine That Builds Itself

**Chapter 15** - Local-first patterns. Architecture decisions for privacy-preserving AI.

**Chapter 16** - Dual-language architecture. Why AGI needs both a systems language and Python. Bridge patterns (conceptual).

**Chapter 17** - Project scaffolding. Generate project structures for Python, Rust, Go, TypeScript, and Java.

**Chapter 18** - Session-as-git. Every interaction becomes a git commit. Automatic HISTORY.md, PROGRESS.md generation. This becomes `loopagi/core/session.py`.

**Chapter 19** - Docker agent patterns. Service orchestration, health checks, container management. This becomes `loopagi/tools/base.py`.

### Part VI: The Future We're Building

**Chapter 20** - ZAPIX concepts. Agent kernel architecture, intent-based interaction patterns.

**Chapter 21** - The ARC Challenge. Build a multi-agent reasoning engine for abstract visual puzzles. Five specialist agents (Perceiver, Hypothesizer, Synthesizer, Evaluator, Refiner). This becomes `loopagi/arc/`.

**Chapter 22** - Emergence simulations. Measure emergence formally. Complexity thresholds and phase transitions.

**Chapter 23** - Capstone assembly. Wire everything together into the complete LoopAGI CLI. The cursor blinks.

---

## License

This companion repository is provided exclusively to purchasers of *God in the Loop*.
Do not redistribute.

Copyright 2026 Alexandros Karales. All Rights Reserved.
