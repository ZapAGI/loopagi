# V8 Regression Analysis: 24 Tasks Lost vs V3

**Date:** 2026-03-29
**V3:** 90/120 (75.0%) — branch `feature/arc-improvements-v2`, commit `8929afe`
**V8:** 83/120 (69.2%) — branch `feature/arc-improvements-v3`, commit `e093ba7`
**Net delta:** -7 (gained 17, lost 24)

---

## Executive Summary

V8 solves 83/120 tasks but **regresses on 24 tasks** that V3 solved. All 24 regressions were solved by `augmented_transduction` (D4 voting) in V3. The root cause is **LLM non-determinism in D4 voting** — these tasks are fragile to model state, Ollama version, and the accumulated pipeline changes between V3 and V8 (symbolic filtering, grid traversal, color permutations added to the voting pool).

V8 also **gains 17 new solves** that V3 missed, including 3 via the new multi-strategy voting and 12 via augmented transduction (different random winners). The net result is -7 overall.

---

## Regression Breakdown

### By V8 Fallback Method

| V8 Method | Count | Interpretation |
|-----------|-------|----------------|
| medium (code synthesis) | 9 | D4 failed, fell through to slow code path |
| high (evolution) | 8 | D4 failed, deep pipeline exhausted |
| relaxed_transduction | 5 | D4 failed, relaxed got close but not exact |
| low | 1 | D4 failed, trivial attempt |
| unknown | 1 | Pipeline error / edge case |

### By V8 Similarity Achieved

| Similarity Range | Count | Tasks |
|------------------|-------|-------|
| **95-100%** | 5 | 38007db0 (99.6%), 88e364bc (98.7%), 8b9c3697 (96.2%), 8f215267 (95.4%), a25697e4 (95.9%) |
| **90-95%** | 6 | 7b80bb43 (97.3%), b99e7126 (97.1%), c4d067a0 (94.7%), 7ed72f31 (94.4%), db695cfb (91.9%), 142ca369 (90.3%) |
| **85-90%** | 4 | 4a21e3da (89.2%), cbebaa4b (88.0%), 16de56c4 (87.9%), e12f9a14 (87.8%) |
| **70-85%** | 2 | e3721c99 (75.1%), de809cff (70.4%) |
| **<50%** | 5 | a32d8b75 (30.3%), edb79dae (30.6%), e87109e9 (26.8%), 898e7135 (6.6%), 8698868d (59.5%) |
| **0%** | 2 | 64efde09 (86.5%), 6e4f6532 (0.0%) |

**Key finding:** 11/24 regressions achieve ≥90% similarity in V8. These are near-misses that V3's D4 voting happened to nail but V8's expanded voting pool (with traversals, color perms, symbolic filter) misses.

### Statistics

- **Min similarity:** 0.0%
- **Max similarity:** 99.6%
- **Average similarity:** 74.6%
- **Near-miss (≥90%):** 11/24 (45.8%)

---

## Full Regression Table

| Task ID | V3 Method | V3 Sim | V3 Time | V8 Method | V8 Sim | V8 Time |
|---------|-----------|--------|---------|-----------|--------|---------|
| 142ca369 | augmented_transduction | 100% | 282s | medium | 90.3% | 2148s |
| 16de56c4 | augmented_transduction | 100% | 138s | medium | 87.9% | 872s |
| 38007db0 | augmented_transduction | 100% | 233s | relaxed_transduction | 99.6% | 1076s |
| 4a21e3da | augmented_transduction | 100% | 256s | low | 89.2% | 1600s |
| 64efde09 | augmented_transduction | 100% | 330s | high | 86.5% | 3091s |
| 6e4f6532 | augmented_transduction | 100% | — | unknown | 0.0% | 1343s |
| 7b80bb43 | augmented_transduction | 100% | — | medium | 97.3% | 1696s |
| 7ed72f31 | augmented_transduction | 100% | — | medium | 94.4% | 2194s |
| 8698868d | augmented_transduction | 100% | — | high | 59.5% | 1615s |
| 88e364bc | augmented_transduction | 100% | 285s | relaxed_transduction | 98.7% | 2465s |
| 898e7135 | augmented_transduction | 100% | 309s | high | 6.6% | 1332s |
| 8b9c3697 | augmented_transduction | 100% | 264s | relaxed_transduction | 96.2% | 1816s |
| 8f215267 | augmented_transduction | 100% | 282s | relaxed_transduction | 95.4% | 2321s |
| a25697e4 | augmented_transduction | 100% | 467s | relaxed_transduction | 95.9% | 2136s |
| a32d8b75 | augmented_transduction | 100% | 488s | high | 30.3% | 1714s |
| b99e7126 | augmented_transduction | 100% | 453s | medium | 97.1% | 1884s |
| c4d067a0 | augmented_transduction | 100% | 335s | medium | 94.7% | 2538s |
| cbebaa4b | augmented_transduction | 100% | 398s | high | 88.0% | 2500s |
| db695cfb | augmented_transduction | 100% | 206s | medium | 91.9% | 1470s |
| de809cff | augmented_transduction | 100% | 335s | medium | 70.4% | 1480s |
| e12f9a14 | augmented_transduction | 100% | 413s | medium | 87.8% | 2918s |
| e3721c99 | augmented_transduction | 100% | 582s | high | 75.1% | 2047s |
| e87109e9 | augmented_transduction | 100% | 346s | high | 26.8% | 1582s |
| edb79dae | augmented_transduction | 100% | 295s | high | 30.6% | 1594s |

