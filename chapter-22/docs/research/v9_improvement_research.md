# V9 Improvement Research: From 83/120 to 95+/120

**Date:** 2026-03-29
**Current best:** V8 = 83/120 (69.2%), V3 = 90/120 (75.0%)
**Target:** 95+/120 (79%+)
**Approach:** Fix regressions first, then push frontier

---

## 1. Literature Review: State of the Art (ARC Prize 2025)

### 1.1 NVARC (1st Place, 24% on ARC-AGI-2)

**Key techniques:**
- **Synthetic data generation**: 260K puzzles from task combination (quadratic space of descriptions)
- **Consensus verification**: Generate 20 transformation implementations per task, keep only when ≥8/20 agree
- **Custom tokenizer**: Reduced to 16 tokens (10 colors + formatting), patched embedding table
- **D4 + color augmentation**: 8 geometric × factorial-10 color perms = massive augmentation pool
- **Augmentation levels**: 256 augmentations for known data, 24-32 for synthetic
- **Pass-at-128**: TRM achieves ~30% at pass-at-128, suggesting RL reranking could help

**Relevance to us:** Our D4 voting uses 8 candidates. NVARC uses 96-256 augmented versions at temp=0. We should increase our candidate count significantly.

### 1.2 ARChitects (2nd Place, ~53.5% on ARC-AGI-1)

**Key techniques:**
- **Token-level probability exploration**: Sample multiple token sequences above a fixed probability
- **Augmentation-based scoring**: "A correct solution should demonstrate greater stability in its sampling probability under augmented conditions compared to an incorrect one"
- **2D-aware masked diffusion LLM**: Non-autoregressive generation
- **Recursive self-refinement**: Iteratively improve predictions

**Relevance to us:** The stability principle is exactly what our D4 voting does, but ARChitects use it at the token level. We could weight candidates by cross-augmentation stability.

### 1.3 Omni-ARC (40% on ARC-AGI-1)

**Key techniques:**
- **96 augmented versions** at temperature=0
- **Per-task test-time fine-tuning** (leave-one-out from training pairs)
- **Majority voting** across all 96 reversed augmentations
- **Qwen model family** (same as ours)

**Relevance to us:** We use 8 D4 candidates. Omni-ARC uses 96. The gap explains much of our voting fragility. We need more candidates.

### 1.4 Jeremy Berman (ARC-Lang, Paper Award)

**Key techniques:**
- **Natural language program evolution**: Evolve English instructions (we already implement this)
- **Differential formatting**: Show what changed between predicted/expected grids
- **40 attempts per task**: Multiple retries with varied prompts

