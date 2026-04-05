# ARC-AGI Solver: Improvement Research V3

**Date:** March 21, 2026  
**Author:** Alexandros Karales + Cascade AI  
**Current Score (V3 eval in progress):** ~24-28/120 projected (20-23%)  
**Previous Score (V2):** 11/120 (9.2%)  
**Hardware:** RTX 5080 (16GB VRAM), 30GB RAM, Ubuntu 25.10  

---

## What V3 Already Implements

| Technique | Module | Impact |
|-----------|--------|--------|
| D4 augmented voting | `augmentation_voter.py` | **+12 solves** (biggest win) |
| Relaxed transduction (solved=True at 100%) | `solve_improved.py` | **+4 solves** |
| Best-of-N sampling (N=5) | `sampler.py` → `llm_solver.py` | Infrastructure |
| NL description before synthesis | `nl_describer.py` → `llm_solver.py` | Alignment |
| NL instruction evolution | `nl_evolver.py` → `solve_improved.py` | Fallback path |
| Relaxed transduction floor baseline | `solve_improved.py` | Prevents regressions |
| Early-exit augmented voting | `augmentation_voter.py` | Saves 6 LLM calls/fail |

---

## Phase EE: Test-Time Training (LoRA) — HIGH PRIORITY

### What NVARC/ARChitects Does (ARC-AGI-2 Top Kaggle)

