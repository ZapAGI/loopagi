# V9 Implementation Plan

**Date:** 2026-03-29
**Current:** V8 = 83/120 (69.2%)
**Target:** 95+/120 (79%+)
**Branch:** `feature/arc-improvements-v3` (continue from V8 commit `e093ba7`)
**Estimated effort:** 3-5 days for Tier 1+2, 1-2 weeks for Tier 3

---

## Strategy Overview

V9 focuses on **regression recovery** (24 tasks lost vs V3) and **near-miss completion** (13 tasks at ≥90% sim). These 37 tasks represent the highest-ROI targets. The 13 genuinely unsolved tasks are deprioritized — they require research-grade investment for marginal gains.

### Projected Impact

| Phase | Tasks Recovered | Cumulative | % |
|-------|----------------|------------|---|
| V8 baseline | 83 | 83/120 | 69.2% |
| Phase A: Pure D4 restore | +10-15 | 93-98 | 77-82% |
| Phase B: Relaxed threshold | +5 | 98-103 | 82-86% |
| Phase C: Soft symbolic filter | +2-3 | 100-106 | 83-88% |
| Phase D: Post-relaxed cell fix | +2-3 | 102-109 | 85-91% |
| Phase E: Training-guided refinement | +2-3 | 104-112 | 87-93% |
| Phase F: TTT pass-at-K | +1-2 | 105-114 | 88-95% |

---

## Phase A: Restore Pure D4 Voting (HIGH PRIORITY)

**Goal:** Recover 10-15 D4 regression tasks by running a clean 8-candidate vote before the expanded pool.

### Root Cause

V4-V8 added grid traversal, color permutation, and symbolic filter candidates to the D4 voting pool. This dilutes correct votes and causes fragile tasks to fail.

### Implementation

**File:** `loopagi/arc/augmentation_voter.py`

**Change 1:** Add `pure_d4_first` flag to `vote_transduction()`:

```python
def vote_transduction(
    bridge, train_pairs, test_input,
    agreement_threshold=0.80,
    pure_d4_first=True,        # NEW: try clean D4 before expanded pool
    ...
):
    # Phase 1: Pure D4 vote (8 candidates only — identity + 7 D4 transforms)
    if pure_d4_first:
        d4_grids = []
        for aug in _get_d4_augmentations():  # Only D4, no traversals/colors
            aug_pairs = [(aug.forward(i), aug.forward(o)) for i, o in train_pairs]
            aug_test = aug.forward(test_input)
            result = transduce(bridge, aug_pairs, aug_test, temperature=0.0)
            if result.predicted_grid is not None:
                d4_grids.append(aug.reverse(result.predicted_grid))
        
        if len(d4_grids) >= 4:
            agreement = _compute_agreement(d4_grids)
            if agreement >= agreement_threshold:
                voted = _majority_vote_grid(d4_grids)
                return voted, agreement  # Accept pure D4 result
    
    # Phase 2: Fall through to expanded pool (traversals + color perms)
    # ... existing code ...
```

**Change 2:** Extract `_get_d4_augmentations()` that returns ONLY the 8 D4 transforms (no traversals, no color perms).

**Change 3:** In `try_augmented_transduction()`, pass `pure_d4_first=True`.

### Testing

- Unit test: `test_pure_d4_vote_accepts_when_agreement_high()`
- Unit test: `test_pure_d4_falls_through_when_agreement_low()`
- Integration: Run on 5 known regression tasks to verify recovery

### Validation

Run a targeted eval on the 24 regression task IDs:
```bash
uv run python chapter-22/run_eval_improved.py \
    --tasks 142ca369,16de56c4,38007db0,4a21e3da,64efde09,6e4f6532,7b80bb43,7ed72f31,8698868d,88e364bc,898e7135,8b9c3697,8f215267,a25697e4,a32d8b75,b99e7126,c4d067a0,cbebaa4b,db695cfb,de809cff,e12f9a14,e3721c99,e87109e9,edb79dae \
    --no-few-shot --output chapter-22/ARC_MODEL_REPORTS/eval_v9a_regressions.json -v
```

