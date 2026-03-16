# LoopAGI: The Engineering Manual

## Building a 13-Agent AI System with Voice

### By Alexandros Karales

---

> **Volume 2 of the AGI Book Series**
> **Website:** loopagi.org | **License:** MIT | **Language:** Python
>
> This is a pure engineering reference. Every chapter is code, algorithms,
> architecture, and implementation. No stories, no philosophy. That was Volume 1.
>
> Volume 1 (God in the Loop) built a 7-agent system with basic tools.
> This volume upgrades it to 13 agents, adds voice I/O, and makes it
> production-ready.

---

## Part I: Foundation Upgrade (Chapters 1-4)

### Chapter 1: From 7 to 13 - The Agent Expansion

- Review of the Vol 1 architecture (7 agents, 7 tools)
- Why 13 agents: the specialization threshold
- The 6 new agents: debugger, documenter, knowledge, memory, listener, speaker
- Agent registry pattern: dynamic agent loading
- Configuration-driven agent creation
- **Code:** `loopagi/agents/registry.py`, agent config TOML format
- **Tests:** Agent registry unit tests

### Chapter 2: The Routing Engine Rewrite

- Limitations of keyword routing at scale
- Three-phase routing: keyword, embedding similarity, LLM classification
- Embedding-based route classification with fastembed
- Confidence thresholds and fallback chains
- Route caching for repeated patterns
- **Code:** `loopagi/routing/engine.py`, `loopagi/routing/embeddings.py`
- **Benchmarks:** Routing accuracy vs latency across all 13 agents
- **Tests:** Route decision tests with 100+ example queries

### Chapter 3: The Agent Protocol

- Standardized agent interface: `invoke()`, `stream()`, `reset()`, `tools()`
- Agent lifecycle: init, warm, active, cooldown, terminate
- Agent state serialization for session persistence
- Inter-agent message format (typed dataclasses)
- **Code:** `loopagi/agents/protocol.py`, `loopagi/agents/lifecycle.py`
- **Tests:** Protocol conformance tests

### Chapter 4: Configuration and Project Setup

- TOML-based configuration system
- Per-project `.loopagi.toml` files
- Global config at `~/.config/loopagi/config.toml`
- Environment variable overrides
- Model selection per agent role
- **Code:** `loopagi/config.py`, default config template
- **Tests:** Config loading, merging, validation

---

## Part II: The Specialist Agents (Chapters 5-10)

### Chapter 5: The Debugger Agent

- Error classification: syntax, runtime, logic, import, type
- Stack trace parsing and root cause analysis
- Automated fix suggestion pipeline
- Integration with Python traceback module
- Bisection debugging strategy
- **Code:** `loopagi/agents/debugger.py`
- **Tests:** Error classification tests, fix suggestion tests

### Chapter 6: The Documenter Agent

- Docstring generation from function signatures
- README generation from project structure
- API documentation extraction
- Changelog generation from git log
- Type stub generation
- **Code:** `loopagi/agents/documenter.py`
- **Tests:** Docstring quality tests, README generation tests

### Chapter 7: The Knowledge Agent

- RAG pipeline integration (from Vol 1 `rag.py`)
- Project document ingestion (markdown, Python, text)
- Semantic search across project knowledge base
- Context window management: what to include, what to drop
- Incremental re-indexing on file changes
- **Code:** `loopagi/agents/knowledge.py`, `loopagi/knowledge/indexer.py`
- **Tests:** Ingestion tests, retrieval accuracy tests

### Chapter 8: The Memory Agent

- Long-term memory architecture (from Vol 1 `memory.py`)
- Significance detection: what is worth remembering
- Memory categories: preferences, decisions, patterns, facts
- Memory decay and reinforcement
- Cross-session memory persistence
- **Code:** `loopagi/agents/memory_agent.py`, `loopagi/memory/store.py`
- **Tests:** Memory CRUD tests, significance scoring tests

### Chapter 9: The Quality Pipeline Upgrade

- Upgraded planner, coder, tester, reviewer pipeline
- Parallel test generation with agent pools
- Review scoring rubric (1-10 with categories)
- Iteration budget and early termination
- Pipeline metrics and reporting
- **Code:** `loopagi/pipeline/quality.py`, `loopagi/pipeline/metrics.py`
- **Tests:** Pipeline integration tests

### Chapter 10: The DevOps and FileOps Agents

