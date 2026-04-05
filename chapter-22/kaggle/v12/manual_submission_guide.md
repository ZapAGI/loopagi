# ARC Prize 2026 - Manual Submission Guide

**Author**: Alexandros Karales
**Date**: April 4, 2026

---

## Problem Solved

v1-v6 submissions all failed because Kaggle assigned a **P100 GPU** (compute capability 6.0, Pascal architecture). **PyTorch 2.10.0+cu128 dropped sm_60 support** - every CUDA operation fails with `no kernel image is available for execution on the device`.

**Fix**: The solver now auto-detects GPU compute capability:
- **T4/newer (sm_70+)**: Uses BitsAndBytes 4-bit quantization (fast, 5GB VRAM)
- **P100 (sm_60)**: Falls back to float16 (no bnb, needs 16GB VRAM)

## Quick Submission via CLI (Already Done)

```bash
# Push with T4x2 accelerator
kaggle kernels push -p chapter-22/kaggle/ --accelerator gpu_t4x2

# Check status
kaggle kernels status karales/arc-prize-2026-arc-agi-2-submission

# Get logs when complete
kaggle kernels output karales/arc-prize-2026-arc-agi-2-submission -p /tmp/kaggle-output
```

## Manual Submission via Kaggle UI

If you need to submit manually through the website:

### Step 1: Go to the notebook
https://www.kaggle.com/code/karales/arc-prize-2026-arc-agi-2-submission

### Step 2: Edit notebook settings
1. Click the **Settings** panel (right sidebar)
2. Under **Accelerator**, select **GPU T4 x2** (NOT GPU P100)
3. Ensure **Internet** is OFF
4. Ensure these datasets are attached:
   - `karales/loopagi-arc-solver` (solver code + bnb wheel)
   - `mavicbf/qwen3-8b-unsloth-4bit-quantized` (model weights)
5. Competition data source: `arc-prize-2026-arc-agi-2`

### Step 3: Submit
1. Click **Save Version** (top right)
2. Select **Save & Run All (Commit)**
3. Wait for completion (expect 2-6 hours for 240 tasks)

### Step 4: Submit to competition
1. After notebook completes, go to the notebook output
2. Click **Submit to Competition**
3. Select `submission.json`

## GPU Compatibility Matrix

| GPU | Compute Cap | PyTorch 2.10+cu128 | BnB 4-bit | float16 | Status |
|-----|------------|--------------------|-----------|---------|----|
| P100 | 6.0 (sm_60) | BROKEN | BROKEN | Works (tight) | Auto fallback |
| T4 | 7.5 (sm_75) | Works | Works | Works | Preferred |
| V100 | 7.0 (sm_70) | Works | Works | Works | OK |

## Resubmission Workflow

```bash
# 1. Update solver code in loopagi/arc/

# 2. Repackage dataset
bash chapter-22/kaggle/package_for_kaggle.sh
# Copy bnb wheel back (packaging script wipes dataset dir)
cp /tmp/bnb-wheel/bitsandbytes-0.49.2-py3-none-manylinux_2_24_x86_64.whl chapter-22/kaggle/dataset/
kaggle datasets version -p chapter-22/kaggle/dataset/ -m "description" --dir-mode zip

# 3. Push notebook with T4
kaggle kernels push -p chapter-22/kaggle/ --accelerator gpu_t4x2

# 4. Monitor
kaggle kernels status karales/arc-prize-2026-arc-agi-2-submission

# 5. Get logs
kaggle kernels output karales/arc-prize-2026-arc-agi-2-submission -p /tmp/kaggle-output
```

## Key Files Changed (v7/v11)

- `loopagi/arc/hf_bridge.py` - Added `_gpu_supports_bnb()` auto-detection, float16 fallback
- `chapter-22/kaggle/notebook.ipynb` - GPU compat check cell, conditional bnb install, CUDA sanity test
- `chapter-22/kaggle/dataset/` - Updated solver + bnb 0.49.2 wheel

## Token Conservation Notes

- Notebook uses `adaptive=False` to prevent perceiver from overriding MAX_HYPOTHESES=1/MAX_ITERATIONS=1
- Only transduction phases enabled (no evolution, TTT, NL evolution, sampling)
- 3-minute hard cap per task
- CUDA cache cleared between tasks to prevent OOM accumulation
