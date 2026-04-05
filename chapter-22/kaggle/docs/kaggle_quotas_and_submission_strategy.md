# Kaggle Quotas, Limits, and Submission Strategy Guide

**Date:** April 2, 2026
**Author:** Alexandros Karales

---

## 1. Kaggle Accelerator Quotas

Kaggle provides free accelerator access to phone-verified users with **weekly** rolling quotas.

| Accelerator | Hardware | VRAM | Weekly Quota | Per-Session Max |
|-------------|----------|------|-------------|-----------------|
| **CPU** | 4 vCPU, ~30 GB RAM | — | Unlimited | 12 hours |
| **GPU P100** | Tesla P100-PCIE | 16 GB | 30 hrs (shared) | 12 hours |
| **GPU T4x2** | 2× NVIDIA T4 | 16 GB each | 30 hrs (shared with P100) | 12 hours |
| **TPU v3-8** | 8 TPU v3 cores | 128 GB HBM | 20 hrs (separate pool) | 9-12 hours |

**Key points:**
- GPU quota is **shared** between P100 and T4x2 — using one drains the same 30-hour pool
- TPU quota is **separate** — 20 hours that do NOT draw from the GPU pool
- Phone verification required to unlock accelerators
- No rollover — unused hours expire each week
- Both interactive editing and commit/save mode consume quota

---

## 2. How Competition Submissions Consume Quotas

### Code Competitions (e.g., ARC Prize)

Your notebook IS the submission. When you submit:

1. Kaggle **re-runs your entire notebook** from scratch on their servers
2. This re-run **DOES consume your weekly GPU/TPU quota**
3. A 9-hour submission eats 9 of your 30 weekly GPU hours
4. If you cancel the notebook, the competition scoring also fails

**Each submission = real GPU hours burned.** Plan accordingly.

### CSV/File Upload Competitions

- You train locally or in a notebook, then upload predictions
- The upload itself does NOT consume GPU quota
- Only the notebook runs you did for training/inference count against quota

### Daily Submission Limits

Most Kaggle competitions impose a **daily submission cap** (typically 2-5 per day):

| Competition Type | Typical Daily Limit |
|-----------------|-------------------|
| Standard code competitions | 2-5 submissions/day |
| ARC Prize 2026 (ARC-AGI-2) | ~2-5 submissions/day (set by competition) |
| Google hackathons/challenges | Often 5 submissions/day |
| CSV upload competitions | 5-10 submissions/day |

The daily limit resets at UTC midnight. Combined with the weekly GPU quota, this creates a **dual constraint**: you are limited both by how many times you can submit AND how many GPU hours you have.

---

## 3. ARC Prize 2026: Specific Rules

The ARC Prize has a unique setup compared to most Kaggle competitions.

### Competition Details

| Parameter | Value |
|-----------|-------|
| **Competition** | ARC Prize 2026 - ARC-AGI-2 |
| **Format** | Code competition (notebook submission) |
| **Tasks** | 120 private eval tasks (scored), semi-private for leaderboard |
| **Runtime limit** | 12 hours max per submission |
| **Hardware** | GPU P100 or T4x2 (set in notebook metadata) |
| **Internet** | **NO** internet access during evaluation |
| **Predictions** | 2 attempts per test input (either correct = 1 point) |
| **Scoring** | Average across all tasks (exact match only) |
| **Open source** | Required for prize eligibility |
| **Grand Prize** | $500K top score + $200K bonus for >85% |

### How ARC Prize Differs from Google DeepMind Competitions

**ARC Prize does NOT use special credits or API quotas.** It runs as a standard Kaggle code competition:

- Your notebook runs on Kaggle's standard GPU hardware
- It consumes your normal weekly GPU quota (30 hrs shared)
- No special tokens, API keys, or cloud credits involved
- No external API calls allowed (no internet during eval)
- Everything must be self-contained in the notebook + attached datasets

This is fundamentally different from Google-sponsored competitions (see Section 5).

---

## 4. Google DeepMind / Google-Sponsored Competitions

Google-sponsored competitions on Kaggle often work differently by providing **API credits** or **special quotas**.

### How Google Competitions Typically Work

| Feature | Google/DeepMind Competitions | ARC Prize |
|---------|------------------------------|-----------|
| **API access** | Often provided (Gemini API, etc.) | None — no internet |
| **Credits** | Google Cloud credits or free API quota | No credits needed |
| **Daily limits** | API rate limits (e.g., requests/min) | Submission count limit |
| **GPU usage** | May use Kaggle GPU OR external cloud | Kaggle GPU only |
| **Model hosting** | Models may be API-hosted by Google | Must bundle model weights |

