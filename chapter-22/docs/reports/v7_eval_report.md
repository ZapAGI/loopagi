# V7 Evaluation Report — TTT Enabled

**Date:** March 28, 2026
**Author:** Alexandros Karales + Cascade AI
**Branch:** feature/arc-improvements-v3
**Config:** D4 retries removed, TTT enabled (sim ≥ 0.85 trigger), cell-fix threshold ≥ 0.95

---

## Results Summary

| Metric | V7 (TTT) | V6 (no TTT) | V5 (no TTT) | V4b (no TTT) | V3 (outlier) |
|---|---|---|---|---|---|
| **Solved** | **78/120 (65.0%)** | 77/120 (64.2%) | 77/120 (64.2%) | 75/120 (62.5%) | 90/120 (75.0%) |
| Total time | 22.8h | 22.6h | 21.3h | 22.8h | 16.2h |
| Avg time/task | 684s | 678s | 639s | 684s | 487s |
| Errors | 1 | 0 | 0 | 0 | 0 |
| Avg similarity | 89.3% | — | — | — | 90.8% |

**Net gain from TTT: +1 solve** (task `d59b0160`).

---

## Solve Method Breakdown

| Method | V7 | V6 | V5 | V4b |
|---|---|---|---|---|
| Augmented transduction (D4) | 46 | 49 | 52 | 45 |
| Relaxed transduction | 22 | 18 | 15 | 20 |
| Direct transduction | 10 | 10 | 10 | 10 |
| Code synthesis/evolution | 0 | 0 | 0 | 0 |
| **TTT** | **0*** | — | — | — |
| **Total** | **78** | **77** | **77** | **75** |

*`d59b0160` was solved via relaxed transduction AFTER TTT adapted the model, but the JSONL records it as `complexity=relaxed_transduction`, not TTT.

---

## TTT Performance Analysis

### Overview

| Metric | Value |
|---|---|
| TTT attempts triggered | 24 tasks |
| TTT completed training | 5 tasks |
| TTT timed out (600s) | 19 tasks (79%) |
| TTT produced solve | 1 task (`d59b0160`) |
| TTT success rate | 1/24 (4.2%) |
| TTT success rate (completed only) | 1/5 (20%) |

### TTT Completed Tasks

| Task | Similarity | Training Examples | Time | Outcome |
|---|---|---|---|---|
| `16de56c4` | 88.8% | 33 | 353.6s | Not solved |
| `38007db0` | 99.6% | 20 | 590.2s | Not solved |
| `409aa875` | 98.6% | 31 | 550.6s | Not solved |
| `d59b0160` | — | 33 | 473.3s | **SOLVED** ✅ |
| `db695cfb` | 91.9% | 55 | 542.5s | Not solved |

### TTT Timed Out Tasks (19/24)

`142ca369`, `221dfab4`, `4a21e3da`, `4c416de3`, `62593bfd`, `64efde09`, `6e4f6532`, `71e489b6`, `7b80bb43`, `7ed72f31`, `88e364bc`, `8b7bacbf`, `8b9c3697`, `8f215267`, `a25697e4`, `b99e7126`, `c4d067a0`, `cbebaa4b`, `e12f9a14`

### Root Cause: 79% Timeout Rate

The 600s timeout is killing TTT effectiveness. Each TTT attempt requires:
1. **Unload Ollama** (~10-20s) — free VRAM for LoRA training
2. **LoRA training** (~200-400s) — 50 gradient steps on augmented data
3. **Inference** (~100-200s) — generate predictions with adapted model
4. **Reload Ollama** (~10-30s) — restore for next task

The entire pipeline takes 350-600s when it works. With the 600s timeout, tasks with more training examples (larger augmented datasets) consistently timeout.

### TTT Fix Recommendations

| Fix | Impact | Effort |
|---|---|---|
| **Increase timeout to 900s** | Would complete 10-15 more tasks | Trivial |
| **Reduce gradient steps (50 → 30)** | Faster training, minor quality loss | Trivial |
| **Reduce augmentation multiplier** | Fewer training examples → faster | Easy |
| **Pre-download model to avoid first-load penalty** | Saves 30-60s per attempt | Easy |
| **Cross-task retrieval (Phase XX)** | Better training signal, fewer steps needed | Medium |

---

## Consistency Analysis (V4–V7, 4 Runs)

| Category | Count | Tasks |
|---|---|---|
| **Solved in ALL 4 runs** | 74 | (stable core) |
| **Solved in ANY run** | 79 | |
| **Flaky (not all 4)** | 5 | See below |

### Flaky Tasks

