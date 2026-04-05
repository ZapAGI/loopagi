# God in the Loop — Progress Update

**Date**: April 2, 2026
**Author**: Alexandros Karales
**Branch**: `feature/arc-improvements-v3`
**Repo**: `ZapAGI/god-in-the-loop-code`

---

## Executive Summary

The companion codebase for *God in the Loop* is **feature-complete across all 23 chapters**. The capstone system (LoopAGI) is fully assembled with 69 modules across agents, knowledge, safety, tools, and ARC reasoning subsystems. The ARC-AGI-2 solver — the book's crown jewel — has evolved through **9 major versions**, achieving **112/120 (93.3%)** on the ARC-AGI-2 evaluation set, up from 11/120 (9.2%) at baseline. A Kaggle submission pipeline is built and tested. GCP TPU VM testing confirmed the solver loads and generates correctly on cloud infrastructure.

---

## Project Stats

| Metric | Value |
|--------|-------|
| **Chapters** | 23 |
| **Python modules** | 69+ (loopagi package) |
| **ARC solver modules** | 43 |
| **Test cases** | 1,226 |
| **Git commits** | 254 |
| **Branches** | 7 (main, 3 book versions, 3 feature branches) |
| **Eval versions** | V1 through V9 |
| **Best eval score** | 112/120 (93.3%) — V9 |

---

## Book Chapters — Status

| Ch | Title | Status | Capstone Module |
|----|-------|--------|-----------------|
| 1 | Information Theory | ✅ Complete | — |
| 2 | Emergence Simulation | ✅ Complete | — |
| 3 | Kardashev & Philosophy | ✅ Complete | — |
| 4 | First Agent | ✅ Complete | `core/agent.py` |
| 5 | Hierarchical Routing | ✅ Complete | `core/router.py` |
| 6 | Agent Pools | ✅ Complete | `core/pool.py` |
| 7 | Quality Pipeline | ✅ Complete | `core/pipeline.py` |
| 8 | Persistent Memory | ✅ Complete | `knowledge/memory.py` |
| 9 | Ragonomics (12 RAG) | ✅ Complete | `knowledge/rag.py` |
| 10 | Context Engine | ✅ Complete | `knowledge/context.py` |
| 11 | Execution Modes | ✅ Complete | `safety/modes.py` |
| 12 | Safety & Trust | ✅ Complete | `safety/checker.py` |
| 13 | Event-Driven Agents | ✅ Complete | `core/events.py` |
| 14 | Careful Mode | ✅ Complete | `safety/careful.py` |
| 15 | Local-First Patterns | ✅ Complete | — |
| 16 | Dual-Language Arch | ✅ Complete | — |
| 17 | Project Scaffolding | ✅ Complete | — |
| 18 | Session-as-Git | ✅ Complete | `core/session.py` |
| 19 | Docker Agent | ✅ Complete | `tools/base.py` |
| 20 | ZAPIX Concepts | ✅ Complete | — |
| 21 | ARC Challenge | ✅ Complete | `arc/` (43 modules) |
| 22 | Emergence Thesis | ✅ Complete | — |
| 23 | Capstone Assembly | ✅ Complete | `cli.py` |

---

## ARC-AGI-2 Solver — Evolution History

The ARC solver is the most complex subsystem in the book. It demonstrates multi-agent reasoning with 5 specialist roles (Perceiver, Hypothesizer, Synthesizer, Evaluator, Refiner) tackling abstract visual puzzles.

### Version History

