# ARC-AGI V3 Full Evaluation — Run Guide

**Date:** March 21, 2026
**Branch:** `feature/arc-improvements-v2`
**Model:** qwen3:8b (local, Ollama)
**Expected duration:** 12-15 hours
**Expected score:** 22-27/120 (18-22%)

---

## 1. Pre-Flight Checks

```bash
# Ensure correct branch
cd /home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code
git branch --show-current
# Should show: feature/arc-improvements-v2

# Ensure all tests pass
uv run pytest tests/ --tb=short -q

# Ensure Ollama is running with qwen3:8b
ollama ps

# Ensure caffeine is running (prevents suspend)
pgrep caffeine || caffeine &
```

---

## 2. Start the Full Eval

```bash
nohup nice -n 10 uv run python chapter-22/run_eval_improved.py \
  --no-few-shot \
  --output chapter-22/ARC_MODEL_REPORTS/eval_v3_full.json \
  --resume \
  -v \
  > eval_v3_full.log 2>&1 &
```

Note the PID printed (e.g., `[1] 12345`).

---

## 3. Monitor Progress

### Quick status (solved count + current task)
```bash
grep -E "SOLVED|^\[.*\.\.\." eval_v3_full.log | tail -20
```

### Completed task count
```bash
wc -l chapter-22/ARC_MODEL_REPORTS/eval_v3_full.jsonl
```

### Live follow
```bash
tail -f eval_v3_full.log
```

### Solve rate so far
```bash
python3 -c "
import json
with open('chapter-22/ARC_MODEL_REPORTS/eval_v3_full.jsonl') as f:
    recs = [json.loads(l) for l in f if l.strip()]
solved = sum(1 for r in recs if r.get('solved'))
avg_sim = sum(r.get('similarity',0) for r in recs) / max(len(recs),1)
print(f'{solved}/{len(recs)} solved ({solved/max(len(recs),1):.0%}), avg sim {avg_sim:.1%}')
"
```

### Breakdown by method
```bash
python3 -c "
import json
from collections import Counter
with open('chapter-22/ARC_MODEL_REPORTS/eval_v3_full.jsonl') as f:
    recs = [json.loads(l) for l in f if l.strip()]
methods = Counter(r.get('complexity','?') for r in recs if r.get('solved'))
print('Solves by method:')
for m, c in methods.most_common():
    print(f'  {m}: {c}')
"
```

### Check if process is still running
```bash
ps aux | grep run_eval_improved | grep -v grep
```

### GPU usage
```bash
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader
```

---

## 4. If You Need to Stop & Resume

```bash
# Find and kill the eval process
pkill -f "run_eval_improved.*eval_v3_full"

# Later, restart with --resume (skips completed tasks)
nohup nice -n 10 uv run python chapter-22/run_eval_improved.py \
  --no-few-shot \
  --output chapter-22/ARC_MODEL_REPORTS/eval_v3_full.json \
  --resume \
  -v \
  > eval_v3_full.log 2>&1 &
```

---

## 5. When Complete — Analyze Results

### Full summary
```bash
python3 -c "
import json
with open('chapter-22/ARC_MODEL_REPORTS/eval_v3_full.jsonl') as f:
    recs = [json.loads(l) for l in f if l.strip()]
solved = [r for r in recs if r.get('solved')]
avg_sim = sum(r.get('similarity',0) for r in recs) / max(len(recs),1)
total_t = sum(r.get('time_seconds',0) for r in recs)
print(f'=== V3 Full Eval Results ===')
print(f'Solved: {len(solved)}/{len(recs)} ({len(solved)/max(len(recs),1):.0%})')
print(f'Avg similarity: {avg_sim:.1%}')
print(f'Total time: {total_t/3600:.1f}h ({total_t/max(len(recs),1):.0f}s/task)')
from collections import Counter
methods = Counter(r.get('complexity','?') for r in solved)
print('By method:', dict(methods.most_common()))
"
```

### Compare V2 vs V3
```bash
python3 -c "
import json
with open('chapter-22/ARC_MODEL_REPORTS/eval_v2_full.jsonl') as f:
    v2 = {json.loads(l)['task_id']: json.loads(l) for l in f if l.strip()}
with open('chapter-22/ARC_MODEL_REPORTS/eval_v3_full.jsonl') as f:
    v3 = {json.loads(l)['task_id']: json.loads(l) for l in f if l.strip()}
new_solves = [t for t in v3 if v3[t].get('solved') and not v2.get(t,{}).get('solved')]
regressions = [t for t in v3 if not v3[t].get('solved') and v2.get(t,{}).get('solved')]
print(f'New solves: {len(new_solves)}')
for t in new_solves:
    print(f'  {t}: {v3[t].get(\"complexity\")}')
print(f'Regressions: {len(regressions)}')
for t in regressions:
    print(f'  {t}: v2={v2[t].get(\"similarity\",0):.1%} v3={v3[t].get(\"similarity\",0):.1%}')
"
```

### Find new near-misses to target next
```bash
python3 -c "
import json
with open('chapter-22/ARC_MODEL_REPORTS/eval_v3_full.jsonl') as f:
    recs = [json.loads(l) for l in f if l.strip()]
near = [r for r in recs if not r.get('solved') and r.get('similarity',0) >= 0.90]
near.sort(key=lambda r: r['similarity'], reverse=True)
print(f'Near-misses (>=90%): {len(near)}')
for r in near[:20]:
    print(f'  {r[\"task_id\"]}: {r[\"similarity\"]:.1%} [{r.get(\"complexity\",\"?\")}]')
"
```

---

## 6. Commit Results

```bash
git add -A
git commit -m "V3 full eval results: XX/120 (XX%) — augmented voting + NL pipeline"
git push
```

---

*ARC-AGI V3 Eval Run Guide — March 2026*