- Git workflow automation (feature branch, commit, PR description)
- Project scaffolding for 5 languages
- File organization heuristics
- Dependency analysis and update checking
- **Code:** `loopagi/agents/devops.py`, `loopagi/agents/fileops.py`
- **Tests:** Git operation tests, scaffolding tests

---

## Part III: Voice Integration (Chapters 11-14)

### Chapter 11: Speech-to-Text with faster-whisper

- Local STT architecture (no cloud, no API keys)
- faster-whisper setup: distil-large-v3 model
- Microphone capture with sounddevice
- Voice Activity Detection (VAD) for automatic segmentation
- Streaming transcription pipeline
- **Code:** `loopagi/voice/stt.py`, `loopagi/voice/microphone.py`
- **Tests:** Transcription accuracy tests with sample audio

### Chapter 12: Text-to-Speech with piper-tts

- Local TTS architecture
- piper-tts setup: voice model selection
- Audio output with sounddevice/soundfile
- Chunked synthesis for streaming playback
- Voice selection and configuration
- **Code:** `loopagi/voice/tts.py`, `loopagi/voice/speaker.py`
- **Tests:** TTS output validation tests

### Chapter 13: The Listener and Speaker Agents

- Listener agent: microphone to agent routing
- Speaker agent: agent response to audio output
- Voice command parsing: "/voice on", "/voice off"
- Wake word detection (optional, simple energy-based)
- Conversation flow: voice in, text processing, voice out
- **Code:** `loopagi/agents/listener.py`, `loopagi/agents/speaker.py`
- **Tests:** Voice agent integration tests (mocked audio)

### Chapter 14: The Voice-Enabled CLI

- Integrating voice into the LoopAGI CLI
- --voice flag and runtime toggle
- Audio feedback: confirmation tones, error sounds
- Hands-free operation mode
- Accessibility considerations
- **Code:** `loopagi/cli.py` voice integration
- **Tests:** CLI voice mode tests

---

## Part IV: Production Engineering (Chapters 15-18)

### Chapter 15: The Tool System Architecture

- Tool registry with capability discovery
- Tool result types and error propagation
- Tool composition: chaining tool calls
- Tool authorization levels (safe, caution, blocked)
- Creating custom tools
- **Code:** `loopagi/tools/registry.py`, `loopagi/tools/base.py`
- **Tests:** Tool registry tests, custom tool tests

### Chapter 16: The Event System

- Event bus architecture for background agents
- Event types and subscription patterns
- Background monitoring: file watcher, health check
- Event-driven agent activation
- Async event processing
- **Code:** `loopagi/events/bus.py`, `loopagi/events/handlers.py`
- **Tests:** Event routing tests, background agent tests

### Chapter 17: Session Management and Provenance

- Session-as-git: every action is a commit
- Session artifacts: HISTORY.md, COMMANDS.md, FILES.md, PROGRESS.md
- Session resume across restarts
- Session export and sharing
- Conversation archival
- **Code:** `loopagi/session/logger.py`, `loopagi/session/resume.py`
- **Tests:** Session lifecycle tests, artifact generation tests

### Chapter 18: Testing, Benchmarks, and CI

- Testing strategy for multi-agent systems
- Unit tests, integration tests, agent behavior tests
- Benchmark suite: routing latency, agent response time, tool throughput
- CI pipeline with GitHub Actions
- Coverage and quality gates
- **Code:** `tests/`, `.github/workflows/ci.yml`
- **Benchmarks:** `benchmarks/`

---

## Appendices

### Appendix A: Complete API Reference

- All 13 agent classes with parameters and methods
- All 9 tool classes with actions and options
- CLI command reference
- Configuration reference

### Appendix B: Model Recommendations

- Ollama model comparison by agent role
- VRAM requirements by model size
- Quality vs speed trade-offs
- Multi-model configuration examples

### Appendix C: Troubleshooting

- Common installation issues
- Ollama connection problems
- Voice setup on Linux, macOS, Windows
- Memory and performance tuning

---

## Estimated Scope

| Part | Chapters | Focus |
|------|----------|-------|
| Part I | 4 | Foundation upgrade, routing, protocol, config |
| Part II | 6 | Specialist agents (debugger, documenter, knowledge, memory, pipeline, devops) |
| Part III | 4 | Voice (STT, TTS, listener/speaker agents, CLI integration) |
| Part IV | 4 | Production (tools, events, sessions, testing) |
| Appendices | 3 | Reference, models, troubleshooting |
| **Total** | **21** | **Pure engineering, every chapter has code + tests** |

---

*LoopAGI: The Engineering Manual - Copyright 2026 Alexandros Karales. MIT License.*