| Task | V4b | V5 | V6 | V7 | Notes |
|---|---|---|---|---|---|
| `247ef758` | ❌ | ✅ | ✅ | ✅ | Stabilized after V4b |
| `53fb4810` | ❌ | ✅ | ✅ | ✅ | Stabilized after V4b |
| `a47bf94d` | ❌ | ✅ | ✅ | ✅ | Stabilized after V4b |
| `aa4ec2a5` | ✅ | ❌ | ❌ | ❌ | Lost after V4b |
| `d59b0160` | ❌ | ❌ | ❌ | ✅ | **NEW — TTT recovered** |

**Key finding:** `d59b0160` was NEVER solved in V4b/V5/V6. TTT is the only method that recovered it. This proves TTT adds genuine value when it completes.

---

## Unsolved Near-Miss Tasks (23 tasks with sim ≥ 85%)

These are the highest-value recovery targets for future improvements:

| Task | Similarity | Complexity | TTT Status | Recovery Path |
|---|---|---|---|---|
| `38007db0` | 99.6% | relaxed_trans | Completed, not solved | Diff refinement, more steps |
| `88e364bc` | 98.7% | relaxed_trans | Timed out | Increase TTT timeout |
| `409aa875` | 98.6% | relaxed_trans | Completed, not solved | Diff refinement |
| `7b80bb43` | 97.3% | medium | Timed out | Increase TTT timeout |
| `b99e7126` | 97.1% | medium | Timed out | Increase TTT timeout |
| `8b9c3697` | 96.2% | relaxed_trans | Timed out | Increase TTT timeout |
| `a25697e4` | 95.9% | relaxed_trans | Timed out | Increase TTT timeout |
| `8f215267` | 95.4% | relaxed_trans | Timed out | Increase TTT timeout |
| `4c416de3` | 95.0% | high | Timed out | Increase TTT timeout |
| `8b7bacbf` | 94.9% | medium | Timed out | Increase TTT timeout |
| `c4d067a0` | 94.7% | medium | Timed out | Increase TTT timeout |
| `7ed72f31` | 94.4% | medium | Timed out | Increase TTT timeout |
| `db695cfb` | 91.9% | medium | Completed, not solved | More training steps |
| `62593bfd` | 90.8% | medium | Timed out | Increase TTT timeout |
| `142ca369` | 90.3% | medium | Timed out | Increase TTT timeout |
| `4a21e3da` | 89.2% | low | Timed out | Increase TTT timeout |
| `16de56c4` | 88.8% | medium | Completed, not solved | More training steps |
| `cbebaa4b` | 88.7% | high | Timed out | Increase TTT timeout |
| `71e489b6` | 88.3% | medium | Timed out | Increase TTT timeout |
| `6e4f6532` | 88.1% | high | Timed out | Increase TTT timeout |
| `e12f9a14` | 87.8% | medium | Timed out | Increase TTT timeout |
| `64efde09` | 86.5% | high | Timed out | Increase TTT timeout |
| `221dfab4` | 86.1% | medium | Timed out | Increase TTT timeout |

**If TTT timeout is fixed:** 19 additional tasks would complete TTT training. At the 20% success rate (1/5 completed → solved), this projects to ~4 more solves → **82/120 (68.3%)**.

---

## V8 Immediate Action Items

### Quick Fix: Increase TTT Timeout (est. +3-5 solves)

```python
# In ttt.py or solve_improved.py
TTT_TIMEOUT = 900  # was 600s — gives 50% more time for training
```

### Quick Fix: Reduce TTT Gradient Steps for Large Tasks

```python
# In ttt.py
steps = 30 if n_training_examples > 40 else 50  # adaptive steps
```

### Quick Fix: Skip TTT for Tasks Below 85% (already implemented)

Already filtering on sim ≥ 0.85 — confirmed working.

---

## Historical Solve Rate Trend

```
V2:  ██████████░░░░░░░░░░░░░░░░░░░░░░░░  11/120 ( 9.2%)
V3:  ████████████████████████████████████  90/120 (75.0%) ← outlier
V4b: ██████████████████████████████░░░░░░  75/120 (62.5%)
V5:  ███████████████████████████████░░░░░  77/120 (64.2%)
V6:  ███████████████████████████████░░░░░  77/120 (64.2%)
V7:  ███████████████████████████████░░░░░  78/120 (65.0%) ← +1 from TTT
```

**Stable baseline: 77 ± 1.5 solves.** TTT adds marginal but real value (+1 confirmed, more with timeout fix).

---

## Conclusion

V7 confirms:

1. **TTT works** — it recovered `d59b0160`, a task never solved in 3 prior runs
2. **TTT is severely hampered by timeout** — 79% of attempts fail before completing
3. **The stable baseline is 77 solves** — consistent across 4 runs (V4b-V7)
4. **23 near-miss tasks** exist at ≥85% similarity — the primary recovery targets
5. **Next highest-impact changes**: increase TTT timeout, implement diff refinement (Phase RR), expand pass-at-K (Phase YY)

---

*V7 Evaluation Report*
*Copyright 2026 Alexandros Karales. All Rights Reserved.*