Source: [arxiv.org/html/2603.06590](https://arxiv.org/html/2603.06590)

**Core technique:** Per-task LoRA fine-tuning at inference time.

1. **Leave-one-out training:** For each task with N training pairs, create N tasks by promoting each pair to "test" in turn
2. **Augmentation:** D4 symmetry (8x) + color permutations (up to 10!) + padding/upscaling
3. **LoRA config:** rank=8, alpha=16, dropout=0.0, target="all-linear" (q/k/v/o + FFN)
4. **Gradient steps:** ~50-100 per task
5. **External memory:** FAISS retrieval of similar training tasks, added to TTT training set
6. **Cross-task augmentation modes:**
   - `Many_sim`: Leave-one-out on similar tasks
   - `Aug_0`: Leave-one-out from similar + append I/O pair from target task
   - `Aug_1`: Leave-one-out from target + append I/O pair from similar task
7. **Memory management:** bfloat16, dynamic batching, adapter mount/dismount on base model

**Ablation result:** Removing TTT drops score by **33 percentage points** — it's the single most impactful component.

### Feasibility on RTX 5080 (16GB VRAM)

| Component | VRAM |
|-----------|------|
| qwen3:8b base | ~5GB |
| LoRA rank=8 adapters | ~50MB |
| Training overhead (optimizer states, gradients) | ~2-3GB |
| **Total** | **~8GB** — fits easily |

### Implementation Plan

```
1. Install unsloth or peft for efficient LoRA training
2. Create loopagi/arc/ttt.py:
   - leave_one_out_tasks(): generate N tasks from N training pairs
   - augment_task(): D4 + color permutations → 8-80x expansion
   - train_lora(): LoRA fine-tune on augmented tasks (~50 steps)
   - generate_with_lora(): inference with adapted model
   - discard_adapter(): clean up and move to next task
3. Wire into solve_improved.py as a phase between synthesis and evolution
4. Use existing task_similarity.py for cross-task retrieval (already built)
```

**Estimated impact:** +10-20 solves. NVARC showed TTT is the #1 technique.

---

## Phase FF: SOAR Self-Improving Loop — MEDIUM PRIORITY

### What SOAR Does (52% on ARC-AGI-1)

Source: [arxiv.org/abs/2507.14172](https://arxiv.org/abs/2507.14172)

**Core technique:** Fine-tune the LLM on its own successful search traces.

1. **Evolutionary search phase:** Use LLM to generate/mutate programs for ARC tasks
2. **Hindsight learning:** Convert successful search attempts into (prompt, response) training pairs
3. **Fine-tune LLM:** LoRA fine-tune on the successful traces
4. **Iterate:** Re-run search with improved model, collect new traces, fine-tune again
5. **Key insight:** Positive transfer between sampling and refinement capabilities

### Implementation Plan

```
1. Collect search traces from full 120-task eval:
   - Every hypothesis generated
   - Every program synthesized (with similarity scores)
   - Every transduction attempt (with grid similarity)
   - Every NL instruction (with scores)
2. Filter to successful traces (similarity > 90%)
3. Format as instruction-following pairs
4. LoRA fine-tune qwen3:8b on successful traces
5. Re-run eval with improved model
6. Repeat 2-3 cycles
```

**Estimated impact:** +5-15 solves per cycle. Compounds over iterations.

---

## Phase GG: Symbolic Filtering — QUICK WIN

### What NVARC Does

Three white-box filters applied to candidate outputs:

1. **Color consistency:** Output must only use colors that appear in the task's training pairs
2. **Grid size consistency:** If all outputs share same dimensions, test output must match. If outputs scale with inputs (e.g., 2x), test output must follow same ratio
3. **Inclusion filtering:** If output ⊂ input in training (object extraction), same must hold for test

**Ablation:** Removing filtering drops score by **14 percentage points**.

### Implementation Plan

```
1. Create loopagi/arc/symbolic_filter.py:
   - filter_by_colors(predicted, task) → bool
   - filter_by_size(predicted, task) → bool
   - filter_by_inclusion(predicted, task) → bool
2. Apply to all transduction/synthesis outputs before scoring
3. Reject invalid candidates early, improve selection quality
```

**Estimated impact:** +2-5 solves. Cheap to implement, filters garbage predictions.

---

## Phase HH: Grid Traversal Representations — MEDIUM PRIORITY

### What NVARC Does

Instead of always encoding grids row-by-row left-to-right, use multiple traversal orders:

- Row-by-row (standard)
- Column-by-column
- Snake (alternating direction per row)
- Spiral
- Diagonal

**Ablation:** Removing traversals drops score by **6 percentage points**.

**Why it works:** Different traversals expose different spatial patterns. A vertical stripe is obvious in column traversal but invisible in row traversal. Multiple perspectives help the model abstract the transformation rule.

### Implementation Plan

```
1. Create loopagi/arc/grid_traversal.py:
   - traverse_row(grid) → token sequence
   - traverse_col(grid) → token sequence  
   - traverse_snake(grid) → token sequence
   - reconstruct_from_traversal(tokens, method) → grid
2. In transduction: try each traversal, vote on results
3. In synthesis prompts: include multiple traversal representations
```

**Estimated impact:** +3-6 solves. Complements D4 augmentation.

---

## Phase II: Imbue Evolver Improvements — MEDIUM PRIORITY

### What We're Missing vs Imbue's Open-Source Evolver

Source: [github.com/imbue-ai/darwinian_evolver](https://github.com/imbue-ai/darwinian_evolver)

| Imbue Feature | Our Status | Gap |
|---------------|-----------|-----|
| NL explanation before code | ✅ Implemented | — |
| Differential formatting | ✅ Implemented | — |
| Randomized mutation strength | ✅ Implemented | — |
| Population + crossover | ✅ Implemented | — |
| Transfer score (7%) | ✅ Implemented | — |
| Simplicity score (3%) | ✅ Implemented | — |
| Identity baseline = 0.2 | ✅ Implemented | — |
| **Up to 16 iterations** | ❌ We use 5 | **3x more budget** |
| **Start from identity, not seed** | ❌ We seed with best | Different strategy |
| **Two distinct outputs** | ⚠️ We duplicate | Need diversity |
| **Use reasoning model for mutations** | ❌ We use qwen3:8b | Could try qwen3:14b |

### Key Imbue Finding

> "We also experimented with using natural-language only as the representation on which mutation acts. However, we did not observe a significant performance gain from doing so."

This validates our approach — NL evolution is a fallback, not a replacement for code evolution. Imbue found the same.

### Implementation Plan

```
1. Increase evolution budget: 5 → 12 generations for near-miss tasks
2. Ensure two distinct outputs per challenge input (not just duplicated)
3. Try qwen3:14b or qwen2.5-coder:14b for evolution mutations on near-misses
4. Start evolution from identity for some tasks (diversifies search)
```

---

## Phase JJ: Ensemble Transduction + Induction — QUICK WIN

### What the Research Says

From Lewis H's review and the ARC Prize 2024 Technical Report:

> "Ensembling both transductive and inductive methods was crucial to get to the top of the leaderboard."

The Omni-ARC approach (2nd place 2024):
- Generate solutions via augmented transduction (AIRV: Augment, Inference, Reverse, Vote)
- Generate solutions via code synthesis
- Ensemble both, vote on best answer

### What We Can Do

We already have both tracks! But currently they run sequentially with early return. We should:

```
1. For unsolved tasks, run transduction AND synthesis independently
2. Collect all candidate grids from both tracks
3. Use D4 symmetry scoring to rank candidates
4. Submit top-2 distinct candidates
```

---

## Phase KK: Color Permutation Augmentation — QUICK WIN

### What Everyone Does

Color permutations are used by NVARC, Omni-ARC, and others for data augmentation. The idea: swap colors in both input and output, creating new training examples that force the model to learn the *structure* not the specific colors.

Example: if a task uses colors {1, 3, 5}, create variants with {2, 4, 7}, {6, 8, 9}, etc.

### Implementation

```
1. Add to augmentation_voter.py or separate color_augmentor.py
2. Generate 5-10 color-permuted variants per task
3. Include in TTT training data
4. Include in transduction voting pool
```

**Estimated impact:** +2-4 solves. Especially helps tasks where the model overfits to specific color values.

---

## Phase LL: DL-Guided Program Search (Long-Term)

### The Chollet Vision

From the ARC Prize 2024 Technical Report:

> "One approach that has not been tried so far (likely because it is technically challenging) but that we expect to perform well in the future, is the use of specialist deep learning models to guide the branching decisions of a discrete program search process — similar to what can be seen in the AlphaProof system from Google DeepMind."

This is the AlphaGo-for-ARC approach:
1. Build a DSL of grid operations (we have `grid_ops.py` with 37 functions)
2. Train a small neural network to predict which DSL operations are likely useful for a given task
3. Use the network to guide beam search through the DSL program space
4. Much more efficient than brute-force DSL search

### Status

Nobody has implemented this fully yet. It's the holy grail of ARC research. Our `grid_ops.py` DSL would be the foundation.

---

## Priority Execution Order

```
IMMEDIATE (before full eval completes):
  Phase GG: Symbolic filtering                        [2h]  → +2-5 solves
  Phase II: Increase evolution budget to 12 gens      [1h]  → +1-3 solves
  Phase JJ: Ensemble transduction + induction         [3h]  → +2-4 solves
  Phase KK: Color permutation augmentation            [2h]  → +1-3 solves

WEEK 1 (after V3 eval results):
  Phase EE: Test-Time Training with LoRA              [20h] → +10-20 solves
  Phase HH: Grid traversal representations            [4h]  → +3-6 solves

WEEK 2:
  Phase FF: SOAR self-improving loop                  [20h] → +5-15 solves/cycle

LONG-TERM:
  Phase LL: DL-guided program search                  [40h] → unknown (research frontier)
```

---

## Projected Scores

| Phase | Cumulative Solves | Score |
|-------|-------------------|-------|
| V2 baseline | 11 | 9.2% |
| V3 (current eval) | ~25-28 | ~21-23% |
| + Symbolic filtering + ensemble | ~30-35 | ~25-29% |
| + TTT with LoRA | ~40-50 | ~33-42% |
| + SOAR self-improvement | ~45-60 | ~38-50% |
| + DL-guided search | ? | ? |

---

## Key References (New)

| Source | Key Insight |
|--------|-------------|
| [NVARC Technical Report](https://arxiv.org/html/2603.06590) | TTT is +33pp. Symbolic filtering is +14pp. Traversals +6pp. |
| [Imbue Darwinian Evolver](https://imbue.com/research/2026-02-27-arc-agi-2-evolution/) | NL-only evolution doesn't beat code evolution. 16 iterations optimal. |
| [Lewis H Research Review](https://lewish.io/posts/arc-agi-2025-research-review) | Ensemble transductive + inductive is key. TTT per-task > TTT global. |
| [Omni-ARC (2nd place 2024)](https://ironbar.github.io/arc24/) | AIRV: Augment, Inference, Reverse, Vote. Qwen2.5-0.5B + LoRA. |
| [SOAR](https://arxiv.org/abs/2507.14172) | Self-improving via search traces → 52% on ARC-AGI-1. |
| [Redwood Research](https://redwoodresearch.substack.com/p/getting-50-sota-on-arc-agi-with-gpt) | 8K programs + revision = 50% on public eval. Revision is huge. |
| [ARC Prize 2025 Results](https://arcprize.org/blog/arc-prize-2025-results-analysis) | Refinement loop is the meta. TRM (7M params) got 45% on v1. |
| [Chollet (ARC Prize 2024 Report)](https://arxiv.org/html/2412.04604v2) | DL-guided program search is the untried approach expected to work. |

---

*ARC-AGI Solver: Improvement Research V3*  
*Copyright 2026 Alexandros Karales. All Rights Reserved.*
