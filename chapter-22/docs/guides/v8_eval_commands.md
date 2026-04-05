# V8 Eval Commands & Guide

## Quick Start

```bash
# Close Windsurf first! TTT needs GPU VRAM.
cd /home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code
chmod +x chapter-22/run_v8_eval.sh
./chapter-22/run_v8_eval.sh
```

## What's New in V8

| Feature | Phase | Description | Expected Impact |
|---------|-------|-------------|-----------------|
| Multi-strategy voting | FF | Pass-at-K with D4+temp+retry candidates (~20/test) | +3-5 solves |
| Diff-based refinement | RR | ASCII diff feedback for near-miss correction | +2-4 solves |
| TTT timeout fix | EE | 600s→900s, adaptive gradient steps | +2-3 solves |

### Pipeline Order (V8)

```
1. Strict transduction (3 temps)
2. Refined transduction (Phase Y)
3. D4 augmented voting (Phase CC3, agreement ≥ 0.80)
4. Multi-strategy voting (Phase FF, agreement ≥ 0.70)  ← NEW
5. Relaxed transduction (≥ 0.97, then ≥ 0.90)
6. Code synthesis + sampling
7. Evolution (AST + LLM)
8. Cell fix
9. NL evolution
10. Diff-based refinement (Phase RR, sim ≥ 0.85)  ← NEW
11. TTT (LoRA, timeout=900s, adaptive steps)  ← IMPROVED
```

## Monitoring

```bash
# Live log
tail -f chapter-22/eval_v8.log

# Summary
cat chapter-22/eval_v8_summary.txt

# Count solves
grep -c SOLVED chapter-22/eval_v8.log

# V8-specific activity
grep 'Pass-at-K\|multi_strategy\|Multi-strategy' chapter-22/eval_v8.log | tail -20
grep 'Diff refiner' chapter-22/eval_v8.log | tail -20
grep 'TTT:' chapter-22/eval_v8.log | tail -20

# JSONL progress
wc -l < chapter-22/ARC_MODEL_REPORTS/eval_v8_full.jsonl

# GPU usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
```

## Output Files

| File | Description |
|------|-------------|
| `chapter-22/eval_v8.log` | Full timestamped log |
| `chapter-22/eval_v8_summary.txt` | Status summary |
| `chapter-22/eval_v8.pid` | PID file (auto-removed on completion) |
| `chapter-22/ARC_MODEL_REPORTS/eval_v8_full.json` | Final JSON results |
| `chapter-22/ARC_MODEL_REPORTS/eval_v8_full.jsonl` | Incremental JSONL results |

## Stopping / Resuming

```bash
# Stop
kill $(cat chapter-22/eval_v8.pid)

# Resume (picks up from JSONL)
cd /home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code
uv run python chapter-22/run_eval_improved.py \
    --no-few-shot \
    --output chapter-22/ARC_MODEL_REPORTS/eval_v8_full.json \
    --resume -v 2>&1 | tee -a chapter-22/eval_v8.log
```

## Disabling Individual Features

```bash
# V8 without multi-strategy voting
uv run python chapter-22/run_eval_improved.py \
    --no-few-shot --no-multi-strategy \
    --output chapter-22/ARC_MODEL_REPORTS/eval_v8_no_ms.json -v

# V8 without diff refinement
uv run python chapter-22/run_eval_improved.py \
    --no-few-shot --no-diff-refine \
    --output chapter-22/ARC_MODEL_REPORTS/eval_v8_no_dr.json -v

# V8 without TTT (faster, no VRAM pressure)
uv run python chapter-22/run_eval_improved.py \
    --no-few-shot --no-ttt \
    --output chapter-22/ARC_MODEL_REPORTS/eval_v8_no_ttt.json -v
```

## Post-Eval Analysis

```bash
# Parse JSONL results
uv run python -c "
import json
results = [json.loads(l) for l in open('chapter-22/ARC_MODEL_REPORTS/eval_v8_full.jsonl')]
solved = [r for r in results if r.get('solved')]
print(f'Solved: {len(solved)}/{len(results)} ({len(solved)/len(results)*100:.1f}%)')
by_complexity = {}
for r in results:
    c = r.get('complexity', 'unknown')
    by_complexity.setdefault(c, {'solved': 0, 'total': 0})
    by_complexity[c]['total'] += 1
    if r.get('solved'):
        by_complexity[c]['solved'] += 1
for c, v in sorted(by_complexity.items(), key=lambda x: -x[1]['solved']):
    print(f'  {c}: {v[\"solved\"]}/{v[\"total\"]}')
"

# Compare V8 vs V7
uv run python -c "
import json
v7 = {json.loads(l)['task_id']: json.loads(l) for l in open('chapter-22/ARC_MODEL_REPORTS/eval_v7_ttt.jsonl')}
v8 = {json.loads(l)['task_id']: json.loads(l) for l in open('chapter-22/ARC_MODEL_REPORTS/eval_v8_full.jsonl')}
v7_solved = {t for t, r in v7.items() if r.get('solved')}
v8_solved = {t for t, r in v8.items() if r.get('solved')}
gained = v8_solved - v7_solved
lost = v7_solved - v8_solved
print(f'V7: {len(v7_solved)}/120, V8: {len(v8_solved)}/120')
print(f'Gained ({len(gained)}): {gained}')
print(f'Lost ({len(lost)}): {lost}')
"
```

## Expected Results

| Version | Solved | Notes |
|---------|--------|-------|
| V3 | 90/120 (75.0%) | Best baseline (D4 voting) |
| V4b | 75/120 (62.5%) | Reverted V4 additions |
| V5 | 77/120 (64.2%) | No D4 retries (seed) |
| V6 | 77/120 (64.2%) | No D4 retries (temp) |
| V7 | 78/120 (65.0%) | +TTT (+1 solve via TTT) |
| **V8** | **85-90/120 (71-75%)** | **+multi-strategy +diff-refine +TTT-fix** |

## VRAM Notes

- Multi-strategy voting: **no extra VRAM** (uses same Ollama model)
- Diff refinement: **no extra VRAM** (uses same Ollama model)
- TTT: **~8-10 GB VRAM** (Ollama unloaded during training)
- Keep Windsurf closed during eval to free ~2.5 GB VRAM
