# V7 Eval — Commands & Instructions

## Overview

V7 enables TTT (Test-Time Training) for near-miss recovery and removes useless D4 retries.

| Change | Impact |
|---|---|
| **Removed D4 retries** | Saves ~6h (seed: 0/64, temp: 2/129 success rate) |
| **TTT enabled** | LoRA fine-tunes on ~23 near-miss tasks (sim >= 0.85) |
| **No seed** | Matches V3 behavior |

## Quick Start

```bash
# 1. Close Windsurf first!
# 2. From a plain terminal:
cd /home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code
chmod +x chapter-22/run_v7_eval.sh
./chapter-22/run_v7_eval.sh
```

## Check Progress

```bash
py -c "
import json
solved = total = errors = 0
with open('chapter-22/ARC_MODEL_REPORTS/eval_v7_ttt.jsonl') as f:
    for line in f:
        r = json.loads(line)
        total += 1
        if r.get('solved'): solved += 1
        if r.get('error'): errors += 1
remaining = 120 - total
print(f'Progress: {total}/120 ({remaining} remaining)')
print(f'Solved:   {solved}/{total} ({solved/total*100:.1f}%)')
print(f'Errors:   {errors}')
" && nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
```

## Monitoring

```bash
# Live log stream
tail -f chapter-22/eval_v7.log

# Quick status summary
cat chapter-22/eval_v7_summary.txt

# Count solved tasks
grep -c SOLVED chapter-22/eval_v7.log

# Count completed tasks
wc -l < chapter-22/ARC_MODEL_REPORTS/eval_v7_ttt.jsonl

# Check TTT attempts and successes
grep "TTT" chapter-22/eval_v7.log

# Check TTT solve count
grep -c "SOLVED via TTT" chapter-22/eval_v7.log
```

## Output Files

| File | Description |
|---|---|
| `chapter-22/ARC_MODEL_REPORTS/eval_v7_ttt.json` | Final results (JSON) |
| `chapter-22/ARC_MODEL_REPORTS/eval_v7_ttt.jsonl` | Incremental results (JSONL) |
| `chapter-22/eval_v7.log` | Full timestamped log |
| `chapter-22/eval_v7_summary.txt` | Live status summary |
| `chapter-22/eval_v7.pid` | PID file (auto-cleaned) |

## Stopping / Resuming

```bash
# Stop the eval
kill $(cat chapter-22/eval_v7.pid)

# Resume (add --resume flag to the script's uv run command, then re-run)
./chapter-22/run_v7_eval.sh
```

## Post-Eval Comparison

```bash
py -c "
import json
for name, path in [
    ('V3', 'chapter-22/ARC_MODEL_REPORTS/eval_v3_full.jsonl'),
    ('V4b', 'chapter-22/ARC_MODEL_REPORTS/eval_v4_nottt.jsonl'),
    ('V5', 'chapter-22/ARC_MODEL_REPORTS/eval_v5_nottt.jsonl'),
    ('V6', 'chapter-22/ARC_MODEL_REPORTS/eval_v6_nottt.jsonl'),
    ('V7', 'chapter-22/ARC_MODEL_REPORTS/eval_v7_ttt.jsonl'),
]:
    try:
        solved = sum(1 for l in open(path) if json.loads(l).get('solved'))
        total = sum(1 for _ in open(path))
        print(f'{name}: {solved}/{total} ({solved/total*100:.1f}%)')
    except FileNotFoundError:
        print(f'{name}: not found')
"
```

## TTT Analysis

```bash
# Check which tasks TTT attempted and results
py -c "
import json
with open('chapter-22/ARC_MODEL_REPORTS/eval_v7_ttt.jsonl') as f:
    ttt_attempted = ttt_solved = 0
    for line in f:
        r = json.loads(line)
        if r.get('ttt'):
            ttt_attempted += 1
            if r.get('solved'):
                ttt_solved += 1
                print(f'  TTT SOLVED: {r[\"task_id\"]} (sim={r.get(\"similarity\",0):.3f})')
    print(f'TTT: {ttt_solved}/{ttt_attempted} solved')
"
```

## Expected Results

| Version | Solved | Key Change |
|---|---|---|
| V3 (baseline) | 90/120 | Lucky D4 outlier (+23% above avg) |
| V4b | 75/120 | D4 non-determinism |
| V5 | 77/120 | seed=42 (useless) |
| V6 | 77/120 | temp retries (2/129) |
| **V7 (expected)** | **85-95/120** | **TTT recovers near-misses** |

## VRAM Notes

- TTT uses ~8-10 GB VRAM for LoRA fine-tuning
- Ollama is unloaded during TTT training, then reloaded
- Total peak VRAM ~12 GB (safe on RTX 5080 16 GB)
- **Do NOT open Windsurf** while eval is running

## Root Cause Summary

The V4b regression was **NOT a code bug** — it was LLM non-determinism:

- D4 voting success: ~47/120 per run (V3's 63 was a +23% outlier)
- 76/120 tasks are D4-solvable, but only 33 are reliable (all 4 runs)
- D4 retries don't work (seed/temp changes produce same failures)
- Recovery strategy: TTT on the ~23 near-miss tasks (sim >= 0.85)
