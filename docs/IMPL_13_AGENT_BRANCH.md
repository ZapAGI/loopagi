# LoopAGI 13-Agent Branch Implementation Guide

**Branch:** `book/v2-13-agents`
**Base:** `book/v1-7-agents` (working 7-agent system)
**Target:** Full 13-agent system with voice I/O for Volume 2

---

## Current State

### What Exists (7-agent branch)

| Module | File | Status |
|--------|------|--------|
| Base Agent | `loopagi/core/agent.py` | Working |
| Router (keyword + LLM) | `loopagi/core/router.py` | Working (7 agents) |
| Agent Pools | `loopagi/core/pool.py` | Working |
| Quality Pipeline | `loopagi/core/pipeline.py` | Working (plan/code/test/review) |
| Event Bus | `loopagi/core/events.py` | Working |
| Session-as-Git | `loopagi/core/session.py` | Working |
| Vector Memory | `loopagi/knowledge/memory.py` | Working (Qdrant) |
| RAG Engine | `loopagi/knowledge/rag.py` | Working (4 strategies) |
| Context Engine | `loopagi/knowledge/context.py` | Working |
| Safety Checker | `loopagi/safety/checker.py` | Working |
| Execution Modes | `loopagi/safety/modes.py` | Working (Zap/Careful) |
| Careful Mode | `loopagi/safety/careful.py` | Working |
| Shell Tool | `loopagi/tools/base.py` | Working |
| File Tool | `loopagi/tools/base.py` | Working |
| Edit Tool | `loopagi/tools/edit.py` | Working |
| Git Tool | `loopagi/tools/git.py` | Working |
| Python Tool | `loopagi/tools/python.py` | Working |
| Search Tool | `loopagi/tools/search.py` | Working |
| Web Tool | `loopagi/tools/web.py` | Working |
| CLI | `loopagi/cli.py` | Working |
| ARC Solver | `loopagi/arc/` | Working (45 modules) |
| Tests | `tests/` | 57 test files |

### 7 Existing Agents (from `cli.py::_create_agents`)

1. **coder** - Python coding specialist
2. **researcher** - Concept explanation, comparisons
3. **planner** - Architecture and implementation planning
4. **tester** - Pytest test suite generation
5. **reviewer** - Code review with quality scoring
6. **fileops** - File management and project structure
7. **devops** - Git, CI/CD, Docker, deployment

### 6 New Agents to Implement

8. **debugger** - Root cause analysis and bug fixing
9. **documenter** - Generate docs, READMEs, docstrings
10. **knowledge** - RAG-powered retrieval from project docs
11. **memory** - Long-term memory storage and recall
12. **listener** - Voice-to-text input (local STT)
13. **speaker** - Text-to-voice output (local TTS)

---

## Phase 1: New Agent Definitions

**Goal:** Add 4 text-based agents (debugger, documenter, knowledge, memory)
**Estimated effort:** 1 session

### 1.1 Create Agent Module Files

Create `loopagi/agents/` with individual agent files:

```
loopagi/agents/
    __init__.py
    debugger.py
    documenter.py
    knowledge_agent.py
    memory_agent.py
```

Each agent file should define:
- Agent name, role prompt, default model
- Specialized tool bindings
- Custom response formatting (if needed)

### 1.2 Agent Specifications

#### debugger (`loopagi/agents/debugger.py`)
- **Role:** Root cause analysis. Read error messages, tracebacks, logs. Identify the bug. Propose minimal fix.
- **Model:** `qwen2.5-coder:14b` (needs code understanding)
- **Tools:** `shell_exec`, `read_file`, `search_codebase`, `python_exec`
- **Keywords:** `debug`, `error`, `traceback`, `exception`, `bug`, `crash`, `fail`, `broken`, `stack trace`, `segfault`, `not working`, `wrong output`

#### documenter (`loopagi/agents/documenter.py`)
- **Role:** Generate documentation. READMEs, docstrings, API docs, changelogs, inline comments.
- **Model:** `qwen3:14b` (needs good prose)
- **Tools:** `read_file`, `write_file`, `search_codebase`
- **Keywords:** `document`, `readme`, `docstring`, `changelog`, `comment`, `explain code`, `api doc`, `type hint`, `annotate`, `describe`

