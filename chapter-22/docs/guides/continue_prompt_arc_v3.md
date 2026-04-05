# ARC-AGI Solver: Continuation Prompt V3

**Copy-paste this entire document into a new Cascade chat session to continue development.**

---

## Context

You are helping me improve my ARC-AGI solver integrated into the LoopAGI framework. The solver is part of my book "God in the Loop" companion code repository.

### Repositories

- **Book repo:** `/home/anubix/Documents/CODE/BOOKS/AGI_BOOK/` (private, github.com/ZapAGI/god-in-the-loop)
- **Code repo:** `/home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code/` (private, github.com/ZapAGI/god-in-the-loop-code)

### Branches

- `main` — latest evolving code (merged, up to date)
- `feature/arc-improvements-v3` — active dev branch (Phase EE + GG committed)
- `book/v3-arc-reasoning` — frozen branch for Volume 3

### Chapter Structure (IMPORTANT — recently restructured)

All chapters are numbered sequentially. There is NO `chapter-arc/` folder anymore.

| Chapter | Code Folder | Book Chapter | Content |
|---------|-------------|--------------|---------|
| 20 | `chapter-20/` | ZAPIX - AI-Native OS | — |
| **21** | **`chapter-22/`** | **The ARC Challenge** | ARC solver, eval scripts, reports |
| 22 | `chapter-22/` | The Emergence Thesis | emergence_thesis.py |
| 23 | `chapter-23/` | What Comes After the Loop | capstone.py, letter_to_agents.py |

### Current Eval Results (V3, March 22, 2026)

- **90/120 solved (75.0%)** — up from 11/120 (9.2%) in V2
- **8x improvement**, zero regressions
- 63 solves via augmented D4 voting, 17 via relaxed transduction, 10 via strict transduction
- Results file: `chapter-22/ARC_MODEL_REPORTS/eval_v3_full.jsonl`

### 30 Unsolved Tasks

| Tier | Count | Similarity Range | Top Tasks |
|------|-------|-----------------|-----------|
| Near-miss (≥90%) | 10 | 90-99% | 8e5c0c38 (98.7%), d59b0160 (96.9%), 6e453dd6 (96.5%) |
| Mid-range (50-89%) | 10 | 51-89% | 7c66cb00 (89.8%), 71e489b6 (88.9%), 221dfab4 (86.1%) |
| Hard (<50%) | 10 | 0-49% | 291dc1e1 (24.3%), 67e490f4 (20.1%), 195c6913 (0%) |

### Hardware

- Ubuntu 25.10, RTX 5080 (16GB VRAM), 30GB RAM
- Ollama with qwen3:8b (primary), qwen3:14b, qwen2.5-coder:14b installed
- Python 3.14 (main venv) — **NO PyTorch CUDA support on 3.14**
- Python 3.12 TTT venv at `chapter-22/ttt_venv/` — PyTorch 2.10+cu128 + Unsloth working
- **VRAM SAFETY:** TTT and Ollama CANNOT coexist. Stop Ollama before TTT. See `chapter-22/TTT_BEST_PRACTICES.md`

### Codebase

- 39 modules in `loopagi/arc/` (~11,000 LOC)
- 1178 tests passing (all green)
- Key entry point: `loopagi/arc/solve_improved.py` → `solve_task_improved()`
- Eval script: `chapter-22/run_eval_improved.py`
- TTT script: `chapter-22/ttt_train.py` (runs in ttt_venv)

---

## What Was Already Done (Phases 1-EE)

### Original Phases (1-AA) — V2 Baseline: 11/120 (9.2%)

| Phase | What |
|-------|------|
| 1-5 | Core: arc_loader, grid_ops, grid_objects, 5 specialist agents, task_similarity, llm_bridge |
| A | Flash attention, complexity estimator, adaptive iteration counts |
| B | Few-shot context from similar tasks |
| C | ModelConfig, per-agent model routing |
| D | 5-model benchmark (qwen3:8b won) |
| F | Polars analytics engine |
| G | Adaptive stagnation detection (3-tier thresholds) |
| H | Best-of-N sampling module |
| I | AST mutation + evolution |
| J | Direct transduction (fast path) |
| K | Object-centric grid descriptions |
| V | Population pool + crossover in LLM evolution |
| W | Identity trap bypass + relaxed transduction fallback |
| X | Imbue-style normalized fitness scoring |
| Y | Iterative transduction refinement + differential formatting |
| Z | Transfer scorer module |
| AA | Solution store (few-shot from solved tasks) |