---

## Phase B: Lower Relaxed Transduction Threshold (HIGH PRIORITY)

**Goal:** Recover 5 tasks at 95-99% similarity that pass training verification.

### Implementation

**File:** `loopagi/arc/solve_improved.py`

**Change 1:** Add tiered relaxed acceptance:

```python
# In _try_relaxed_transduction():
# Tier 1: Accept if test sim >= 99% (almost certainly correct)
if test_similarity >= 0.99 and training_sim >= 1.0:
    result.solved = True
    return result

# Tier 2: Accept if test sim >= 95% AND training sim == 100%
if test_similarity >= 0.95 and training_sim >= 1.0:
    result.solved = True
    return result

# Tier 3: Existing threshold (97%)
if test_similarity >= config.relaxed_transduction_threshold:
    # ... existing logic ...
```

**Change 2:** Add `relaxed_auto_accept_threshold` to `ImprovedSolverConfig` (default: 0.95).

### Target Tasks

| Task ID | Current Sim | Expected Recovery |
|---------|-------------|-------------------|
| 38007db0 | 99.6% | ✅ Auto-accept (≥99%) |
| 88e364bc | 98.7% | ✅ Accept (≥95%, train=100%) |
| 8b9c3697 | 96.2% | ✅ Accept (≥95%, train=100%) |
| a25697e4 | 95.9% | ✅ Accept (≥95%, train=100%) |
| 8f215267 | 95.4% | ✅ Accept (≥95%, train=100%) |

### Testing

- Unit test: `test_relaxed_auto_accepts_at_99_percent()`
- Unit test: `test_relaxed_accepts_at_95_with_perfect_training()`
- Unit test: `test_relaxed_rejects_at_95_without_perfect_training()`

---

## Phase C: Soften Symbolic Filter (MEDIUM PRIORITY)

**Goal:** Prevent over-rejection of valid candidates in D4 voting and multi-strategy voting.

### Root Cause

The symbolic filter (`symbolic_filter.py`) uses binary accept/reject. Evidence from V8 logs shows "0 valid, 20 filtered" on multiple tasks — ALL candidates rejected, preventing any vote.

### Implementation

**File:** `loopagi/arc/symbolic_filter.py`

**Change:** Replace `filter_candidate() -> bool` with `score_candidate() -> float`:

```python
def score_candidate(candidate, test_input, priors):
    """Score candidate 0.0-1.0 based on structural priors.
    
    Returns 1.0 if all priors satisfied, penalizes but doesn't
    reject for single violations.
    """
    score = 1.0
    violations = 0
    
    # Color prior: candidate uses only colors from training
    if not _check_color_prior(candidate, priors):
        score -= 0.3
        violations += 1
    
    # Size prior: output dimensions match pattern
    if not _check_size_prior(candidate, test_input, priors):
        score -= 0.4
        violations += 1
    
    # Inclusion prior: background color dominance
    if not _check_inclusion_prior(candidate, priors):
        score -= 0.2
        violations += 1
    
    return max(0.0, score)
```

**File:** `loopagi/arc/augmentation_voter.py` and `loopagi/arc/pass_at_k.py`

**Change:** Use `score_candidate()` to weight votes instead of binary filtering:

```python
# Weight each candidate's vote by its symbolic score
for cand in candidates:
    weight = score_candidate(cand.grid, test_input, priors)
    if weight > 0.3:  # Minimum score to participate in vote
        weighted_grids.append((cand.grid, weight))
```

### Testing

- Unit test: `test_score_candidate_all_priors_satisfied()`
- Unit test: `test_score_candidate_partial_violation()`
- Unit test: `test_weighted_voting_prefers_high_score_candidates()`

---

## Phase D: Post-Relaxed Cell Fix (MEDIUM PRIORITY)

**Goal:** Fix 1-5 wrong cells in relaxed transduction outputs that are 95-99% correct.

### Implementation

**File:** `loopagi/arc/solve_improved.py`

**Change:** After relaxed transduction returns a near-miss (not solved but sim ≥ 95%), run cell_fixer:

```python
# After relaxed transduction
if relaxed is not None and not relaxed["result"].solved:
    if relaxed["result"].best_similarity >= 0.95:
        from loopagi.arc.cell_fixer import fix_cells
        # Try fixing the few wrong cells
        fixed = fix_cells(bridge, train_pairs, test_input, 
                         relaxed_prediction, wrong_cells)
        if fixed is not None:
            # Verify fix on training pairs
            ...
```

**File:** `loopagi/arc/cell_fixer.py`

**Change:** Add `fix_transduction_output()` function that works on transduction predictions (not just code synthesis outputs).

### Testing

- Unit test: `test_cell_fix_on_relaxed_near_miss()`
- Integration: Run on 38007db0 (99.6% — should fix 1-2 cells)

---

## Phase E: Training-Guided Diff Refinement (MEDIUM PRIORITY)

**Goal:** Rewrite diff_refiner to use training errors as ground truth signal.

### Root Cause

V8's diff_refiner compares test prediction against a fresh prediction — this is circular because neither prediction is known to be correct. The LLM can't determine which is right.

### New Approach

Instead of diffing two test predictions, **diff against training pairs** where we know the ground truth:

1. Run transduction on each training input → get predictions
2. Diff predictions against actual training outputs → identify systematic error patterns
3. Show these error patterns to the LLM
4. Ask: "Based on these errors, fix the test prediction"

### Implementation

**File:** `loopagi/arc/diff_refiner.py`

**Change:** Rewrite `refine_with_diff()`:

```python
def refine_with_diff(bridge, train_pairs, test_input, prediction):
    # Step 1: Identify training errors
    training_errors = []
    for inp, expected_out in train_pairs:
        predicted = transduce(bridge, train_pairs, inp, temperature=0.0)
        if predicted.predicted_grid is not None:
            diff = compute_grid_diff(expected_out, predicted.predicted_grid)
            if diff.n_wrong > 0:
                training_errors.append({
                    "input": inp,
                    "expected": expected_out,
                    "predicted": predicted.predicted_grid,
                    "diff": diff,
                })
    
    if not training_errors:
        return prediction  # No training errors to learn from
    
    # Step 2: Format error analysis
    error_text = format_training_error_analysis(training_errors)
    
    # Step 3: Ask LLM to fix test prediction based on training errors
    prompt = TRAINING_GUIDED_REFINE_PROMPT.format(
        pairs=format_pairs(train_pairs),
        training_errors=error_text,
        test_input=compact_grid(test_input),
        prediction=compact_grid(prediction),
    )
    
    response = bridge.call(prompt, temperature=0.0)
    refined = parse_grid_from_response(response)
    return refined if refined is not None else prediction
```

### Testing

- Unit test: `test_training_error_analysis_identifies_systematic_errors()`
- Unit test: `test_refine_uses_training_errors_not_fresh_predictions()`

---

## Phase F: TTT Pass-at-K (LOW PRIORITY)

**Goal:** Generate 10+ predictions from TTT fine-tuned model instead of 1-2.

### Root Cause

NVARC achieves pass-at-128 accuracy of ~30% (vs pass-at-1 of ~10%). Our TTT generates only 1-2 predictions, missing opportunities.

### Implementation

**File:** `chapter-22/ttt_train.py`

**Change:** Add `--num-predictions` argument (default: 10), generate multiple outputs at varied temperatures:

```python
temperatures = [0.0, 0.1, 0.2, 0.3, 0.5]
predictions = []
for temp in temperatures:
    for _ in range(num_per_temp):
        pred = model.generate(test_input, temperature=temp)
        predictions.append(pred)
```

**File:** `loopagi/arc/ttt.py`

**Change:** After TTT generates multiple predictions, run majority voting:

```python
# Vote across TTT predictions
from loopagi.arc.pass_at_k import _majority_vote
voted = _majority_vote(ttt_predictions)
```

### Testing

- Unit test: `test_ttt_generates_multiple_predictions()`
- Integration: Run on 3 TTT candidate tasks