### Examples of Google Competition Credit Systems

**Gemma Competitions (2024-2025):**
- Participants received free Kaggle GPU access + sometimes GCP credits
- Used Kaggle's standard GPU quota for fine-tuning
- Model weights pre-hosted as Kaggle datasets

**Gemini API Competitions (2025-2026):**
- Participants received free Gemini API quota
- Daily request limits (e.g., 1,500 requests/day free tier)
- Rate limits per minute (e.g., 15-60 RPM depending on model)
- These API quotas are **completely separate** from Kaggle GPU hours
- Your notebook can call the Gemini API during development but NOT during final scoring (no internet in code competitions)

**Key distinction:** Google competitions often give you API credits to experiment with during development, but the final submission still runs without internet. The credits help you iterate faster during the building phase.

---

## 5. Strategies for Maximizing Submissions

### Strategy A: Split Tasks Across Multiple Smaller Runs

When your solver takes close to the 12-hour limit for all tasks, split the work:

```
Run 1: Tasks 0-59   (notebook processes first half, ~6 hrs)
Run 2: Tasks 60-119 (notebook processes second half, ~6 hrs)
Merge: Combine both submission.json files locally
Final: Submit the merged file
```

**Benefits:**
- Each run uses only ~6 hours of GPU quota instead of 12
- If one run fails at task 80, you only lost 6 hours, not 12
- Can iterate on the second half while first half results are solid
- Faster feedback loop

**Implementation pattern:**
```python
import os
TASK_OFFSET = int(os.environ.get("TASK_OFFSET", "0"))
TASK_LIMIT = int(os.environ.get("TASK_LIMIT", "120"))

challenges = dict(list(all_challenges.items())[TASK_OFFSET:TASK_LIMIT])
```

### Strategy B: CPU-Only Pre-Processing + GPU Solve

Split your notebook into two phases:
1. **CPU notebook** (unlimited quota): data loading, feature extraction, task analysis, similarity indexing
2. **GPU notebook** (30 hrs/week): only the LLM inference and solving

Save CPU results to `/kaggle/working/` as a dataset, then attach it to the GPU notebook.

### Strategy C: Progressive Submission

Submit incrementally to build confidence:

```
Submission 1: Transduction-only (fast, ~1 hour) → baseline score
Submission 2: Transduction + relaxed fallback (~3 hours) → improved score  
Submission 3: Full pipeline (~9 hours) → best score
```

Each submission gives you a leaderboard score. You only burn 9 hours on the full pipeline once you're confident the fast methods work.

### Strategy D: Local Development + Kaggle Validation

Do ALL development and iteration locally:
- Run your solver locally on the public training/eval set
- Only submit to Kaggle when you're confident in your approach
- Use Kaggle submissions only for private eval scoring

This preserves your weekly GPU quota for actual competition submissions rather than debugging.

### Strategy E: Use TPU for Some Workloads

Since TPU has a **separate 20-hour quota**, consider:
- Running JAX/PyTorch-XLA compatible models on TPU
- Using TPU for test-time training (LoRA fine-tuning)
- Keeping GPU quota for the main inference pipeline

---

## 6. Splitting Work Across Smaller Test Batches

### Why Split?

A full ARC Prize run processing all 120 tasks can take 9+ hours. If it crashes at task 100, you've wasted 8 hours of GPU quota. Splitting mitigates this.

### Batch Strategy

| Batch | Tasks | Est. Time | Purpose |
|-------|-------|-----------|---------|
| Quick test | 5 tasks | ~15 min | Verify notebook runs at all |
| Smoke test | 20 tasks | ~1.5 hrs | Validate solver + model loading |
| Half run | 60 tasks | ~4.5 hrs | Get partial score |
| Full run | 120 tasks | ~9 hrs | Final submission |

### Implementation: Resume-Capable Notebook

Design your notebook to checkpoint progress:

```python
import json
from pathlib import Path

CHECKPOINT = Path("/kaggle/working/checkpoint.json")

# Load existing results if resuming
if CHECKPOINT.exists():
    results = json.loads(CHECKPOINT.read_text())
else:
    results = {}

for task_id, task in challenges.items():
    if task_id in results:
        continue  # Skip already-solved tasks
    
    prediction = solve(task)
    results[task_id] = prediction
    
    # Checkpoint every task
    CHECKPOINT.write_text(json.dumps(results))
```

