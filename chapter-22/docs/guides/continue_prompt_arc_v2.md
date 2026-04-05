# ARC-AGI Solver: Continuation Prompt V2

**Copy-paste this entire document into a new Cascade chat session to continue development.**

---

## Context

You are helping me improve my ARC-AGI solver integrated into the LoopAGI framework. The solver is part of my book "God in the Loop" companion code repository.

### Repositories

- **Book repo:** `/home/anubix/Documents/CODE/BOOKS/AGI_BOOK/` (private, github.com/ZapAGI/god-in-the-loop)
- **Code repo:** `/home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code/` (private, github.com/ZapAGI/god-in-the-loop-code)

### Branches

- `main` — latest evolving code (merged, up to date)
- `feature/audit-and-arc-agi` — active dev branch (synced with main)
- `book/v3-arc-reasoning` — frozen branch for Volume 3

### Current Eval Results (120-task, March 20, 2026)

- **11/120 solved (9.2%)**, avg similarity 63.1%
- 10 solves via transduction, 1 via code synthesis
- 22 near-misses at 90-99% similarity
- 0 solves from evolution or high-complexity tasks
- Results file: `chapter-22/ARC_MODEL_REPORTS/eval_v2_full.jsonl`

### Hardware

- Ubuntu 25.10, RTX 5080 (16GB VRAM), 30GB RAM
- Ollama with qwen3:8b (primary), qwen3:14b, qwen2.5-coder:14b installed
- Caffeine installed and configured for auto-start (prevents suspend during long runs)

### Codebase

- 30 modules in `loopagi/arc/` (9,008 LOC)
- 918 tests passing (all green)
- Key entry point: `loopagi/arc/solve_improved.py` → `solve_task_improved()`
- Eval script: `chapter-22/run_eval_improved.py`

---

## What Was Already Done (Phases 1-AA)

All of these are implemented, tested, and merged:

| Phase | What |
|-------|------|
| 1-5 | Core: arc_loader, grid_ops, grid_objects, 5 specialist agents, task_similarity, llm_bridge |
| A | Flash attention, complexity estimator, adaptive iteration counts |
| B | Few-shot context from similar tasks |
| C | ModelConfig, per-agent model routing |
| D | 5-model benchmark (qwen3:8b won) |
| F | Polars analytics engine |
| G | Adaptive stagnation detection (3-tier thresholds) |
| H | Best-of-N sampling module (exists but **NOT wired**) |
| I | AST mutation + evolution |
| J | Direct transduction (fast path) |
| K | Object-centric grid descriptions |
| V | Population pool + crossover in LLM evolution |
| W | Identity trap bypass + relaxed transduction fallback |
| X | Imbue-style normalized fitness scoring |
| Y | Iterative transduction refinement + differential formatting |
| Z | Transfer scorer module (exists but **NOT wired**) |
| AA | Solution store (few-shot from solved tasks) |

---

## TODO: What Needs To Be Done

Read the full research document first:
**`chapter-22/ARC_IMPROVEMENT_RESEARCH_V2.md`**

Then execute this plan in order:

### Phase BB: Wire Existing Modules (Tier 1, ~3 hours)

1. **Wire Best-of-N sampling** (`sampler.py`) into `solve_improved.py`
   - Replace single synthesis call with `sample_n_programs()` in the main hypothesis loop
   - Use temperature variation (0.3 to 0.9) across N=5 samples
   - Pick best by training pair similarity

