# ARC-AGI Solver: Improvement Research V2

**Date:** March 20, 2026
**Author:** Alexandros Karales + Cascade AI
**Current Score:** 11/120 (9.2%), avg similarity 63.1%
**Target Score:** 30-40/120 (25-33%)
**Hardware:** RTX 5080 (16GB VRAM), 30GB RAM, Ubuntu 25.10

---

## Current State Summary

### What We Have (30 modules, 9,008 LOC, 918 tests)

| Component | Module | Status |
|-----------|--------|--------|
| Transduction (fast path) | `transducer.py` | ✅ Wired, 10/10 solves |
| Transduction refinement | `transducer_refine.py` | ✅ Wired |
| Code synthesis | `synthesizer.py` + `llm_bridge.py` | ✅ Wired, 1/100 solves |
| AST mutation evolution | `mutator.py` + `evolver.py` | ✅ Wired, 0 solves |
| LLM-guided evolution | `llm_evolver.py` | ✅ Wired, 0 solves |
| Population pool | `population.py` | ✅ Wired |
| Best-of-N sampling | `sampler.py` | ⚠️ **NOT wired** |
| Transfer scorer | `transfer_scorer.py` | ⚠️ **NOT wired** |
| Solution store | `solution_store.py` | ✅ Wired into eval |
| Cell fixer | `cell_fixer.py` | ⚠️ **NOT wired** |
| Object descriptions | `grid_describer.py` | ✅ Imported, partially used |
| Fitness scoring | `fitness.py` | ✅ Wired |
| Analytics | `arc_analytics.py` | ✅ Wired |
| Few-shot context | `few_shot.py` | ✅ Wired |
| Task similarity | `task_similarity.py` | ✅ Wired |

### Eval Breakdown

| Method | Tasks | Solved | Rate |
|--------|-------|--------|------|
| Transduction (fast path) | 10 | 10 | 100% |
| Medium complexity (synthesis) | 46 | 1 | 2.2% |
| High complexity (evolution) | 54 | 0 | 0% |
| Relaxed transduction (fallback) | 9 | 0 | 0% |

**Key insight:** Transduction produces 91% of solves. Code synthesis/evolution on qwen3:8b is nearly non-functional (1/100).

---

## State of the Art (2024-2026)

### Leaderboard Snapshot (ARC-AGI-2, as of March 2026)

| System | Score | Cost/Task | Method |
|--------|-------|-----------|--------|
| Gemini 3 Deep Think | 84.6% | $13.62 | Frontier reasoning model |
| Gemini 3.1 Pro + Imbue Evolver | 95.1% | $8.71 | Code evolution harness |
| Poetiq + Gemini 3 Pro | 54% | $31 | Consensus refinement |
| Imbue + Kimi K2.5 (open-weights) | 34% | $2.67 | Code evolution |
| Jeremy Berman (Grok-4) | 79.6% v1 | $8.42 | NL evolution + multi-agent |
| NVARC (zero-pretraining DL) | Top Kaggle | - | LongT5 + TTT + augmentation |
| TRM (7M params) | 45% v1, 8% v2 | - | Recursive refinement |
| CompressARC (76K params) | 20% v1 | - | MDL gradient descent |
| SOAR (self-improving) | 52% v1 | - | Evolutionary + self-fine-tune |
| **Our system (qwen3:8b local)** | **9.2%** | **$0** | **Transduction + evolution** |

### Key Techniques from SOTA

#### 1. Imbue Darwinian Evolver (Open Source)