### Improvement Phases (BB-EE) — V3: 90/120 (75.0%)

| Phase | What | Impact |
|-------|------|--------|
| **BB** | Wire Best-of-N sampling into synthesis loop, fix cell fixer bug (propagate fixed program), extract `llm_solver.py` from `llm_bridge.py` | Infrastructure |
| **CC** | NL description before synthesis (`nl_describer.py`), D4 augmented voting (`augmentation_voter.py`), Imbue techniques wired | **+63 solves via augmented voting** |
| **DD** | NL instruction evolution (`nl_evolver.py`), dual-track pipeline (NL evolution as fallback for unsolved tasks) | Fallback path |
| **Fixes** | Relaxed transduction `solved=True` at 100%, floor baseline prevents regressions, voting threshold 80%, early-exit optimization | **+17 relaxed transduction solves** |
| **GG** | Symbolic filtering (`symbolic_filter.py`) — color/size/inclusion priors from NVARC. Wired into augmented voting | Quality filter |
| **EE** | Test-Time Training with LoRA (`ttt.py` + `ttt_train.py`). Python 3.12 venv with PyTorch cu128 + Unsloth. VRAM safety (stop Ollama before training). Smoke test passed. | **Not yet evaluated** |
| **HH** | Grid traversal representations (`grid_traversal.py`). Column/snake/diagonal/spiral encodings wired into augmented voting. NVARC +6pp. | Diversity |
| **KK** | Color permutation augmentation (`color_augmentor.py`). 5 random color remaps per task wired into voting pool. | Diversity |
| **JJ** | Ensemble transduction + induction (`ensemble.py`). Collects candidates from all tracks, structural scoring, picks best distinct. | Candidate selection |
| **II** | Evolution budget increased: 10→12 generations, 200→300 mutations. Imbue uses 16. | More search |

### Key Architecture Decisions

- **Augmented D4 voting is the #1 technique** — 70% of all solves
- **Code synthesis/evolution produces 0 solves** on 8b models — transduction only
- **Relaxed transduction floor** prevents regressions from code synthesis
- **TTT requires stopping Ollama** — they can't share 16GB VRAM
- **All modules under 500 lines** — enforced by test_file_size.py

---

## TODO: Improvement Checklist

Read the full research document first:
**`chapter-22/ARC_IMPROVEMENT_RESEARCH_V3.md`**

### ✅ COMPLETED

- [x] Phase BB: Wire Best-of-N sampling
- [x] Phase CC: NL description + D4 augmented voting
- [x] Phase DD: NL instruction evolution + dual-track pipeline
- [x] Phase GG: Symbolic filtering (color/size/inclusion)
- [x] Phase EE: TTT with LoRA (code written, smoke test passed)
- [x] Chapter restructuring: chapter-arc/ → chapter-22/
- [x] Phase HH: Grid traversal representations (5 methods, wired into voting)
- [x] Phase KK: Color permutation augmentation (5 permutations, wired into voting)
- [x] Phase JJ: Ensemble transduction + induction (structural scoring)
- [x] Phase II: Evolution budget 10→12 generations, 200→300 mutations

### 🔲 TODO: Validate & Test

- [ ] **Run TTT on 10 near-miss tasks** — validate TTT actually improves scores
  - Close Windsurf first, run from terminal
  - `chapter-22/ttt_venv/bin/python chapter-22/ttt_train.py --input /tmp/task.json --output /tmp/pred.json --steps 30`
  - Compare TTT predictions vs V3 eval results
  - If TTT helps, run V4 eval with TTT enabled

- [ ] **Run V4 eval WITHOUT TTT** (safe, tests symbolic filtering impact)
  ```bash
  nohup nice -n 10 uv run python chapter-22/run_eval_improved.py \
    --no-few-shot --no-ttt --resume \
    --output chapter-22/ARC_MODEL_REPORTS/eval_v4_nottt.json \
    -v > eval_v4.log 2>&1 &
  ```

### 🔲 TODO: Major Improvements (1-2 weeks each)

- [ ] **Phase FF: SOAR self-improving loop** (+5-15 solves/cycle)
  - Collect search traces from V3 eval (hypotheses, programs, scores)
  - Filter to successful traces (similarity > 90%)
  - LoRA fine-tune qwen3:8b on successful traces
  - Re-run eval with improved model
  - Repeat 2-3 cycles