2. **Wire transfer scorer** (`transfer_scorer.py`) into evolution fitness
   - Integrate into `fitness.py` or `llm_evolver.py`
   - Use as 7% of total fitness score (matching Imbue's weighting)
   - Requires LLM call, so only use for top candidates

3. **Wire cell fixer** (`cell_fixer.py`) as post-evolution repair step
   - After evolution completes with a near-miss, run cell fixer on the remaining wrong cells
   - Add to `solve_improved.py` after the evolution block

4. **Run targeted eval** on the 22 near-miss tasks only (not full 120) to validate improvements

### Phase CC: Imbue Techniques (Tier 2, ~6 hours)

5. **Natural language explanation before code** — Add a "describe the transformation in English" step before synthesis in `solve_improved.py`. Pass the NL description into the synthesis prompt.

6. **Randomized mutation strength** — In `llm_evolver.py`, randomly choose between "small incremental" and "think outside the box" mutation prompts.

7. **Augmentation-based voting for transduction** — Create `loopagi/arc/augmentation_voter.py`:
   - Generate 8 augmented versions of each task (D4 symmetry: 4 rotations × 2 reflections)
   - Run transduction on each
   - Reverse augmentations
   - Majority vote on output grid
   - This leverages the fact that LLMs reason better about horizontal patterns than vertical ones

8. **Two-attempt strategy** — Ensure the solver returns top-2 distinct predictions per challenge input

### Phase DD: Natural Language Evolution (Tier 3, ~12 hours)

9. **Create `loopagi/arc/nl_evolver.py`** — Evolve natural language instructions instead of Python code:
   - Generate 10 candidate NL instructions describing the transformation
   - Score by having a sub-agent apply instructions to training examples
   - Individual revision (refine single instruction with error feedback)
   - Pooled revision (combine best elements from multiple instructions)
   - This is the Jeremy Berman approach and addresses our core weakness (code synthesis = 1% success rate on 8b models)

10. **Create dual-track pipeline** — Run transduction AND NL-evolution in parallel, pick best result

### Phase EE: Test-Time Training (Tier 4, ~20 hours)

11. **Per-task LoRA fine-tuning** using unsloth or peft:
    - Augment each task (rotations, reflections, color permutations)
    - Leave-one-out training examples
    - LoRA rank=8, alpha=16, ~50-100 gradient steps per task
    - Generate solutions with adapted model, then discard adapter
    - VRAM budget: qwen3:8b (~5GB) + LoRA (~50MB) = well within 16GB

12. **Cross-task retrieval for TTT** — Use existing `task_similarity.py` to find similar training tasks, add their I/O pairs to TTT training set

### Phase FF: Self-Improvement (Tier 5, ~20 hours)

13. **Collect search traces** from all 120 tasks into structured JSONL
14. **Fine-tune qwen3:8b** on successful search traces (SOAR approach)
15. **Re-run eval** with improved model, repeat

---

## Rules

- Always use `pnpm` instead of `npm`
- Never pin versions, always install latest
- Use `uv` for Python package management
- Use multi-edit tool, never grep+sed
- All modules must be under 500 lines
- Every public function needs tests
- Use feature branch development: `git checkout -b feature/branch_name`
- Commit with descriptive messages: `git add -A && git commit -m "message" && git push`
- Run eval with: `nohup nice -n 10 uv run python chapter-22/run_eval_improved.py --no-few-shot --output chapter-22/ARC_MODEL_REPORTS/eval_v3.json --resume -v > eval_v3.log 2>&1 &`
- Monitor eval: `tail -f eval_v3.log` or `wc -l chapter-22/ARC_MODEL_REPORTS/eval_v3.jsonl`
- Run tests: `uv run pytest tests/ -v --tb=short`
- Always ensure caffeine is running before long evals: `caffeine &`

---

## Key Files to Read First

1. `chapter-22/ARC_IMPROVEMENT_RESEARCH_V2.md` — Full research document with SOTA analysis
2. `loopagi/arc/solve_improved.py` — Main solver pipeline (474 LOC)
3. `chapter-22/run_eval_improved.py` — Eval script (416 LOC)
4. `loopagi/arc/llm_evolver.py` — LLM-guided evolution (492 LOC)
5. `loopagi/arc/sampler.py` — Best-of-N sampling (216 LOC, NOT wired)
6. `loopagi/arc/transfer_scorer.py` — Transfer scorer (125 LOC, NOT wired)
7. `loopagi/arc/cell_fixer.py` — Cell-level repair (235 LOC, NOT wired)
8. `chapter-22/ARC_MODEL_REPORTS/eval_v2_full.jsonl` — Current eval results

---

## Start Here

1. Read `chapter-22/ARC_IMPROVEMENT_RESEARCH_V2.md`
2. Read `loopagi/arc/solve_improved.py`
3. Create a new feature branch: `git checkout -b feature/arc-improvements-v2`
4. Start with Phase BB (wire existing modules)
5. Run targeted eval on near-miss tasks after each phase
6. Commit after each phase
7. Update the book chapter (`AGI_BOOK/chapters/chapter_21.md`) with new results

**Target: Get from 9.2% to 25%+ on the 120-task eval.**

---

*Copyright 2026 Alexandros Karales. All Rights Reserved.*
