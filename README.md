# LoopAGI

**Open Source Multi-Agent AGI System**

> *The engineering manual for building intelligent agent systems.*
> *By Alexandros Karales*

**Website:** [loopagi.org](https://loopagi.org)
**Book:** *LoopAGI: The Engineering Manual* (Volume 2 of the AGI Book Series)
**Volume 1:** *God in the Loop* (philosophy + foundations)

---

## What is LoopAGI?

LoopAGI is a fully open source, local-first, multi-agent AI system that runs entirely on your machine. No API keys. No cloud. No data leaves your device.

**13 specialist agents** coordinate through hierarchical routing to handle coding, testing, reviewing, research, planning, file operations, DevOps, debugging, documentation, knowledge retrieval, memory management, voice input, and voice output.

### Agents

| # | Agent | Role |
|---|-------|------|
| 1 | **coder** | Write, debug, and refactor Python code |
| 2 | **tester** | Generate comprehensive pytest test suites |
| 3 | **reviewer** | Code review with quality scoring |
| 4 | **planner** | Architecture and implementation planning |
| 5 | **researcher** | Explain concepts, compare options |
| 6 | **fileops** | File management and project structure |
| 7 | **devops** | Git, CI/CD, Docker, deployment |
| 8 | **debugger** | Root cause analysis and bug fixing |
| 9 | **documenter** | Generate docs, READMEs, docstrings |
| 10 | **knowledge** | RAG-powered retrieval from project docs |
| 11 | **memory** | Long-term memory storage and recall |
| 12 | **listener** | Voice-to-text input (local STT) |
| 13 | **speaker** | Text-to-voice output (local TTS) |

### Tools

| Tool | Description |
|------|-------------|
| **shell** | Execute commands with safety checking |
| **file** | Read, write, list files |
| **edit** | Surgical find-and-replace editing |
| **git** | Full git workflow (status, diff, commit, branch) |
| **search** | Grep, find files, symbol search |
| **python** | Execute Python code and scripts |
| **web** | DuckDuckGo search, URL fetching |
| **voice_in** | Microphone capture + local STT |
| **voice_out** | Local TTS + audio playback |

---

## Requirements

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (Python package manager)
- **[Ollama](https://ollama.ai/)** (local LLM inference)
- **Git**
- **Optional:** Microphone (for voice input), speakers (for voice output)

## Quick Start

```bash
# Clone
git clone https://github.com/ZapAGI/loopagi.git
cd loopagi

# Install
uv sync

# Pull a model
ollama pull llama3.2

# Run
uv run loopagi
```

## Usage

```bash
# Default (llama3.2, zap mode)
uv run loopagi

# Specify model
uv run loopagi --model qwen3:8b

# Careful mode (every action requires approval)
uv run loopagi --mode careful

# Enable voice
uv run loopagi --voice

# Verbose logging
uv run loopagi --verbose
```

## Book

This repository is the companion code for **LoopAGI: The Engineering Manual** by Alexandros Karales.

The book is a pure engineering reference in the tradition of Knuth. No stories, no philosophy (that was Volume 1). Every chapter is code, algorithms, architecture, and implementation.

### The AGI Book Series

| Volume | Title | Focus |
|--------|-------|-------|
| 1 | *God in the Loop* | Philosophy + foundations + 7-agent capstone |
| **2** | ***LoopAGI*** | **Engineering manual + 13 agents + voice** |
| 3 | *Ragpedia* | Complete RAG encyclopedia (28 strategies) |
| 4 | *Drone AGI* | Autonomous drones, swarms, near-space flight |
| 5 | *ZAPIX* | AI-native operating system engineering |

---

## License

MIT License. Free to use, modify, and distribute.

Copyright 2026 Alexandros Karales.