#### knowledge (`loopagi/agents/knowledge_agent.py`)
- **Role:** RAG-powered retrieval. Ingest project docs, search knowledge base, answer questions from indexed content.
- **Model:** `qwen3:8b`
- **Tools:** Wraps `loopagi/knowledge/rag.py` (RAGEngine)
- **Keywords:** `knowledge`, `search docs`, `what does`, `find in docs`, `look up`, `index`, `ingest`
- **Integration:** Uses existing `RAGEngine` class, exposes `ingest()` and `query()` as agent actions

#### memory (`loopagi/agents/memory_agent.py`)
- **Role:** Long-term memory. Store facts, preferences, project context. Recall relevant memories for other agents.
- **Model:** `qwen3:8b`
- **Tools:** Wraps `loopagi/knowledge/memory.py` (MemoryStore)
- **Keywords:** `remember`, `recall`, `memory`, `forget`, `what did`, `last time`, `history`, `store`, `save note`
- **Integration:** Uses existing `MemoryStore` class, exposes `add()` and `search()` as agent actions

### 1.3 Update Router

File: `loopagi/core/router.py`

Add keyword patterns for 4 new agents to `ROUTING_PATTERNS` dict:

```python
"debugger": [
    "debug", "error", "traceback", "exception", "bug", "crash",
    "fail", "broken", "stack trace", "not working", "wrong output",
],
"documenter": [
    "document", "readme", "docstring", "changelog", "comment",
    "explain code", "api doc", "type hint", "annotate", "describe",
],
"knowledge": [
    "knowledge", "search docs", "what does", "find in docs",
    "look up", "index", "ingest", "documentation",
],
"memory": [
    "remember", "recall", "memory", "forget", "what did",
    "last time", "history", "store", "save note",
],
```

### 1.4 Update CLI

File: `loopagi/cli.py` (`_create_agents` method)

Add 4 new Agent instances with their role prompts and model assignments.

### 1.5 Tests

Create test files:
- `tests/test_debugger.py`
- `tests/test_documenter.py`
- `tests/test_knowledge_agent.py`
- `tests/test_memory_agent.py`

Each test file should cover:
- Agent initialization
- Keyword routing hits the correct agent
- Agent produces valid output format
- Tool integration (mock Ollama responses)

### 1.6 Verification

```bash
# Run all tests
uv run pytest tests/ -v

# Test routing to new agents
uv run python -c "
from loopagi.core.agent import Agent
from loopagi.core.router import Router, ROUTING_PATTERNS
print('Routing patterns:', list(ROUTING_PATTERNS.keys()))
assert len(ROUTING_PATTERNS) == 11  # 7 + 4 new
print('All 11 routing patterns present')
"

# Test agent creation
uv run python -c "
from loopagi.cli import LoopAGI
app = LoopAGI.__new__(LoopAGI)
agents = app._create_agents('llama3.2')
print(f'{len(agents)} agents created')
for a in agents:
    print(f'  - {a.name}')
assert len(agents) == 11  # 7 + 4 new
"
```

---

## Phase 2: Voice Agents

**Goal:** Add listener (STT) and speaker (TTS) agents
**Estimated effort:** 1-2 sessions
**Dependencies:** `faster-whisper`, `piper-tts`, `sounddevice`, `soundfile`

### 2.1 Voice Tools

Create voice tool modules:

```
loopagi/voice/
    __init__.py
    listener.py     # Microphone capture + STT (faster-whisper)
    speaker.py      # TTS + audio playback (piper-tts)
```

#### listener.py
- Capture audio from microphone via `sounddevice`
- Transcribe with `faster-whisper` (local, no API)
- Model: `base.en` or `small.en` (auto-downloaded)
- Output: transcribed text string
- Must handle: no microphone, silence detection, interrupt

```python
class Listener:
    def __init__(self, model_size: str = "base.en"):
        self.whisper = WhisperModel(model_size, device="cpu", compute_type="int8")

    def listen(self, duration: float = 5.0) -> str:
        """Record audio and transcribe."""
        audio = self._record(duration)
        segments, _ = self.whisper.transcribe(audio)
        return " ".join(s.text for s in segments).strip()
```