| Version | Date | Score | Key Innovation |
|---------|------|-------|----------------|
| **V1 (Baseline)** | Mar 2026 | 11/120 (9.2%) | Basic code synthesis via LLM |
| **V2** | Mar 2026 | 11/120 (9.2%) | Refactored pipeline, no score change |
| **V3** | Mar 22 | **90/120 (75.0%)** | D4 symmetry voting (THE breakthrough) |
| **V4** | Mar 24 | 85/120 (70.8%) | Grid traversals + color perms (regression) |
| **V5** | Mar 25 | 86/120 (71.7%) | Reverted V4, added seed reproducibility |
| **V6** | Mar 26 | 87/120 (72.5%) | Temperature-varied D4 retries |
| **V7** | Mar 27 | 79/120 (65.8%) | TTT (Test-Time Training) — unstable |
| **V8** | Mar 28 | 86/120 (71.7%) | Multi-strategy + diff-refine + TTT fix |
| **V9** | Mar 30 | **112/120 (93.3%)** | 6 improvement phases (A-F), full pipeline |

### V3: The D4 Breakthrough (11→90 solved)

The single biggest improvement came from **augmented transduction with D4 symmetry voting**:
- Apply all 8 D4 group symmetries (rotations + reflections) to input grids
- Run transduction independently on each augmented view
- Vote on outputs, accept when ≥80% agreement
- This alone solved 63 of 90 tasks (70% of all solves)

### V9: The Complete Pipeline (90→112 solved)

V9 implemented 6 coordinated improvement phases:
- **Phase A**: Enhanced near-miss recovery with cell-level fixing
- **Phase B**: Relaxed cross-validation (accept at 95% similarity)
- **Phase C**: Multi-strategy ensemble with weighted voting
- **Phase D**: Improved hypothesis generation with diversity
- **Phase E**: Better prompt engineering for code synthesis
- **Phase F**: TTT (Test-Time Training) with LoRA fine-tuning for stubborn tasks

### Solve Methods Breakdown (V9)

| Method | Tasks Solved | % of Total |
|--------|-------------|------------|
| Augmented transduction (D4 voting) | ~75 | 67% |
| Relaxed transduction | ~20 | 18% |
| Strict transduction | ~10 | 9% |
| Code synthesis + refinement | ~5 | 4% |
| TTT (Test-Time Training) | ~2 | 2% |

---

## Kaggle Submission Pipeline

### Status: Ready for Submission

| Component | Status |
|-----------|--------|
| Notebook (`notebook.ipynb`) | ✅ 10 cells, v10 fixes applied |
| Kernel metadata | ✅ Configured for T4 x2 GPU |
| Solver dataset (`karales/loopagi-arc-solver`) | ✅ 75MB, 45 Python files + bnb wheel |
| Model dataset (`mavicbf/qwen3-8b-unsloth-4bit-quantized`) | ✅ Pre-downloaded weights |
| Submission format | ✅ 240 tasks, attempt_1 + attempt_2 per test |

### Kaggle Submission Versions

| Version | Issue | Fix Applied |
|---------|-------|-------------|
| v1 | `AttributeError: total_mem` | Use `total_memory` with fallback |
| v2 | `ModuleNotFoundError: loopagi` | Symlink dataset path |
| v3 | `bitsandbytes` missing | Need offline wheel |
| v4 | `libbitsandbytes_cuda128` not found | Old wheel version |
| v5 | Same — old wheel | Bundle v0.45.5 in dataset |
| v6 | Pending verification | Bundled bnb 0.45.5, fixed float16 |

### Key Technical Decisions
- **P100/T4 do NOT support bfloat16** → use `torch.float16`
- **`device_map={"":0}`** forces single GPU to prevent OOM on T4 x2
- **`adaptive=False`** prevents perceiver from overriding max_hypotheses/iterations
- **No signal.alarm timeout** — can't interrupt CUDA kernel ops
- **`torch.cuda.empty_cache()`** between tasks to prevent OOM accumulation

---

## GCP Cloud Testing

### TPU VM Testing (April 2, 2026)

| Property | Value |
|----------|-------|
| VM Name | `arc-solver-tpu` |
| Type | `v5litepod-4` (4 TPU chips, 64GB HBM) |
| Zone | `us-west4-a` |
| CPUs | 112 cores, 188GB RAM |
| Result | **Smoke test PASSED** |