**Relevance to us:** Our diff_refiner implements Berman's differential formatting but hasn't produced solves. The issue may be that we compare against fresh predictions (we can't see ground truth) rather than training error analysis.

### 1.5 Eric Pang (SOAR, Efficient Evolutionary Program Synthesis)

**Key techniques:**
- **Self-improving evolutionary search**: Fine-tune LLM on its own search traces
- **Dynamic program abstraction library**: Build vocabulary from successful programs
- **10 attempts per task**: Most compute-efficient approach

**Relevance to us:** SOAR's self-improvement loop could recover tasks where code synthesis nearly works. Our 1/16 medium solve rate suggests we're not exploring the program space effectively.

### 1.6 Refinement Loop (2025 Theme)

The ARC Prize 2025 blog identifies **refinement loops** as the central innovation:
- **Explore** → generate many candidates
- **Verify** → analyze candidates with feedback signal
- **Repeat** per-task until refined

Our pipeline does this partially (D4 voting = explore, similarity = verify) but lacks true iterative refinement. We generate, vote once, and move on.

### 1.7 Iterative Grid Refinement (lewish.io review)

From the research review:
- Repeatedly apply a function over partial grids
- Provide partial outputs as context after step 0
- Explicitly ask the LLM to correct mistakes
- "Many ARC problems become much easier if you repeatedly apply some function"

This is exactly what our diff_refiner attempts, but our implementation doesn't leverage partial grid context effectively.

### 1.8 Object-Centric Representations

Multiple papers note that parsing grids into abstract objects before reasoning improves performance:
- One researcher claimed **doubling O1 performance** by mapping grids into object-centric representations
- Graph-based representations of grid objects enable structural reasoning
- The encoder → abstract representation → decoder pattern is common

Our pipeline works on raw grids. Object-centric parsing could help the LLM reason about spatial relationships.

---

## 2. Root Cause Analysis of Our V8 Gaps

### 2.1 The D4 Regression Problem (24 tasks lost vs V3)

**Root cause:** V4-V8 added modules that expanded the D4 voting pool:
- Phase GG: Symbolic filter (rejects candidates that violate priors) 
- Phase HH: Grid traversals (adds column/snake/diagonal candidates)
- Phase KK: Color permutations (adds 5 color-remapped candidates)

**Evidence:** V3 had pure 8-candidate D4 voting and solved 63 tasks via augmented transduction. V8's expanded pool dilutes votes and the symbolic filter over-rejects.

**Fix complexity:** LOW — restore pure D4 first, add extras only as fallback.

### 2.2 The Relaxed Transduction Threshold (5 tasks at 95-99%)

**Root cause:** Relaxed transduction requires ≥97% test similarity AND 100% training similarity. Five tasks achieve 95-99% test sim with perfect training — the threshold is too strict.

**Evidence:** 38007db0 (99.6%), 88e364bc (98.7%), 8b9c3697 (96.2%), a25697e4 (95.9%), 8f215267 (95.4%)

**Fix complexity:** TRIVIAL — lower threshold or add secondary acceptance criteria.

### 2.3 Diff Refinement Ineffectiveness (0 solves from 23 attempts)

**Root cause:** Our diff_refiner compares against fresh predictions (can't see ground truth), so the "diff" shows disagreement between two noisy outputs, not actual errors. This is circular — the LLM doesn't know which prediction is right.

**Better approach (from literature):** Use TRAINING pair diffs as the feedback signal. Show the LLM where it gets training pairs wrong and ask it to fix the test prediction based on those error patterns. This is grounded in actual errors, not speculation.

### 2.4 TTT Ineffectiveness (0 solves from 17 completions)

**Root cause:** Several potential issues:
1. LoRA rank 8 may be too low for 8B model
2. Leave-one-out augmentation creates too few training examples for some tasks
3. The fine-tuned model may need more inference attempts (we only try 1-2)
4. Ollama restart after TTT may not properly load the adapter

**Evidence from NVARC:** They use pass-at-128 with TRM and much larger augmentation pools. Our 1-2 inference attempts after TTT are far too few.

### 2.5 Code Synthesis Stagnation (1/33 solve rate)

**Root cause:** The code synthesis pipeline (Python generation → execution → evolution) only solves 1 medium-complexity task. The 8B model cannot generate correct Python programs for spatial transformations.

**Evidence:** 0/14 high-complexity tasks solved via any method.

**Fix:** Don't invest in code synthesis — invest in transduction quality. The literature confirms: transduction accounts for the vast majority of solves.

---

## 3. Technique Catalog: What Works for ARC

### 3.1 Voting Robustness Techniques

| Technique | Source | Expected Impact | Complexity |
|-----------|--------|-----------------|------------|
| **Pure D4 first, expanded pool second** | Our analysis | +10-15 regressions recovered | Low |
| **96-256 augmented versions** | Omni-ARC | +5-10 additional solves | Medium |
| **Stability-weighted voting** | ARChitects | +2-5 solves | Medium |
| **Cross-temperature consensus** | Our pass_at_k | +3-5 (already +6 in V8) | Done |
| **Training-pair accuracy weighting** | Novel | +2-3 solves | Low |

### 3.2 Near-Miss Recovery Techniques

| Technique | Source | Expected Impact | Complexity |
|-----------|--------|-----------------|------------|
| **Lower relaxed threshold to 95%** | Our analysis | +5 tasks directly | Trivial |
| **Post-relaxed cell fix** | Berman + our cell_fixer | +2-3 tasks | Low |
| **Training-error-guided refinement** | Berman/literature | +3-5 tasks | Medium |
| **Iterative partial-grid refinement** | lewish.io review | +2-4 tasks | Medium |
| **TTT with more inference attempts** | NVARC (pass-at-128) | +2-3 tasks | Low |

### 3.3 Frontier Expansion Techniques

| Technique | Source | Expected Impact | Complexity |
|-----------|--------|-----------------|------------|
| **Object-centric grid parsing** | Multiple papers | +3-5 hard tasks | High |
| **Synthetic ARC data fine-tuning** | NVARC | +10-20 tasks | Very High |
| **SOAR self-improvement** | Eric Pang | +3-5 tasks | High |
| **Larger model (32B)** | General | +5-10 tasks | Medium (VRAM) |
| **Custom 16-token tokenizer** | NVARC | +2-5 tasks (efficiency) | High |

### 3.4 Compute Efficiency Techniques

| Technique | Source | Expected Impact | Complexity |
|-----------|--------|-----------------|------------|
| **Early exit on high-agreement D4 vote** | Our V3 | Saves 30-60% time | Low |
| **Skip code synthesis when D4 sim < 50%** | Novel | Saves ~20min/task on hopeless cases | Trivial |
| **Batch LLM calls** | General | 2-3x throughput | Medium |

---

## 4. Priority Ranking: Impact vs Effort

### Tier 1: Quick Wins (1-2 days, +15-20 solves projected)

1. **Restore pure D4 voting** — run clean 8-candidate vote FIRST, accept at ≥80%
2. **Lower relaxed threshold** — accept at ≥95% when training sim = 100%
3. **Auto-accept relaxed at ≥99%** — trivially correct (one cell maybe wrong)
4. **Soften symbolic filter** — score-based instead of binary reject

### Tier 2: Medium Effort (3-5 days, +5-10 solves projected)

5. **Training-error-guided diff refinement** — rewrite diff_refiner to use training diffs as ground truth
6. **Weighted D4 voting** — weight candidates by training pair accuracy
7. **Post-relaxed cell fix** — run cell_fixer on relaxed transduction near-misses
8. **TTT pass-at-K** — generate 10+ predictions from fine-tuned model instead of 1-2

### Tier 3: Research (1-2 weeks, +5-10 solves projected)

9. **96-augmentation voting** — scale up from 8 to 96 augmented versions
10. **Object-centric grid representation** — parse grids into objects/graphs
11. **SOAR self-improvement loop** — fine-tune on own search traces

### Tier 4: Major Investment (2-4 weeks, +10-20 solves)

12. **Synthetic ARC data generation** — generate 100K+ synthetic puzzles
13. **Custom tokenizer** — reduce to 16 ARC-specific tokens
14. **Larger model** — test with 32B model for hard tasks

---

## 5. Key References

1. **NVARC solution**: https://github.com/1ytic/NVARC — Synthetic data + consensus verification
2. **ARChitects paper**: https://lambdalabsml.github.io/ARC2025_Solution_by_the_ARChitects/ — Token-level stability scoring
3. **Omni-ARC**: 96 augmentations at temp=0, per-task TTT, majority voting
4. **Jeremy Berman (ARC-Lang)**: NL program evolution + differential formatting
5. **Eric Pang (SOAR)**: Self-improving evolutionary synthesis
6. **Combining Induction and Transduction**: https://arxiv.org/abs/2411.02272 — BARC dataset, induction/transduction complementarity
7. **TRM (Tiny Recursive Model)**: 7M params, 45% on ARC-AGI-1 via recursive refinement
8. **CompressARC**: 76K params, MDL principle, zero-pretraining, 20% on ARC-AGI-1
9. **ARC Prize 2025 Results**: https://arcprize.org/blog/arc-prize-2025-results-analysis
10. **ARC-AGI Research Review**: https://lewish.io/posts/arc-agi-2025-research-review

---

## 6. Conclusion

The single highest-ROI action is **restoring pure D4 voting** to recover the 24 V3 regressions. Combined with lowering the relaxed threshold and softening the symbolic filter, this alone should push V9 from 83→95+ solves.

The 13 genuinely unsolved tasks (never solved by any version) require fundamentally different approaches — object-centric representations, synthetic data fine-tuning, or larger models. These are research-grade investments that should come after the quick wins are locked in.
