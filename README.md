# God in the Loop - Companion Code

**Working Python code for every chapter of *God in the Loop: Consciousness, Control, and the Architecture of Artificial General Intelligence* by Alexandros Karales.**

---

## The Capstone: LoopAGI

This repository is not just a collection of isolated examples. Across 22 chapters, you progressively build **LoopAGI**, a fully functional mini multi-agent AGI system. Each chapter contributes a real component. By the end, you have a working system with:

- **Multi-agent orchestration** with hierarchical routing (Ch 4-5)
- **Agent pools** for parallel execution (Ch 6)
- **Quality pipeline**: plan, code, test, review (Ch 7)
- **Persistent memory** with vector search (Ch 8)
- **RAG-powered knowledge retrieval** (Ch 9)
- **Context engine** with rules, action tracking, and repo mapping (Ch 10)
- **Human-in-the-loop** execution modes (Ch 11)
- **Command safety** and trust scoring (Ch 12)
- **Event-driven background agents** (Ch 13)
- **Careful mode** with approval workflows (Ch 14)
- **Session-as-git** provenance logging (Ch 18)
- **Tool integration**: shell, files, Docker (Ch 19)

### Progressive Build Map

| Chapter | LoopAGI Module | What You Build |
|---------|---------------|----------------|
| 4 | `loopagi/agent.py` | Base Agent class with Ollama LLM |
| 5 | `loopagi/router.py` | Hierarchical routing (Master to Workers) |
| 6 | `loopagi/pool.py` | Agent pools for parallel execution |
| 7 | `loopagi/pipeline.py` | Quality pipeline (plan/code/test/review) |
| 8 | `loopagi/memory.py` | Persistent memory with Qdrant vectors |
| 9 | `loopagi/rag.py` | RAG-powered knowledge retrieval |
| 10 | `loopagi/context.py` | Context engine (rules, actions, repo map) |
| 11 | `loopagi/modes.py` | Execution modes (Zap/Careful) |
| 12 | `loopagi/safety.py` | Command safety checker and trust scoring |
| 13 | `loopagi/events.py` | Event bus and background agents |
| 14 | `loopagi/careful.py` | Careful mode approval workflows |
| 18 | `loopagi/session.py` | Session-as-git provenance logging |
| 19 | `loopagi/tools.py` | Tool integration (shell, files, Docker) |
| 21 | `loopagi/arc/` | ARC-AGI reasoning engine (5 specialists) |
| 22 | `loopagi/cli.py` | Emergence thesis simulations |
| 23 | `loopagi/cli.py` | Final CLI that assembles everything |

---

## Requirements

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (Python package manager)
- **[Ollama](https://ollama.ai/)** (local LLM inference)
- **Git**

All code runs locally. No API keys required. No data leaves your machine.

## Setup

```bash
# Clone the companion repo
git clone git@github.com:ZapAGI/god-in-the-loop-code.git
cd god-in-the-loop-code

# Install dependencies
uv sync

# Pull required Ollama models
ollama pull llama3.2
ollama pull nomic-embed-text
```

## Running Examples

Each chapter has its own directory with a `README.md` and self-contained scripts:

```bash
# Run a chapter example
uv run python chapter-01/shannon_entropy.py

# Run a Jupyter notebook (install optional deps first)
uv sync --extra notebooks
uv run jupyter lab
```

## Running the Capstone

After completing all chapters, run the full LoopAGI system:

```bash
# Interactive CLI
uv run loopagi

# Or run directly
uv run python -m loopagi.cli
```

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

  tests/                    # 582 tests for all capstone modules
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