---

## Execution Order

```
Week 1 (Days 1-3):
  ├── Phase A: Restore pure D4 voting
  ├── Phase B: Lower relaxed threshold
  ├── Run targeted eval on 24 regression tasks
  └── Run targeted eval on 5 relaxed tasks

Week 1 (Days 4-5):
  ├── Phase C: Soften symbolic filter
  ├── Phase D: Post-relaxed cell fix
  └── Run full 120-task V9 eval

Week 2 (Days 6-8):
  ├── Phase E: Training-guided diff refinement
  ├── Phase F: TTT pass-at-K
  └── Run full 120-task V9b eval (all phases)
```

---

## Success Criteria

| Metric | V8 | V9 Target | Stretch |
|--------|-----|-----------|---------|
| Solved | 83/120 | 95/120 | 100/120 |
| Solve rate | 69.2% | 79.2% | 83.3% |
| Regressions vs V3 | 24 | ≤5 | 0 |
| Near-miss (≥90%) unsolved | 13 | ≤4 | 0 |
| Total time | 26.9h | ≤20h | ≤16h |
| TTT solves | 0 | ≥2 | ≥5 |

---

## Risk Mitigation

1. **Phase A may not recover all regressions:** D4 voting is inherently non-deterministic. We may recover 10-15/24 but not all. Mitigation: multi-strategy voting as fallback (already in V8).

2. **Lowering relaxed threshold may introduce false positives:** A 95% match could have 5% wrong cells. Mitigation: only accept when training sim = 100% (model truly understands the pattern).

3. **Symbolic filter softening may reduce precision:** Weaker filtering allows more noise into the vote. Mitigation: use scoring to weight, not to include/exclude.

4. **LLM version drift:** Ollama updates or model reloads can change outputs. Mitigation: pin Ollama version, document model hash.

---

## Files to Modify

| File | Phase | Changes |
|------|-------|---------|
| `loopagi/arc/augmentation_voter.py` | A, C | Pure D4 first, weighted voting |
| `loopagi/arc/solve_improved.py` | B, D | Relaxed threshold tiers, post-relaxed cell fix |
| `loopagi/arc/symbolic_filter.py` | C | `score_candidate()` replacing `filter_candidate()` |
| `loopagi/arc/pass_at_k.py` | C | Weighted voting instead of binary filter |
| `loopagi/arc/diff_refiner.py` | E | Training-guided refinement rewrite |
| `loopagi/arc/cell_fixer.py` | D | `fix_transduction_output()` |
| `loopagi/arc/ttt.py` | F | Pass-at-K predictions |
| `chapter-22/ttt_train.py` | F | Multiple prediction generation |
| `chapter-22/run_eval_improved.py` | All | New CLI flags |
| `tests/test_augmentation_voter.py` | A | Pure D4 tests |
| `tests/test_symbolic_filter.py` | C | Scoring tests |
| `tests/test_diff_refiner.py` | E | Training-guided tests |
| `tests/test_ttt.py` | F | Pass-at-K tests |

---

## Quick Reference: Task IDs by Recovery Phase

**Phase A targets (D4 regressions):**
`142ca369`, `16de56c4`, `4a21e3da`, `64efde09`, `6e4f6532`, `7b80bb43`, `7ed72f31`, `8698868d`, `898e7135`, `a32d8b75`, `b99e7126`, `c4d067a0`, `cbebaa4b`, `db695cfb`, `de809cff`, `e12f9a14`, `e3721c99`, `e87109e9`, `edb79dae`

**Phase B targets (relaxed near-misses):**
`38007db0`, `88e364bc`, `8b9c3697`, `a25697e4`, `8f215267`

**Phase D targets (cell fix candidates):**
`7b80bb43` (97.3%), `b99e7126` (97.1%), `c4d067a0` (94.7%), `7ed72f31` (94.4%)

**Phase E targets (diff refinement candidates):**
`8b7bacbf` (94.9%), `62593bfd` (90.8%), `4c416de3` (87.9%), `195c6913` (87.2%)
