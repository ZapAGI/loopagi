# ZapAGI / LoopAGI / God in the Loop — Master Checklist

**Author:** Alexandros Karales  
**Last Updated:** 2026-03-19  
**Branch:** `feature/audit-and-arc-agi`

---

## How to Read This Checklist

This is the **single source of truth** for all work across:
- **God in the Loop** (Volume 1 book + companion code)
- **LoopAGI Engineering Manual** (Volume 2 book)
- **ARC-AGI Challenge** (research chapter / benchmark)
- **ZapAGI** (production application)

Each item links to a detailed explanation in `docs/CHECKLIST_RATIONALE.md`.

---

## 1. ARC-AGI Solver (Immediate Priority)

### 1.1 Complete Evaluation
- [x] Phase A: Ollama optimization + complexity estimator (574 tests)
- [x] Phase B: Task similarity index + few-shot context
- [x] Phase C: Multi-model routing (ModelConfig, call_as)
- [x] Phase D: 5-model benchmark (qwen3:8b best at 79.4%)
- [x] Phase E: Full 120-task eval (0% solve, 67% avg similarity)
- [x] Phase F: Polars analytics foundation (arc_analytics.py, 28 tests)
- [x] Phase G: Adaptive stagnation detection
- [x] Phase H: Best-of-N sampling (sampler.py, 13 tests)
- [x] Phase I: Program mutation/evolution (mutator.py + evolver.py, 39 tests)
- [x] Phase J: Direct grid transduction (transducer.py, 34 tests)
- [x] Phase K: Object-centric grid description (grid_describer.py, 28 tests)
- [x] Phase L: Unified improved solver pipeline (solve_improved.py, 14 tests)
- [ ] **Phase M: Full 120-task improved eval** (IN PROGRESS — 2 solved so far)
- [ ] Phase N: Model upgrade eval (qwen3:14b, qwen2.5-coder:14b)
- [ ] Phase O: Final comparison report + chapter writeup

### 1.2 ARC Research Extensions
- [ ] Ensemble voting: run transduction + code synthesis in parallel, vote on outputs
- [ ] Test-time training: fine-tune a small model on each task's training pairs
- [ ] DSL compiler: compile synthesized programs into a restricted grid DSL for safety
- [ ] Multi-attempt strategy: use pass@2 with diverse candidates (warm + cold)
- [ ] ARC-AGI-2 private set submission (Kaggle)

### 1.3 ARC Chapter for the Book
- [ ] Write Chapter 23: "Testing the Thesis" (ARC as evidence for emergence)
- [ ] Create chapter examples (standalone scripts for readers)
- [ ] Write evaluation methodology section
- [ ] Create visualizations (grid diffs, similarity distributions, solve timelines)
- [ ] Single-agent vs multi-agent comparison experiment
- [ ] Phi(S) emergence measurement on ARC tasks

---

## 2. God in the Loop — Volume 1 (book/mvp branch)

### 2.1 Book Content
- [x] All 22 chapters written
- [x] Companion code for all chapters
- [x] 541+ tests passing
- [ ] Final proofreading pass
- [ ] Index generation
- [ ] Chapter 23 (ARC chapter — see §1.3)
- [ ] Artwork finalization (39 images, 3D low-poly origami theme)

### 2.2 Companion Code Fixes (from IMPROVEMENTS.md)
- [ ] **1.1** Persistent agent memory (wire MemoryStore into Agent.invoke)
- [ ] **1.2** Router learning (TF-IDF from user corrections)
- [ ] **1.3** Pipeline code execution (run generated tests, close the loop)
- [ ] **1.4** Streaming output (ChatOllama streaming mode)
- [ ] **1.5** Split cli.py into 4 files (768 lines → 4 × ~150-300 lines)
- [ ] **2.1** Agent-to-agent delegation (Agent.delegate via event bus)
- [ ] **2.2** Conversation branching (tree not list, /branch, /switch)
- [ ] **2.3** Config file (~/.config/loopagi/config.toml)
- [ ] **2.4** Tool result caching (TTL cache, invalidate on writes)

### 2.3 Test Coverage Gaps
- [ ] **3.1** CLI tests (largest module, 0 dedicated tests)
- [ ] **3.2** Memory module tests (mocked Qdrant)
- [ ] **3.3** RAG module tests (443 lines, 0 tests)
- [ ] **3.4** Async tests (Agent.ainvoke, AgentPool.execute_parallel)

### 2.4 Code Quality
- [ ] Extract magic numbers to dataclass configs
- [ ] Fix inconsistent error handling (broad Exception catches)
- [ ] Restructure inline imports (TYPE_CHECKING pattern)
- [ ] API documentation generation (pdoc or mkdocs)
- [ ] Architecture diagram (Mermaid or D2)
- [ ] Improve chapter READMEs (3-5 lines → full learning guides)

---

## 3. LoopAGI Engineering Manual — Volume 2 (book/v2 branch)

### 3.1 Foundation Upgrade (Part I)
- [ ] Chapter 1: Agent expansion (7 → 13 agents, registry pattern)
- [ ] Chapter 2: Routing engine rewrite (3-phase: keyword → embedding → LLM)
- [ ] Chapter 3: Agent protocol (standardized interface, lifecycle)
- [ ] Chapter 4: TOML configuration system