### Merging Partial Submissions

If you ran two batches separately:

```python
import json

batch1 = json.load(open("submission_batch1.json"))
batch2 = json.load(open("submission_batch2.json"))

merged = {**batch1, **batch2}

# Verify coverage
assert len(merged) == 120, f"Missing tasks: {120 - len(merged)}"

json.dump(merged, open("submission.json", "w"))
```

---

## 7. Quota Management Best Practices

### Weekly Budget Planning (30 GPU hours)

| Activity | Hours | Notes |
|----------|-------|-------|
| Debug runs (5 tasks each) | 2-3 hrs | 3-4 quick debug runs |
| Smoke test (20 tasks) | 1.5 hrs | Validate end-to-end |
| Full submission attempt | 9-12 hrs | The real run |
| Buffer for failures/retries | 6-8 hrs | Things go wrong |
| **Total** | **~20-24 hrs** | Leaves margin |

### Avoiding Quota Waste

1. **Test locally first** — Never debug on Kaggle GPU. Use your local machine.
2. **Use CPU mode for non-GPU work** — Data loading, JSON parsing, submission formatting.
3. **Set timeouts per task** — If a single task takes >15 min, skip it and move on.
4. **Checkpoint aggressively** — Save results after every task so crashes don't lose all progress.
5. **Monitor `/kaggle/working/` disk** — 20 GB limit. Clean intermediate files.
6. **Print heartbeats** — Long-running cells with no output get killed by Kaggle's timeout monitor.

### Checking Your Remaining Quota

Navigate to **kaggle.com → Your Profile → Account → GPU/TPU Quota** to see remaining hours. There is no API endpoint for this — you must check the web UI.

---

## 8. Platform Comparison: Free GPU Options

| Platform | GPU | Free Quota | Session Limit | Best For |
|----------|-----|-----------|---------------|----------|
| **Kaggle** | P100 / T4x2 | 30 hrs/week GPU, 20 hrs/week TPU | 12 hrs | Competitions, prototyping |
| **Google Colab** | T4 (free) | 15-30 hrs/week (variable) | ~12 hrs (disconnects) | Quick experiments |
| **Colab Pro** | T4/A100 | $9.99/mo, ~100 hrs | 24 hrs | Sustained training |
| **Lightning AI** | T4/A10G | Free monthly hours | Varies | PyTorch workflows |
| **GCP Free Tier** | — | $300 credits (90 days) | — | Cloud training |

### When to Use Each

- **Kaggle**: Competition submissions, quick GPU experiments, community notebooks
- **Colab**: Interactive development, visualization, tutorials
- **Local GPU** (RTX 5080): All development, full evals, no quota limits
- **GCP/Cloud**: When you need A100/H100 or multi-GPU training

---

## 9. ARC Prize Submission Checklist

Before each Kaggle submission:

- [ ] Solver tested locally on eval set (know your expected score)
- [ ] Notebook tested in Kaggle interactive mode on 3-5 tasks
- [ ] Model weights attached as Kaggle dataset (no internet during eval)
- [ ] All Python dependencies bundled (no pip install from internet)
- [ ] Heartbeat prints every task (prevent timeout kills)
- [ ] Per-task timeout set (skip stuck tasks, save GPU hours)
- [ ] Checkpoint/resume logic working
- [ ] `submission.json` format validated (2 attempts per test output)
- [ ] Weekly GPU quota checked (enough hours for full run?)
- [ ] Daily submission limit checked (submissions remaining today?)

---

## References

- [Kaggle Notebook Environment](https://www.kaggle.com/docs/notebooks)
- [ARC Prize 2026 Competition](https://arcprize.org/competitions/2026)
- [ARC Prize 2026 ARC-AGI-2 Rules](https://arcprize.org/competitions/2026/arc-agi-2)
- [Kaggle GPU Quotas Discussion](https://www.kaggle.com/general/108481)
- [Kaggle for Deep Learning and LLM Workflows (HF Reference)](https://huggingface.co/datasets/John6666/knowledge_base_md_for_rag_1/blob/main/kaggle_20251121.md)
- [GMI Cloud: Free GPU Trials Guide 2026](https://www.gmicloud.ai/blog/where-can-i-get-free-gpu-cloud-trials-in-2026-a-complete-guide)

---

*Copyright 2026 Alexandros Karales. All Rights Reserved.*