---

## Root Cause Analysis

### 1. D4 Voting Pool Dilution (Primary Cause)

V3 used a clean 8-candidate D4 voting pool (identity + 7 D4 transforms). V8 added:
- Grid traversal candidates (column, snake, diagonal)
- Color permutation candidates (5 color-remapped variants)
- Symbolic filtering (rejects candidates that violate priors)

**Hypothesis:** The expanded pool introduces noise that dilutes correct votes. In V3, if 5/8 D4 candidates agreed on the correct answer, the vote passed at 80% agreement. In V8, with 20+ candidates from mixed strategies, it's easier for noisy candidates to split the vote below threshold.

### 2. LLM Non-Determinism (Contributing)

The Ollama model (`qwen3:8b`) with `think=False` produces slightly different outputs across runs due to:
- GPU floating-point non-determinism
- Model weight loading order
- Context window filling differently with longer prompts (traversal encodings are longer)

V3 and V8 used the same model but **different prompt formats** for the added augmentations.

### 3. Symbolic Filter Over-Rejection

The symbolic filter (`symbolic_filter.py`) may reject correct D4 candidates that happen to violate a color or size prior extracted from training pairs. This is especially problematic for tasks where the transformation is non-obvious.

**Evidence:** Multi-strategy voting in V8 logged "0 valid, 20 filtered" for several tasks — the filter rejected ALL candidates, preventing any vote.

### 4. Pipeline Order Effects

V8 runs multi-strategy voting AFTER standard D4 voting. If D4 voting fails (lower agreement), the pipeline falls through. But multi-strategy voting generates its OWN D4 candidates (different from the first run) — the second D4 run may not reproduce the first.

---

## Recovery Opportunities

### Tier 1: Near-Misses (≥95% sim) — 5 tasks

These are **one or two wrong cells** away from correct. Recovery approaches:
- **Lower D4 voting threshold** from 80% to 75% for these specific tasks
- **Relaxed transduction auto-accept** when training sim is 100% AND test sim ≥ 99%
- **Cell-level diff correction** (Phase RR) should handle these but didn't fire effectively

### Tier 2: High Similarity (90-95%) — 6 tasks

These need better voting or refinement:
- **Weighted voting** (weight D4 candidates by training pair accuracy)
- **Second-chance D4** at different temperature
- **Better symbolic filter** (softer rejection, scoring instead of binary)

### Tier 3: Medium Similarity (80-90%) — 4 tasks

These may need fundamentally different approaches:
- **Object-centric representation** (parse grids into objects before transduction)
- **Iterative refinement** with explicit error feedback

### Tier 4: Low Similarity (<80%) — 9 tasks

These are tasks where D4 voting completely fails. Recovery requires:
- **Different model** or **longer context** (these may be too complex for 8B model)
- **SOAR-style self-improving loop** (train on own failures)
- **Test-time training** with longer training (V8 TTT didn't recover any of these)

---

## Recommendations for V9

1. **Restore V3 voting purity**: Run a CLEAN 8-candidate D4 vote (no traversals, no color perms) FIRST, accept if agreement ≥ 80%. Only add extra candidates if the clean vote fails.
2. **Soften symbolic filter**: Change from binary reject to scoring — penalize but don't eliminate candidates that violate one prior.
3. **Lower relaxed threshold**: Accept relaxed transduction when test sim ≥ 99% AND training sim = 100% (would recover `38007db0` at 99.6%).
4. **Retry D4 at different temperature**: If first D4 vote fails, retry at temp=0.1 before falling through.
5. **Weighted candidate voting**: Weight D4 candidates by how well they predicted training pairs.