#### speaker.py
- Synthesize speech with `piper-tts` (local, no API)
- Play audio via `sounddevice`
- Voice: `en_US-lessac-medium` (auto-downloaded)
- Must handle: no speakers, interrupt, queue

```python
class Speaker:
    def __init__(self, voice: str = "en_US-lessac-medium"):
        self.voice = PiperVoice.load(voice)

    def speak(self, text: str) -> None:
        """Convert text to speech and play."""
        audio = self.voice.synthesize(text)
        sounddevice.play(audio, samplerate=22050)
        sounddevice.wait()
```

### 2.2 Voice Agent Definitions

#### listener (`loopagi/agents/listener.py`)
- **Role:** Voice-to-text input. Activate microphone, transcribe, pass text to router.
- **Model:** N/A (uses faster-whisper, not an LLM)
- **Integration:** Wraps `loopagi/voice/listener.py`, feeds transcribed text back to CLI input loop
- **Keywords:** `listen`, `voice`, `microphone`, `speak to me`, `hear`

#### speaker (`loopagi/agents/speaker.py`)
- **Role:** Text-to-voice output. Read agent responses aloud.
- **Model:** N/A (uses piper-tts, not an LLM)
- **Integration:** Wraps `loopagi/voice/speaker.py`, reads from agent output
- **Keywords:** `say`, `read aloud`, `speak`, `voice output`, `tts`

### 2.3 CLI Voice Mode

Update `loopagi/cli.py`:
- Add `--voice` flag
- When enabled: listener captures input, speaker reads output
- Fallback to text I/O if voice dependencies not installed

```python
# In CLI main loop
if self.voice_mode:
    user_input = self.listener.listen()
    console.print(f"[dim]You said:[/dim] {user_input}")
else:
    user_input = console.input("[bold green]> [/bold green]")
```

### 2.4 Tests

- `tests/test_listener.py` - Mock microphone, test transcription pipeline
- `tests/test_speaker.py` - Mock audio output, test synthesis pipeline
- `tests/test_voice_integration.py` - End-to-end voice mode (mocked hardware)

### 2.5 Verification

```bash
# Install voice dependencies
uv sync --extra voice

# Test listener (requires microphone)
uv run python -c "
from loopagi.voice.listener import Listener
l = Listener()
print('Listener initialized, model loaded')
# l.listen(3.0)  # Uncomment to test with real mic
"

# Test speaker (requires speakers)
uv run python -c "
from loopagi.voice.speaker import Speaker
s = Speaker()
s.speak('LoopAGI voice test successful')
"

# Test voice CLI mode
uv run loopagi --voice
```

---

## Phase 3: Infrastructure Upgrades

**Goal:** 3-phase routing, TOML config, per-agent model config
**Estimated effort:** 1-2 sessions

### 3.1 TOML Configuration System

Create `loopagi/core/config.py`:

```python
@dataclass
class LoopAGIConfig:
    """Global configuration loaded from loopagi.toml."""
    model: str = "llama3.2"
    mode: str = "zap"
    voice: bool = False
    agents: dict[str, AgentConfig] = field(default_factory=dict)
    routing: RoutingConfig = field(default_factory=RoutingConfig)
```

Create `loopagi.toml.example`:

```toml
[loopagi]
model = "llama3.2"
mode = "zap"
voice = false

[agents.coder]
model = "qwen2.5-coder:14b"
temperature = 0.3

[agents.researcher]
model = "qwen3:14b"
temperature = 0.7

[agents.planner]
model = "qwen3:14b"
temperature = 0.5

[routing]
keyword_threshold = 0.3
embedding_model = "all-MiniLM-L6-v2"
embedding_threshold = 0.7
```

### 3.2 Three-Phase Routing

Upgrade `loopagi/core/router.py`:

| Phase | Method | Speed | When |
|-------|--------|-------|------|
| 1 | Keyword matching | <1ms | 80%+ of requests |
| 2 | Embedding similarity | ~10ms | Ambiguous keywords |
| 3 | LLM classification | ~500ms | Complex/novel requests |

Add embedding-based routing between keyword and LLM phases:

```python
from fastembed import TextEmbedding

class Router:
    def __init__(self, agents, embedding_model="all-MiniLM-L6-v2"):
        self.embedder = TextEmbedding(model_name=embedding_model)
        self._build_agent_embeddings()

    def _build_agent_embeddings(self):
        """Pre-compute embeddings for agent role descriptions."""
        for name, agent in self.agents.items():
            self.agent_embeddings[name] = self.embedder.embed([agent.role])

    def _embedding_route(self, task: str) -> RouteDecision | None:
        """Phase 2: Embedding similarity routing."""
        task_embedding = self.embedder.embed([task])
        scores = {
            name: cosine_similarity(task_embedding, emb)
            for name, emb in self.agent_embeddings.items()
        }
        best = max(scores, key=lambda k: scores[k])
        if scores[best] >= self.embedding_threshold:
            return RouteDecision(agent_name=best, confidence=scores[best], method="embedding")
        return None
```

### 3.3 Per-Agent Model Configuration

Update `Agent.__init__` to accept model overrides from TOML config:

```python
# Each agent can have its own model
coder = Agent("coder", role="...", model="qwen2.5-coder:14b")
researcher = Agent("researcher", role="...", model="qwen3:14b")
knowledge = Agent("knowledge", role="...", model="qwen3:8b")
```

### 3.4 Tests

- `tests/test_config.py` - TOML parsing, defaults, overrides
- `tests/test_router_embedding.py` - Embedding routing phase
- `tests/test_router_three_phase.py` - Full 3-phase routing pipeline

---

## Phase 4: Integration and Polish

**Goal:** Full system integration, documentation, freeze branch
**Estimated effort:** 1 session

### 4.1 Update `__init__.py`

```python
"""
LoopAGI - Open Source Multi-Agent AGI System

13 specialist agents with voice I/O, built progressively
across the chapters of "LoopAGI: The Engineering Manual"
by Alexandros Karales.
"""
__version__ = "2.0.0"
```

### 4.2 Update `pyproject.toml`

```toml
[project]
description = "Open Source Multi-Agent AGI System - 13 agents with voice"
```

Verify dependencies:
- `faster-whisper` in `[project.optional-dependencies.voice]`
- `piper-tts` in `[project.optional-dependencies.voice]`
- `sounddevice` in `[project.optional-dependencies.voice]`
- `soundfile` in `[project.optional-dependencies.voice]`
- `fastembed` in main dependencies (for embedding routing)

### 4.3 Update README.md

- Update agent table to show all 13
- Update tool table to include voice_in and voice_out
- Update quick start to show `--voice` flag
- Update book series table

### 4.4 End-to-End Testing

```bash
# Full test suite
uv run pytest tests/ -v --tb=short

# Start LoopAGI with all 13 agents
uv run loopagi --verbose

# Test routing to each agent
> write a fibonacci function          # → coder
> test the fibonacci function          # → tester
> review the fibonacci code            # → reviewer
> plan a REST API                      # → planner
> what is dependency injection         # → researcher
> list all python files                # → fileops
> set up docker compose                # → devops
> debug this traceback: ...            # → debugger
> write a README for this project      # → documenter
> search docs for routing              # → knowledge
> remember: user prefers FastAPI        # → memory
> listen                               # → listener (voice mode)
> say hello                            # → speaker (voice mode)

# Test voice mode
uv run loopagi --voice --verbose
```

### 4.5 Freeze Branch

```bash
# Ensure all tests pass
uv run pytest tests/ -v

# Commit everything
git add -A
git commit -m "feat: complete 13-agent system with voice I/O

Adds 6 new agents over the 7-agent capstone:
- debugger: root cause analysis and bug fixing
- documenter: generate docs, READMEs, docstrings
- knowledge: RAG-powered retrieval from project docs
- memory: long-term memory storage and recall
- listener: voice-to-text input (local STT via faster-whisper)
- speaker: text-to-voice output (local TTS via piper-tts)

Infrastructure upgrades:
- 3-phase routing (keyword + embedding + LLM)
- TOML config system (loopagi.toml)
- Per-agent model configuration
- Voice CLI mode (--voice flag)"

# Push to frozen branch
git push origin book/v2-13-agents

# Tag the release
git tag -a v2.0.0 -m "LoopAGI 2.0.0 - 13 agents with voice"
git push origin v2.0.0
```

---

## File Inventory: What Gets Created

### New Files