- [ ] **Phase LL: DL-guided program search** (research frontier)
  - Use `grid_ops.py` DSL (37 functions) as search space
  - Train small neural network to predict useful DSL operations per task
  - Guide beam search through DSL program space
  - This is Chollet's "untried approach expected to work"

### 🔲 TODO: Documentation & Book

- [ ] Update `chapter-22/README.md` with current module list and run instructions
- [ ] Update book chapter_21.md if TTT produces new results
- [ ] Merge `feature/arc-improvements-v3` to main when ready
- [ ] Update frozen branch `book/v3-arc-reasoning`

---

## Key Research Sources

| Source | What It Tells Us |
|--------|-----------------|
| [NVARC Technical Report](https://arxiv.org/html/2603.06590) | TTT = +33pp. Symbolic filtering = +14pp. Traversals = +6pp. |
| [Imbue Darwinian Evolver](https://imbue.com/research/2026-02-27-arc-agi-2-evolution/) | NL-only evolution doesn't beat code. 16 iterations optimal. Identity=0.2. |
| [Lewis H Research Review](https://lewish.io/posts/arc-agi-2025-research-review) | Ensemble transductive + inductive is key. TTT per-task > global. |
| [SOAR](https://arxiv.org/abs/2507.14172) | Self-improving via search traces → 52% on ARC-AGI-1. |
| [ARC Prize 2025 Results](https://arcprize.org/blog/arc-prize-2025-results-analysis) | Refinement loop is the meta. TRM (7M params) got 45% on v1. |
| Full research doc: `chapter-22/ARC_IMPROVEMENT_RESEARCH_V3.md` | All techniques, implementation plans, projected impacts |

---

## Key Files to Read First

1. `chapter-22/ARC_IMPROVEMENT_RESEARCH_V3.md` — Full research doc with all improvement phases
2. `loopagi/arc/solve_improved.py` — Main solver pipeline (477 LOC)
3. `chapter-22/run_eval_improved.py` — Eval script with all CLI flags
4. `loopagi/arc/ttt.py` — TTT orchestrator (327 LOC)
5. `chapter-22/ttt_train.py` — Standalone TTT training script (Python 3.12)
6. `loopagi/arc/augmentation_voter.py` — D4+traversal+color voting (350 LOC, the key innovation)
7. `loopagi/arc/symbolic_filter.py` — Symbolic filtering (239 LOC)
8. `loopagi/arc/grid_traversal.py` — Grid traversal representations (410 LOC)
9. `loopagi/arc/color_augmentor.py` — Color permutation augmentation (247 LOC)
10. `loopagi/arc/ensemble.py` — Ensemble scoring across tracks (335 LOC)
11. `chapter-22/TTT_BEST_PRACTICES.md` — VRAM safety guide
12. `chapter-22/ARC_MODEL_REPORTS/eval_v3_full.jsonl` — Current eval results

---

## Rules

- Always use `pnpm` instead of `npm`
- Never pin versions, always install latest
- Use `uv` for Python package management (NOT pip)
- Use multi-edit tool, never grep+sed
- All modules must be under 500 lines
- Every public function needs tests
- Use feature branch development: `git checkout -b feature/branch_name`
- Commit with descriptive messages: `git add -A && git commit -m "message" && git push`
- Run tests: `uv run pytest tests/ -v --tb=short`
- **VRAM SAFETY:** Never run TTT + Ollama simultaneously. Close Windsurf for TTT. Max 1 Windsurf during evals.
- **Python 3.14 has NO PyTorch CUDA.** TTT uses separate Python 3.12 venv at `chapter-22/ttt_venv/`
- Chapter 21 = ARC (was chapter-arc, renamed). All paths use `chapter-22/` not `chapter-arc/`

---

## Start Here

1. Read `chapter-22/ARC_IMPROVEMENT_RESEARCH_V3.md`
2. Read `loopagi/arc/solve_improved.py`
3. Check current branch: `git branch --show-current` (should be `feature/arc-improvements-v3`)
4. Run tests: `uv run pytest tests/ -q`
5. Pick the next TODO item from the checklist above
6. Implement, test, commit after each item
7. Run targeted eval on near-miss tasks to validate
8. Update book chapter when results change

**Current target: Get from 75% to 85%+ on the 120-task eval.**

---

*Copyright 2026 Alexandros Karales. All Rights Reserved.*
