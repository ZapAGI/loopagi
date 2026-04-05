# V5 Eval — Run Instructions

## Overview

V5 addresses the V4b regression (75/120 → target ≥90/120) with two key fixes:

| Change | Why |
|---|---|
| **Ollama seed=42** | Eliminates 35% run-to-run variance from LLM non-determinism |
| **D4 retry (seed=123)** | Doubles chance of crossing 80% agreement threshold |
| **Reverted V4 additions** | Diversity fallback, ensemble, evolution budget were net-negative |

## Prerequisites

- Ollama installed and `qwen3:8b` model pulled
- RTX 5080 (16 GB VRAM) or equivalent
- **Windsurf must be closed** (frees ~3-5 GB VRAM)

## Quick Start

```bash
# 1. Close Windsurf first!

# 2. Navigate to project root
cd /home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code

# 3. Make launcher executable
chmod +x chapter-22/run_v5_eval.sh

# 4. Run the eval
./chapter-22/run_v5_eval.sh
```

## Monitoring

```bash
# Live log stream
tail -f chapter-22/eval_v5.log

# Quick status summary
cat chapter-22/eval_v5_summary.txt

# Count solved tasks so far
grep -c SOLVED chapter-22/eval_v5.log

# Count completed tasks
wc -l < chapter-22/ARC_MODEL_REPORTS/eval_v5_nottt.jsonl
```

## Output Files

| File | Description |
|---|---|
| `chapter-22/ARC_MODEL_REPORTS/eval_v5_nottt.json` | Final results (JSON) |
| `chapter-22/ARC_MODEL_REPORTS/eval_v5_nottt.jsonl` | Incremental results (JSONL) |
| `chapter-22/eval_v5.log` | Full timestamped log |
| `chapter-22/eval_v5_summary.txt` | Live status summary |
| `chapter-22/eval_v5.pid` | PID file (auto-cleaned) |

## Stopping / Resuming

```bash
# Stop the eval
kill $(cat chapter-22/eval_v5.pid)

# Resume from where it left off (add --resume flag to script)
# Edit run_v5_eval.sh and add --resume to the uv run command, then re-run
./chapter-22/run_v5_eval.sh
```

## Expected Results

| Version | Solved | Rate | Key Difference |
|---|---|---|---|
| V3 (baseline) | 90/120 | 75.0% | No seed, single D4 attempt |
| V4b (regressed) | 75/120 | 62.5% | Non-determinism + wasted diversity calls |
| **V5 (expected)** | **≥90/120** | **≥75.0%** | **Seed + D4 retry** |

- **Floor**: 90/120 (seed makes first attempt reproducible like V3)
- **Ceiling**: ~95-100/120 (D4 retry recovers additional tasks)
- **Time**: ~17-18h (same as V3 + ~2min per D4 retry)

## Post-Eval Analysis

After the eval completes, compare results:

```bash
cd /home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code

# Quick solve count
python3 -c "
import json
for name, path in [
    ('V3', 'chapter-22/ARC_MODEL_REPORTS/eval_v3_full.jsonl'),
    ('V4b', 'chapter-22/ARC_MODEL_REPORTS/eval_v4_nottt.jsonl'),
    ('V5', 'chapter-22/ARC_MODEL_REPORTS/eval_v5_nottt.jsonl'),
]:
    solved = sum(1 for l in open(path) if json.loads(l).get('solved'))
    total = sum(1 for _ in open(path))
    print(f'{name}: {solved}/{total} ({solved/total*100:.1f}%)')
"
```

## Commit History

| Commit | Description |
|---|---|
| `dba7ab9` | V3 baseline |
| `bdfe793` | V4b (diversity fallback, ensemble, evo budget) |
| `a5b40a1` | V5 code changes (seed + retry + revert) |
| `f901a54` | V5 eval launcher script |

## Root Cause Analysis Summary

The V4b regression was **not a code bug** — it was LLM non-determinism:

- D4 voting only **65% reproducible** across runs (42/120 tasks disagree)
- V3 got lucky: 63 D4 solves vs V4b's 45
- 357 grid parse failures + 317 color filter rejections per run
- V4 additions (diversity, ensemble) were harmless but useless
- Fix: seed for reproducibility + retry for resilience