| File | Phase | Description |
|------|-------|-------------|
| `loopagi/agents/__init__.py` | 1 | Agent module (update existing) |
| `loopagi/agents/debugger.py` | 1 | Debugger agent |
| `loopagi/agents/documenter.py` | 1 | Documenter agent |
| `loopagi/agents/knowledge_agent.py` | 1 | Knowledge/RAG agent |
| `loopagi/agents/memory_agent.py` | 1 | Memory agent |
| `loopagi/agents/listener.py` | 2 | Listener agent (STT wrapper) |
| `loopagi/agents/speaker.py` | 2 | Speaker agent (TTS wrapper) |
| `loopagi/voice/listener.py` | 2 | Microphone + faster-whisper |
| `loopagi/voice/speaker.py` | 2 | Piper-tts + audio playback |
| `loopagi/core/config.py` | 3 | TOML config system |
| `loopagi.toml.example` | 3 | Example configuration |
| `tests/test_debugger.py` | 1 | Debugger tests |
| `tests/test_documenter.py` | 1 | Documenter tests |
| `tests/test_knowledge_agent.py` | 1 | Knowledge agent tests |
| `tests/test_memory_agent.py` | 1 | Memory agent tests |
| `tests/test_listener.py` | 2 | Listener tests |
| `tests/test_speaker.py` | 2 | Speaker tests |
| `tests/test_voice_integration.py` | 2 | Voice E2E tests |
| `tests/test_config.py` | 3 | Config tests |
| `tests/test_router_embedding.py` | 3 | Embedding routing tests |
| `tests/test_router_three_phase.py` | 3 | 3-phase routing tests |

### Modified Files

| File | Phase | Changes |
|------|-------|---------|
| `loopagi/__init__.py` | 4 | Update version and docstring |
| `loopagi/core/router.py` | 1, 3 | Add 6 keyword patterns, embedding phase |
| `loopagi/cli.py` | 1, 2 | Add 6 agents, voice mode flag |
| `pyproject.toml` | 2, 4 | Update description, verify voice deps |
| `README.md` | 4 | Update agent/tool tables, docs |

---

## Dependencies

### Already Installed (from 7-agent branch)

- `langchain`, `langchain-ollama`, `langchain-community`, `langgraph`
- `qdrant-client`, `fastembed`, `numpy`, `matplotlib`, `networkx`
- `rich`, `gitpython`, `httpx`

### New Required (voice optional)

```toml
[project.optional-dependencies]
voice = [
    "faster-whisper",
    "piper-tts",
    "sounddevice",
    "soundfile",
]
```

### Models Required (Ollama)

```bash
# Minimum set for 13 agents
ollama pull llama3.2          # default model
ollama pull qwen2.5-coder:14b # coder, debugger
ollama pull qwen3:14b         # researcher, reviewer, planner, documenter
ollama pull qwen3:8b          # fileops, devops, knowledge, memory

# Voice models (auto-downloaded by faster-whisper and piper-tts)
# No ollama models needed for voice
```

---

## Success Criteria

- [ ] All 13 agents instantiate without error
- [ ] Router correctly routes to all 13 agents via keyword
- [ ] Router correctly routes via embedding (Phase 2) for ambiguous queries
- [ ] Router falls back to LLM classification (Phase 3) for novel queries
- [ ] Knowledge agent can ingest docs and answer questions
- [ ] Memory agent can store and recall facts
- [ ] Debugger agent can analyze tracebacks
- [ ] Documenter agent can generate READMEs
- [ ] Listener captures and transcribes audio (with mic)
- [ ] Speaker synthesizes and plays speech (with speakers)
- [ ] Voice mode works end-to-end (`--voice` flag)
- [ ] TOML config loads and applies per-agent models
- [ ] All existing 57 test files still pass
- [ ] All new test files pass
- [ ] `uv run loopagi --verbose` starts with 13 agents listed
- [ ] Branch frozen and pushed as `book/v2-13-agents`

---

## Estimated Timeline

| Phase | Effort | Description |
|-------|--------|-------------|
| Phase 1 | 1 session | 4 text-based agents + routing + tests |
| Phase 2 | 1-2 sessions | Voice agents + tools + CLI integration |
| Phase 3 | 1-2 sessions | 3-phase routing + TOML config |
| Phase 4 | 1 session | Integration, polish, freeze |
| **Total** | **4-6 sessions** | |
