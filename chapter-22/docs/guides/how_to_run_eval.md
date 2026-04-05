# How to Run the ARC-AGI Evaluation Properly

**Machine:** Anubix-Alienware | 60GB RAM | RTX 5080 16GB | Ubuntu 25.10
**Author:** Alexandros Karales | March 20, 2026

## Why the System Froze

The 120-task evaluation froze the system due to **OOM (Out of Memory)**.

Root cause: 4 Windsurf language server instances were consuming ~40GB RAM
(~10GB each), leaving only ~19GB for Ollama + eval + OS. When the eval
script ran complex tasks with large grids (29x29 = 841 cells) and
`num_predict=4096`, Ollama's RAM usage spiked and triggered the OOM killer.

## Pre-Flight Checklist

Before running the full 120-task eval, do this:

### 1. Close unnecessary Windsurf workspaces

Each open workspace spawns a language server using ~10GB RAM. Close ALL
workspaces except the one you're actively working in.

Check current memory hogs:
```bash
ps aux --sort=-%mem | head -10
```

Target: at least **30GB free RAM** before starting eval.
```bash
free -h
# Should show: available > 30Gi
```

### 2. Check Ollama is running and healthy

```bash
systemctl is-active ollama
ollama list | grep qwen3:8b
nvidia-smi  # Check GPU VRAM is mostly free
```

### 3. Close Chrome tabs and other heavy apps

Chrome can use 1-3GB. Close tabs you don't need.

### 4. (Optional) Increase swap

The system has 8GB swap. For safety, you can temporarily increase it:
```bash
sudo fallocate -l 16G /swapfile2
sudo chmod 600 /swapfile2
sudo mkswap /swapfile2
sudo swapon /swapfile2
# After eval: sudo swapoff /swapfile2 && sudo rm /swapfile2
```

## Running the Evaluation

### Option A: Run in a dedicated terminal (RECOMMENDED)

Open a fresh terminal (not inside Windsurf) and run:

```bash
cd /home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code

# Full 120-task eval (no few-shot, ~4-5 hours)
nohup uv run python chapter-22/run_eval_improved.py \
  --no-few-shot \
  --output chapter-22/ARC_MODEL_REPORTS/eval_v2_full.json \
  -v \
  > eval_v2_full.log 2>&1 &

echo "Eval PID: $!"
echo "Monitor: tail -f eval_v2_full.log"
echo "Progress: cat chapter-22/ARC_MODEL_REPORTS/eval_v2_full.jsonl | wc -l"
```

Using `nohup` ensures the eval survives if your terminal disconnects.

### Option B: Run with nice (lower priority)

If you want to keep using the machine while eval runs:

```bash
cd /home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code

nice -n 10 uv run python chapter-22/run_eval_improved.py \
  --no-few-shot \
  --output chapter-22/ARC_MODEL_REPORTS/eval_v2_full.json \
  -v \
  > eval_v2_full.log 2>&1 &
```

`nice -n 10` gives the eval lower CPU priority so your desktop stays responsive.

### Option C: Run with memory limit (SAFEST)

Use systemd-run to cap the eval's memory usage:

```bash
cd /home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code

systemd-run --user --scope -p MemoryMax=4G \
  uv run python chapter-22/run_eval_improved.py \
  --no-few-shot \
  --output chapter-22/ARC_MODEL_REPORTS/eval_v2_full.json \
  -v \
  > eval_v2_full.log 2>&1 &
```

This kills the eval if it exceeds 4GB RAM (the eval itself uses ~200MB,
but this protects against runaway memory leaks).

Note: This does NOT limit Ollama's memory. Ollama runs as a system service
and needs its own RAM for model weights.

### Option D: Resume after interruption

The eval script supports `--resume` to continue from where it left off:

```bash
uv run python chapter-22/run_eval_improved.py \
  --no-few-shot \
  --output chapter-22/ARC_MODEL_REPORTS/eval_v2_full.json \
  --resume \
  -v \
  > eval_v2_full_resume.log 2>&1 &
```

## Monitoring Progress

### Check how many tasks are done:
```bash
wc -l chapter-22/ARC_MODEL_REPORTS/eval_v2_full.jsonl
```

### Check current solve count:
```bash
cat chapter-22/ARC_MODEL_REPORTS/eval_v2_full.jsonl | \
  python3 -c "import sys,json; lines=[l for l in sys.stdin if l.strip()]; \
  solved=sum(1 for l in lines if json.loads(l).get('solved')); \
  print(f'{len(lines)}/120 done, {solved} solved')"
```

### Monitor system resources:
```bash
watch -n 5 'free -h | head -3 && echo --- && nvidia-smi --query-gpu=memory.used --format=csv,noheader'
```

### Watch live log output:
```bash
tail -f eval_v2_full.log | grep -E "SOLVED|\[.*\].*%"
```

## Expected Resource Usage

| Resource | Expected | Danger Zone |
|----------|----------|-------------|
| Eval script RSS | ~170-200 MB | > 500 MB |
| Ollama (qwen3:8b) | ~5-6 GB VRAM, ~2-3 GB RAM | > 10 GB RAM |
| Total system RAM needed | ~8-10 GB (eval + Ollama) | > 40 GB used |
| GPU VRAM | ~5-6 GB of 16 GB | > 14 GB |
| Time per task | ~2-5 min | > 10 min (may be stuck) |
| Total time (120 tasks) | ~4-6 hours | > 10 hours |

## Quick 10-Task Validation (5-10 minutes)

For a quick test before the full run:
```bash
uv run python chapter-22/run_eval_improved.py \
  --tasks 8e5c0c38,135a2760,b99e7126,dbff022c,c4d067a0,a25697e4,38007db0,332f06d7,9bbf930d,3e6067c3 \
  --no-few-shot \
  --output chapter-22/ARC_MODEL_REPORTS/eval_quick_test.json \
  -v
```

## Troubleshooting

### System freezes during eval
1. Close Windsurf workspaces (each = ~10GB RAM)
2. Close Chrome tabs
3. Use Option C (memory-limited run)
4. Consider running overnight when no other apps are open

### Eval is very slow (> 5 min/task)
1. Check `nvidia-smi` for GPU utilization
2. Check if another model is loaded: `ollama ps`
3. Restart Ollama: `sudo systemctl restart ollama`

### Ollama returns 500 errors
1. Too many models loaded: `ollama ps` then stop extras
2. GPU memory full: restart Ollama
3. During model pull: don't run eval simultaneously
