# V4 Evaluation Commands & Tests

**Date:** March 22, 2026  
**Branch:** `feature/arc-improvements-v3`  
**Baseline:** V3 = 90/120 (75.0%)  
**New Phases:** HH (traversals), KK (color perms), JJ (ensemble), II (evolution budget)

---

## 1. Verify Everything Is Green

```bash
# Full test suite — must be 1178 passed, 0 failed
cd /home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code
uv run pytest tests/ -q --tb=short
```

Expected: `1178 passed`

---

## 2. Verify Branch and Git Status

```bash
git branch --show-current
# Expected: feature/arc-improvements-v3

git status --short
# Expected: clean (nothing to commit)

git log --oneline -6
# Should show:
#   Phase II: Increase evolution budget
#   Phase JJ: Ensemble transduction + induction scoring
#   Phase KK: Color permutation augmentation
#   Phase HH: Grid traversal representations
#   (earlier commits)
```

---

## 3. Run Targeted Tests for New Modules

```bash
# Grid traversal (91 tests)
uv run pytest tests/test_grid_traversal.py -v --tb=short

# Color augmentation (28 tests)
uv run pytest tests/test_color_augmentor.py -v --tb=short

# Ensemble scoring (28 tests)
uv run pytest tests/test_ensemble.py -v --tb=short

# Augmentation voter (includes traversal + color perm wiring)
uv run pytest tests/test_augmentation_voter.py -v --tb=short

# Solver pipeline (includes ensemble + evolution budget changes)
uv run pytest tests/test_solve_improved.py -v --tb=short

# File size compliance (all modules under 500 lines)
uv run pytest tests/test_file_size.py -v --tb=short
```

---

## 4. Quick Smoke Test on a Single Task

```bash
# Test the full pipeline on one task to confirm nothing crashes
uv run python -c "
from loopagi.arc import load_default_datasets
from loopagi.arc.llm_bridge import create_llm_bridge
from loopagi.arc.solve_improved import solve_task_improved, ImprovedSolverConfig

ds = load_default_datasets(validate=False)
task = next(iter(ds['training'].tasks.values()))
bridge = create_llm_bridge(model='qwen3:8b')
config = ImprovedSolverConfig(enable_ttt=False)

result = solve_task_improved(task, bridge, config=config)
r = result['result']
print(f'Task: {r.task_id}')
print(f'Solved: {r.solved}')
print(f'Similarity: {r.best_similarity:.1%}')
print(f'Time: {r.total_seconds:.1f}s')
"
```

---

## 5. Run V4 Eval (Full 120-Task — No TTT)

This tests the impact of Phases HH+KK+JJ+II against the V3 baseline.  
**⚠️ CLOSE WINDSURF FIRST** — Ollama + eval + Windsurf > 16GB VRAM = crash.

### Recommended: Use the launcher script

```bash
# From a plain terminal (NOT Windsurf), close Windsurf first
cd /home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code
./chapter-22/run_v4_eval.sh
```

The script handles: VRAM check, timestamped logging, PID tracking, crash recovery (`--resume`), and summary file.

### Alternative: Raw command (single line for zsh)

```bash
nohup nice -n 10 uv run python chapter-22/run_eval_improved.py --no-few-shot --no-ttt --resume --output chapter-22/ARC_MODEL_REPORTS/eval_v4_nottt.json -v > eval_v4.log 2>&1 &
```

### Monitor Progress

```bash
# Watch the log
tail -f eval_v4.log

# Check how many tasks done
grep -c '"solved"' chapter-22/ARC_MODEL_REPORTS/eval_v4_nottt.json 2>/dev/null

# Quick summary (run periodically)
grep "SOLVED" eval_v4.log | wc -l
```

### Expected Results

| Metric | V3 Baseline | V4 Projected |
|--------|-------------|-------------|
| Solved | 90/120 (75.0%) | 96-105/120 (80-88%) |
| Avg similarity | 90.8% | 92-95% |
| Time per task | 487s | ~500-550s (more LLM calls) |
| Total time | 16.2h | ~17-18h |

---

## 6. Run V4 Eval on Near-Miss Tasks Only (Quick Validation)

If you want a faster check before the full eval (~1-2 hours):

```bash
# 10 near-miss tasks from V3 (90-99% similarity) — single line for zsh
uv run python chapter-22/run_eval_improved.py --no-few-shot --no-ttt --tasks 8e5c0c38,d59b0160,6e453dd6,7c66cb00,71e489b6,221dfab4,b9630600,0b17323b,e7639916,c1990cce --output chapter-22/ARC_MODEL_REPORTS/eval_v4_nearmiss.json -v 2>&1 | tee eval_v4_nearmiss.log
```

---

## 7. TTT Validation (REQUIRES Ollama Stopped + Windsurf Closed)

**Do NOT run this alongside the V4 eval or with Windsurf open.**

```bash
# Stop Ollama first
sudo systemctl stop ollama

# Close Windsurf / any GPU-heavy process

# Run TTT on a near-miss task
chapter-22/ttt_venv/bin/python chapter-22/ttt_train.py \
  --input /tmp/task.json \
  --output /tmp/pred.json \
  --steps 30

# Restart Ollama after
sudo systemctl start ollama
```

See `chapter-22/TTT_BEST_PRACTICES.md` for full VRAM safety guide.

---

## 8. Compare V4 vs V3 Results

After V4 eval completes:

```bash
# Count solves
echo "V3 solves:"
python -c "
import json
with open('chapter-22/ARC_MODEL_REPORTS/eval_v3_full.jsonl') as f:
    lines = [json.loads(l) for l in f]
solved = sum(1 for l in lines if l.get('solved'))
print(f'  {solved}/{len(lines)} ({solved/len(lines)*100:.1f}%)')
"

echo "V4 solves:"
python -c "
import json
with open('chapter-22/ARC_MODEL_REPORTS/eval_v4_nottt.json') as f:
    data = json.load(f)
results = data.get('results', data) if isinstance(data, dict) else data
solved = sum(1 for r in (results.values() if isinstance(results, dict) else results) if r.get('solved'))
total = len(results)
print(f'  {solved}/{total} ({solved/total*100:.1f}%)')
"
```

---

## 9. After Eval — Next Steps

- [ ] If V4 > V3: commit eval results, update book chapter
- [ ] If V4 ≈ V3: check logs for which phases helped, tune parameters
- [ ] Run TTT validation on 10 near-miss tasks (separate session)
- [ ] Merge to main when satisfied: `git checkout main && git merge feature/arc-improvements-v3`
- [ ] Update frozen branch: `git checkout book/v3-arc-reasoning && git merge main`

---

## Module Inventory (39 modules, 1178 tests)

| New Module | LOC | Tests | Phase |
|-----------|-----|-------|-------|
| `loopagi/arc/grid_traversal.py` | 410 | 91 | HH |
| `loopagi/arc/color_augmentor.py` | 247 | 28 | KK |
| `loopagi/arc/ensemble.py` | 335 | 28 | JJ |

| Modified Module | Change | Phase |
|----------------|--------|-------|
| `loopagi/arc/augmentation_voter.py` | +traversals +color perms in vote_transduction() | HH, KK |
| `loopagi/arc/solve_improved.py` | +ensemble wiring, +enable_ensemble config, evolution 10→12 | JJ, II |
| `tests/test_file_size.py` | Extended tier additions | HH, KK, JJ |
| `tests/test_solve_improved.py` | Updated evolution_budget default assertion | II |

---

*Copyright 2026 Alexandros Karales. All Rights Reserved.*