**Source:** [imbue.com/research/2026-02-27-arc-agi-2-evolution](https://imbue.com/research/2026-02-27-arc-agi-2-evolution/)
**Repo:** [github.com/imbue-ai/darwinian_evolver](https://github.com/imbue-ai/darwinian_evolver)

Core techniques:
- **Natural language explanation first:** Before code, ask LLM to describe the transformation rule in English. Aligns LLM priors with human visual language.
- **Differential example formatting:** When output grid = same size as input, show only changed cells. Helps LLM focus on what actually changes.
- **Randomized mutation strength:** Randomly prompt for "small incremental changes" vs "think outside the box, major reinterpretation." Prevents local maxima stagnation.
- **Post-mutation diversity filter:** Only accept mutations that produce different outputs on at least one input. Prevents trivial code changes dominating population.
- **Crossover mutations (25%):** Sample 3 parents, ask LLM to combine transformation rules into single child.
- **3-component fitness:** 90% correctness (with identity baseline=0.2), 7% transfer score (LLM judges generalization to challenge inputs), 3% simplicity score (fewer hardcoded constants = better).
- **Global population per task:** Fitness-weighted sampling of parents. Up to 16 iterations per task.
- **Two-attempt submission:** Select two best-scoring distinct outputs per challenge input.

**What we already have vs Imbue:**
- ✅ Identity penalty in fitness (0.2 baseline)
- ✅ Differential formatting for near-identity tasks
- ✅ Population pool with fitness-weighted selection
- ✅ Crossover mutations
- ✅ Transfer scorer (exists but NOT wired)
- ✅ Simplicity score (exists in fitness.py)
- ❌ Natural language explanation before code generation
- ❌ Randomized mutation strength prompting
- ❌ Two-attempt submission strategy

#### 2. Jeremy Berman: Natural Language Evolution

**Source:** [jeremyberman.substack.com](https://jeremyberman.substack.com/p/how-i-got-the-highest-score-on-arc-agi-again)

Key innovation: **Evolve natural language instructions instead of Python code.**
- LLM generates plain-English instructions describing the transformation
- A sub-agent applies instructions to training examples to score fitness
- Two revision strategies: individual (refine single instruction) and pooled (combine multiple)
- Architecture: 30 initial candidates → top 5 individual revisions → top 5 pooled revisions (40 total per task)
- Finding: Python code is too brittle for complex ARC-v2 tasks; English instructions are more flexible
- "Dead reasoning zones" in LLMs prevent consistent logic in novel domains

**Relevance to us:** Our 8b model struggles with code synthesis (1/100 solves). Switching the evolution representation from Python to natural language could dramatically improve the quality of the mutation/refinement loop.

#### 3. SOAR: Self-Improving Evolutionary Program Synthesis

**Source:** [arxiv.org/abs/2507.14172](https://arxiv.org/abs/2507.14172)
**Repo:** [github.com/flowersteam/SOAR](https://github.com/flowersteam/SOAR)

Key innovation: **Fine-tune the LLM on its own search traces.**
- Alternates between: (1) evolutionary search using LLM, (2) hindsight learning that converts search attempts into training data
- Fine-tunes the LLM's sampling AND refinement capabilities from successful search traces
- Positive transfer between sampling and refinement tasks
- Achieves 52% on ARC-AGI-1 public test set

**Relevance to us:** We could collect our search traces (all hypotheses, programs, scores) and fine-tune qwen3:8b on them using LoRA. This would make the model better at ARC tasks over time without needing a bigger model.

#### 4. NVARC / ARChitects: Test-Time Training (TTT)

**Source:** [ARC-AGI-2 Technical Report](https://arxiv.org/html/2603.06590)

Key innovation: **LoRA fine-tune per task at inference time.**
- Uses LongT5 encoder-decoder architecture
- Per-task LoRA fine-tuning (rank=8, alpha=16) on augmented training examples
- Data augmentation: rotations, reflections, transpositions, color permutations, padding
- Leave-one-out: promote each training pair to "test" in turn to create TTT training data
- External memory (FAISS): retrieve similar training tasks and add to TTT training set
- Beam search decoding → filtering (shape/color consistency) → scoring (D4 symmetry invariance)

**Relevance to us:** TTT with LoRA on our local qwen3:8b could be game-changing. We can augment each task into 8+ variants (rotations + reflections), fine-tune a LoRA adapter per task, then generate solutions. This is feasible on 16GB VRAM.

#### 5. TRM / CompressARC: Zero-Pretraining Deep Learning

**Source:** ARC Prize 2025 Paper Awards

Key innovations:
- **TRM (7M params):** Recursive refinement network. Starts with embedded input, iteratively improves answer over 16 steps. 45% on ARC-AGI-1, 8% on ARC-AGI-2.
- **CompressARC (76K params):** Minimizes description length (MDL) at test time. No pretraining, no dataset, no search. Just gradient descent on a tiny network. 20% on ARC-AGI-1.

**Relevance to us:** These show that very small, task-specific models can be competitive. We could explore training tiny per-task models alongside our LLM pipeline as an ensemble.

#### 6. ARC Prize 2025 "Refinement Loop" Meta

The central theme of 2025 ARC research: **iterative refinement is intelligence.**
- Two phases: explore (generate candidates) → verify (score with feedback signal) → refine → repeat
- General-purpose refinement harnesses (GEPA, DSPy) can improve any base model
- Augmentation-based voting: run inference on 96 augmented versions, reverse augmentations, vote on best answer
- Consistency across augmentations is a strong signal for correctness

---

## Improvement Plan: Path from 9.2% to 25-33%

### Tier 1: Wire Existing Modules (1-2 hours, +2-5 solves)

These modules already exist with tests but are not connected to the pipeline.

#### 1A. Wire Best-of-N Sampling

`sampler.py` (216 LOC, tested) generates N candidate programs with temperature variation and picks the best. Currently not called from `solve_improved.py`.

**Expected impact:** More synthesis candidates = higher chance of hitting a correct program. Should help the 46 medium-complexity tasks where we currently get 1 solve.

#### 1B. Wire Transfer Scorer into Evolution Fitness

`transfer_scorer.py` (125 LOC, tested) uses an LLM to evaluate how well a program generalizes to challenge inputs. Imbue uses this as 7% of their fitness score. Currently not integrated into `evolver.py` or `llm_evolver.py`.

**Expected impact:** Better fitness scoring = better parent selection in evolution = better children.

#### 1C. Wire Cell Fixer as Post-Evolution Step

`cell_fixer.py` (235 LOC, tested) performs targeted cell-level repair on near-miss grids. Could be applied after evolution to fix the remaining 1-5 wrong cells.

**Expected impact:** Could convert some of the 22 near-misses (90-99%) to exact solves.

### Tier 2: Adopt Imbue Techniques (4-6 hours, +3-8 solves)

#### 2A. Natural Language Explanation Before Code

Before code synthesis, ask the LLM to describe the transformation rule in plain English. This aligns the model's priors with human visual reasoning.

**Implementation:** Add a "describe" step before synthesis in `solve_improved.py`. Pass the NL description to the synthesizer prompt.

#### 2B. Randomized Mutation Strength

When prompting for mutations in `llm_evolver.py`, randomly choose between:
- "Make small, incremental changes to improve accuracy"
- "Think outside the box. Consider a completely different approach"

**Implementation:** Add a `mutation_strength` parameter to the mutation prompt template.

#### 2C. Two-Attempt Strategy

ARC-AGI allows 2 submission attempts per challenge input. Select the two highest-scoring distinct outputs.

**Implementation:** Already partially supported. Need to ensure `solve_improved.py` returns top-2 distinct predictions.

#### 2D. Augmentation-Based Voting

For transduction: generate predictions on 8 augmented versions of the task (D4 symmetry group: 4 rotations × 2 reflections). Reverse the augmentations. Vote on the most common output.

**Implementation:** New module `augmentation_voter.py`. Use existing `grid_ops.py` rotation/reflection functions.

### Tier 3: Natural Language Evolution (8-12 hours, +5-15 solves)

This is the Jeremy Berman approach, which addresses our core weakness: code synthesis on 8b models is nearly non-functional.

#### 3A. Evolve NL Instructions Instead of Python

Replace the Python code evolution path with natural language instruction evolution:
1. Generate 10 candidate NL instructions describing the transformation
2. Score each by having a sub-agent apply it to training examples
3. Refine top-5 individually (show errors + ask for corrections)
4. Pool top-5 (combine best elements into new instructions)
5. Apply winning instruction to test inputs

**Why this is high-ROI:** Our 8b model is much better at writing English descriptions than syntactically correct Python transform functions. The current 1/100 synthesis solve rate proves code generation is the bottleneck.

#### 3B. Dual-Track Pipeline

Run both transduction AND NL-evolution in parallel:
- Track A: Transduction (fast, handles simple tasks)
- Track B: NL-evolution (slower, handles complex tasks)
- Pick the best result from either track

### Tier 4: Test-Time Training with LoRA (12-20 hours, +10-20 solves)

This is the most technically ambitious improvement but has the highest ceiling.

#### 4A. Per-Task LoRA Fine-Tuning

For each task:
1. Generate augmented training data (rotations, reflections, color permutations)
2. Create leave-one-out training examples
3. Fine-tune a LoRA adapter (rank=8) on qwen3:8b for the specific task
4. Generate solutions with the adapted model
5. Discard the adapter and move to next task

**VRAM budget:** qwen3:8b = ~5GB. LoRA rank 8 adds ~50MB. Total ~5.5GB. Well within 16GB.

**Implementation:** Use `unsloth` or `peft` for efficient LoRA training. ~50-100 gradient steps per task.

#### 4B. Cross-Task Retrieval for TTT

Use our existing `task_similarity.py` to find similar training tasks. Include their I/O pairs in the TTT training data for the target task. This is exactly what NVARC does with FAISS.

#### 4C. Self-Improving Loop (SOAR)

Collect search traces from all 120 tasks:
- Every hypothesis generated
- Every program synthesized
- Every refinement attempt
- Fitness scores for all candidates

Fine-tune qwen3:8b on successful search traces. Re-run the eval. Repeat.

**Expected impact:** SOAR achieves 52% on ARC-AGI-1 with this approach. Even a fraction of that gain would be transformative for us.

### Tier 5: Ensemble and Hybrid (4-8 hours, +2-5 solves)

#### 5A. Multi-Model Pipeline

Run a fast first pass with qwen3:8b. For unsolved tasks, retry with a 14b model on near-misses only.

**Implementation:** Already have qwen3:14b and qwen2.5-coder:14b installed. Need to add retry logic.

#### 5B. Transduction + Code Hybrid

For near-miss transduction results: use the predicted grid as a target for code synthesis. "Write a function that produces this output from this input." This gives the code synthesizer a concrete target instead of having to infer the rule.

#### 5C. DSL-Guided Search (Long-term)

Build a small domain-specific language for common ARC operations (flood fill, rotate, mirror, crop, tile, color swap). Use the LLM to select/compose DSL primitives instead of writing raw Python.

**Relevance:** The ARC Prize technical report notes that "deep learning-guided program synthesis does not currently decisively beat DSL-based brute-force program search." A hybrid approach could leverage both.

---

## Priority Execution Order

```
Week 1 (Quick Wins):
  Tier 1A: Wire Best-of-N sampling                     [1h]  → +1-3 solves
  Tier 1B: Wire transfer scorer                         [1h]  → +0-2 solves
  Tier 1C: Wire cell fixer                              [1h]  → +0-2 solves
  Tier 2D: Augmentation-based voting for transduction   [2h]  → +1-3 solves
  Tier 2A: NL explanation before code                   [2h]  → +1-2 solves
  → Expected: 15-20 solves (12-17%)

Week 2 (NL Evolution):
  Tier 3A: NL instruction evolution                     [8h]  → +5-10 solves
  Tier 3B: Dual-track pipeline                          [4h]  → integrated
  Tier 2B: Randomized mutation strength                 [1h]  → +0-2 solves
  Tier 2C: Two-attempt strategy                         [1h]  → +0-2 solves
  → Expected: 22-32 solves (18-27%)

Week 3 (TTT / Self-Improvement):
  Tier 4A: Per-task LoRA fine-tuning                    [12h] → +5-10 solves
  Tier 4B: Cross-task retrieval for TTT                 [4h]  → +2-5 solves
  Tier 5A: Multi-model retry pipeline                   [4h]  → +2-3 solves
  → Expected: 30-45 solves (25-38%)

Week 4+ (Advanced):
  Tier 4C: SOAR self-improving loop                     [20h] → +5-15 solves
  Tier 5B: Transduction-guided synthesis                [4h]  → +1-3 solves
  Tier 5C: DSL-guided search                            [20h] → +3-8 solves
  → Expected: 35-55 solves (29-46%)
```

---

## Key References

### Papers

| Paper | Key Contribution | Link |
|-------|-----------------|------|
| Imbue: Beating ARC-AGI-2 with Code Evolution | Darwinian evolver, 34% open-weights | [imbue.com](https://imbue.com/research/2026-02-27-arc-agi-2-evolution/) |
| Jeremy Berman: NL Evolution | Natural language > Python for ARC | [substack](https://jeremyberman.substack.com/p/how-i-got-the-highest-score-on-arc-agi-again) |
| SOAR: Self-Improving LMs | Fine-tune on own search traces, 52% v1 | [arxiv 2507.14172](https://arxiv.org/abs/2507.14172) |
| NVARC: ARC-AGI-2 Technical Report | TTT + augmentation + LongT5 | [arxiv 2603.06590](https://arxiv.org/html/2603.06590) |
| TRM: Tiny Recursive Model | 7M params, 45% v1 | ARC Prize 2025 Paper Award 1st |
| CompressARC | 76K params, MDL + gradient descent | ARC Prize 2025 Paper Award 3rd |
| ARC Prize 2025 Results | Refinement loop meta-analysis | [arcprize.org](https://arcprize.org/blog/arc-prize-2025-results-analysis) |
| Lewis H: ARC-AGI 2025 Review | Comprehensive survey of approaches | [lewish.io](https://lewish.io/posts/arc-agi-2025-research-review) |
| ARC Prize 2024 Technical Report | TTT emergence, DSL vs DL | [arxiv 2412.04604](https://arxiv.org/pdf/2412.04604) |

### Open Source Repos

| Repo | What It Does |
|------|-------------|
| [imbue-ai/darwinian_evolver](https://github.com/imbue-ai/darwinian_evolver) | Imbue's code evolution framework |
| [flowersteam/SOAR](https://github.com/flowersteam/SOAR) | Self-improving evolutionary program synthesis |
| [fchollet/ARC-AGI](https://github.com/fchollet/ARC-AGI) | Official ARC-AGI dataset |
| [michaelhodel/re-arc](https://github.com/michaelhodel/re-arc) | Generators for ARC-AGI-1 training tasks |
| [xu3kev/BARC](https://github.com/xu3kev/BARC) | 200K synthetic ARC problems |
| [samacqua/LARC](https://github.com/samacqua/LARC) | Language-annotated ARC tasks |
| [poetiq-ai/poetiq-arc-agi-solver](https://github.com/poetiq-ai/poetiq-arc-agi-solver) | Poetiq's consensus solver |

### Datasets for Training/Fine-Tuning

| Dataset | Size | Use |
|---------|------|-----|
| ARC-AGI-2 training set | 1,000 tasks | Primary eval + TTT training |
| Re-ARC | Infinite (generators) | Data augmentation for TTT |
| BARC / ARC-Heavy | 200K tasks | Pre-training/fine-tuning data |
| Concept-ARC | 160 tasks (16 concept groups) | Concept-grouped evaluation |
| LARC | Language annotations for ARC | NL instruction training |

---

## Success Criteria

| Milestone | Score | Timeline |
|-----------|-------|----------|
| Wire existing modules | 15-20/120 (12-17%) | Week 1 |
| NL evolution working | 22-32/120 (18-27%) | Week 2 |
| TTT integrated | 30-45/120 (25-38%) | Week 3 |
| Match Imbue open-weights | 40+/120 (33%+) | Week 4+ |

---

*ARC-AGI Solver: Improvement Research V2*
*Copyright 2026 Alexandros Karales. All Rights Reserved.*