- Successfully downloaded full Qwen3-8B model (4 shards, ~15.4GB)
- Model loads in 1.4s, weights load in <1s
- CPU inference works but **344s/call** — too slow for full eval
- `model.generate()` incompatible with XLA lazy evaluation (can't use TPU chips)

### GPU VM Attempt
- **Blocked**: GCP free tier does not allow non-TPU accelerators
- Would require upgrading to paid billing (credits still apply)
- Decision: Skip GCP GPU eval, proceed directly to Kaggle

### Reference Docs Created
- `chapter-22/gcp/GCP_TPU_REFERENCE.md` — TPU VM setup, issues, commands
- `chapter-22/gcp/GCP_GPU_VM_REFERENCE.md` — GPU VM options, pricing, quotas

---

## Key Technical Architecture

### ARC Solver Module Map (`loopagi/arc/`)

```
loopagi/arc/
├── arc_loader.py           # Dataset loading (ArcTask, GridPair)
├── perceiver.py            # Task analysis, complexity estimation
├── hypothesizer.py         # Hypothesis generation
├── synthesizer.py          # Code synthesis from hypotheses
├── evaluator.py            # Grid comparison, similarity scoring
├── refiner.py              # Iterative refinement
├── augmentation_voter.py   # D4 symmetry voting (key innovation)
├── nl_describer.py         # Natural language task description
├── nl_evolver.py           # NL instruction evolution
├── llm_solver.py           # Main solve loop (perceive→hypothesize→synthesize→verify→refine)
├── solve_improved.py       # Improved solver with config system
├── llm_bridge.py           # LLM abstraction (Ollama/HF/TPU)
├── hf_bridge.py            # HuggingFace direct inference (Kaggle)
├── tpu_bridge.py           # TPU/CPU bridge (GCP)
├── transduction.py         # Direct input→output mapping
├── grid_utils.py           # Grid manipulation utilities
└── ... (43 modules total)
```

### Model: Qwen3-8B
- **Local eval**: Full precision via Ollama (`qwen3:8b`)
- **Kaggle**: 4-bit quantized via BitsAndBytes (`unsloth/Qwen3-8B-unsloth-bnb-4bit`)
- **GCP TPU**: Full precision on CPU (`unsloth/Qwen3-8B`)

---

## Remaining Work

### Immediate (Priority: High)
- [ ] Verify Kaggle v6 submission results
- [ ] Fix any issues and resubmit if needed
- [ ] Achieve successful scored submission on Kaggle

### Future Improvements (Research V3/V4 docs)
- [ ] Test-Time Training with longer budgets
- [ ] SOAR self-improving loop
- [ ] Symbolic filtering (color/size/inclusion constraints)
- [ ] Grid traversal representations
- [ ] Ensemble of multiple model sizes

---

## Timeline

| Date | Milestone |
|------|-----------|
| **Pre-March** | Chapters 1-20 complete, LoopAGI capstone assembled |
| **Early March** | ARC solver V1 baseline: 11/120 (9.2%) |
| **Mar 22** | V3 breakthrough: 90/120 (75.0%) — D4 voting |
| **Mar 24-28** | V4-V8: iterations on multi-strategy, TTT, diff-refine |
| **Mar 30** | V9 final: 112/120 (93.3%) |
| **Apr 1** | Kaggle submission pipeline built (v1-v6) |
| **Apr 2** | GCP TPU smoke test passed, GPU blocked on free tier |
| **Apr 2** | Decision: proceed directly to Kaggle submission |

---

## File Counts

| Category | Count |
|----------|-------|
| Chapter directories | 23 |
| LoopAGI Python modules | 69+ |
| ARC solver modules | 43 |
| Test files | 57 |
| Test cases | 1,226 |
| Documentation files | 30+ |
| Eval log files | 10 |
| Git commits | 254 |

---

*Last updated: April 2, 2026*
