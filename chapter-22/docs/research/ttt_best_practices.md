# TTT (Test-Time Training) Best Practices

**Hardware:** RTX 5080 (16GB VRAM), Ubuntu 25.10

---

## The VRAM Budget

| Component | VRAM | Can Coexist? |
|-----------|------|--------------|
| TTT training (qwen3:8b 4-bit + LoRA + optimizer) | ~10-12GB | NO with Ollama |
| TTT inference (generation after training) | ~8GB | NO with Ollama |
| Ollama (qwen3:8b loaded) | ~7GB | NO with TTT |
| Windsurf (GPU-accelerated UI) | ~1-2GB | Risky |
| Desktop compositor (GNOME) | ~0.5GB | Always needed |

**Rule: TTT and Ollama CANNOT run simultaneously.**

---

## Safe TTT Workflow

### Option A: From a terminal (RECOMMENDED)

```bash
# 1. Close Windsurf (or any GPU-heavy app)
# 2. Stop Ollama models
ollama stop qwen3:8b

# 3. Verify VRAM is free
nvidia-smi --query-gpu=memory.used --format=csv,noheader
# Should show < 1000 MiB

# 4. Run TTT on a single task
chapter-22/ttt_venv/bin/python chapter-22/ttt_train.py \
    --input /tmp/ttt_task.json \
    --output /tmp/ttt_predictions.json \
    --steps 30 \
    --batch-size 1

# 5. Restart Ollama when done (auto-loads models on demand)
# No action needed — Ollama service stays running, models load on next request
```

### Option B: Via the eval pipeline (automatic)

The `ttt.py` orchestrator handles Ollama automatically:
1. Unloads all Ollama models before TTT (`ollama stop`)
2. Runs TTT with VRAM capped at 14GB
3. Logs "Ollama ready" when done (models reload on next request)

```bash
# Run eval with TTT enabled (default)
nohup nice -n 10 uv run python chapter-22/run_eval_improved.py \
    --no-few-shot \
    --output chapter-22/ARC_MODEL_REPORTS/eval_v4_full.json \
    --resume -v > eval_v4.log 2>&1 &

# Run eval WITHOUT TTT (faster, no VRAM risk)
nohup nice -n 10 uv run python chapter-22/run_eval_improved.py \
    --no-few-shot --no-ttt \
    --output chapter-22/ARC_MODEL_REPORTS/eval_v4_nottt.json \
    --resume -v > eval_v4.log 2>&1 &
```

---

## Safety Measures Built In

1. **VRAM cap:** `torch.cuda.set_per_process_memory_fraction(14/16.6)` — leaves 2.6GB for OS
2. **Ollama unload:** `ollama stop <model>` before training — frees 7GB
3. **Error recovery:** all error paths restore Ollama state
4. **Batch size 1:** reduces peak VRAM during training

---

## If It Crashes Anyway

```bash
# 1. Check if Ollama is running
ollama ps

# 2. Check VRAM usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader

# 3. Kill any stuck Python processes
pkill -f ttt_train.py

# 4. Check crash logs
journalctl --since "1 hour ago" -p err -k | grep -i "nvidia\|drm\|oom\|gem"
```

---

## When to Use TTT

TTT is expensive (~5-10 minutes per task). Only use it for:
- Unsolved tasks with **similarity >= 85%** (near-misses)
- Tasks where transduction almost works but has small errors
- After all cheaper methods (augmented voting, relaxed transduction) have been tried

The pipeline automatically gates TTT to near-misses via `config.enable_ttt` and the 85% similarity threshold.

---

*TTT Best Practices — March 2026*