### 3.2 Specialist Agents (Part II)
- [ ] Chapter 5: Debugger agent (error classification, fix suggestions)
- [ ] Chapter 6: Documenter agent (docstring, README, changelog generation)
- [ ] Chapter 7: Knowledge agent (RAG pipeline, semantic search)
- [ ] Chapter 8: Memory agent (significance detection, decay, reinforcement)
- [ ] Chapter 9: Quality pipeline upgrade (parallel test gen, review scoring)
- [ ] Chapter 10: DevOps + FileOps agents (git workflow, scaffolding)

### 3.3 Voice Integration (Part III)
- [ ] Chapter 11: Speech-to-text (faster-whisper, VAD, streaming)
- [ ] Chapter 12: Text-to-speech (piper-tts, chunked synthesis)
- [ ] Chapter 13: Listener + Speaker agents
- [ ] Chapter 14: Voice-enabled CLI

### 3.4 Production Engineering (Part IV)
- [ ] Chapter 15: Tool system architecture (registry, composition, auth levels)
- [ ] Chapter 16: Event system (bus, handlers, background agents)
- [ ] Chapter 17: Session management + provenance
- [ ] Chapter 18: Testing, benchmarks, CI

---

## 4. ZapAGI Application (Production)

### 4.1 Core Architecture
- [ ] Port LoopAGI to production-grade Rust+Python architecture
- [ ] Agent kernel (ZAPIX) implementation
- [ ] Intent-based interaction system
- [ ] Multi-tenant session management
- [ ] Production logging + monitoring (OpenTelemetry)

### 4.2 Fine-Tuned Task Models (see docs/ZAPAGI_FINETUNING_STRATEGY.md)
- [ ] Data collection pipeline for agent interaction traces
- [ ] Router fine-tuning dataset (query → agent mapping)
- [ ] Code synthesis fine-tuning dataset (from ARC + general coding)
- [ ] Safety classifier fine-tuning dataset
- [ ] Orchestration/delegation fine-tuning dataset
- [ ] LoRA training pipeline (Unsloth / axolotl)
- [ ] Model evaluation harness
- [ ] A/B testing framework for model swaps

### 4.3 ARC Research → ZapAGI Transfer (see docs/ZAPAGI_ARC_RESEARCH_TRANSFER.md)
- [ ] Extract transduction pattern → general "predict before plan" strategy
- [ ] Extract evolution pattern → systematic code repair in quality pipeline
- [ ] Extract multi-agent solver → orchestration template for complex tasks
- [ ] Extract analytics engine → production debugging/monitoring
- [ ] Extract grid DSL → restricted execution sandbox for agent tools

### 4.4 Infrastructure
- [ ] Ollama fleet management (multi-GPU, model scheduling)
- [ ] Model registry (versioned, A/B testable)
- [ ] Continuous evaluation pipeline (nightly benchmarks)
- [ ] Cost tracking per agent / per task

---

## 5. Cross-Cutting Concerns

### 5.1 Documentation
- [ ] API reference for all modules (auto-generated)
- [ ] Architecture decision records (ADRs) for major decisions
- [ ] Onboarding guide for contributors
- [ ] Deployment guide (Ollama setup, GPU requirements)

### 5.2 Testing
- [ ] Integration test suite (full pipeline end-to-end)
- [ ] Performance regression tests
- [ ] Model quality regression tests (eval scores must not decrease)
- [ ] Chaos testing (what happens when Ollama is down?)

### 5.3 CI/CD
- [ ] GitHub Actions for all branches
- [ ] Automated test gates on PR merge
- [ ] Nightly eval runs with result tracking
- [ ] Automated release notes from git log

---

## Priority Matrix

| Priority | Category | Items | Why Now |
|---|---|---|---|
| **P0** | ARC eval | Phase M completion + report | Active eval running, book chapter depends on results |
| **P1** | ARC chapter | Chapter 23 writeup | Strongest addition to Volume 1 |
| **P1** | Code quality | CLI split, test gaps | Technical debt blocking Volume 2 |
| **P2** | Volume 2 | Part I (Foundation) | Builds on Volume 1 code |
| **P2** | ZapAGI | Fine-tuning pipeline | Competitive advantage |
| **P3** | Volume 2 | Parts II-IV | Sequential dependency on Part I |
| **P3** | ZapAGI | Production infrastructure | After research phases complete |

---

## Related Documents

| Document | Purpose |
|---|---|
| `docs/CHECKLIST_RATIONALE.md` | Why each checklist item matters |
| `docs/ZAPAGI_ARC_RESEARCH_TRANSFER.md` | How ARC research benefits ZapAGI |
| `docs/ZAPAGI_FINETUNING_STRATEGY.md` | Fine-tuning small models for ZapAGI |
| `IMPROVEMENTS.md` | Detailed code audit findings |
| `ARC_SOLVER_IMPROVEMENTS.md` | ARC-specific improvement plan |
| `docs/REFERENCE_SYSTEM.md` | Hardware/software specs for the reference dev machine |
| `ARC_AGI_CHALLENGE.md` | ARC strategy + book integration |

---

*Master Checklist — Copyright 2026 Alexandros Karales / ZapAGI. All Rights Reserved.*
