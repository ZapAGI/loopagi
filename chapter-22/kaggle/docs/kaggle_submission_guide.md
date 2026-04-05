# ARC Prize 2026 - Kaggle Submission Guide

## Competition: ARC-AGI-2
- **URL**: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2
- **Format**: 240 test tasks, `submission.json` with `attempt_1` + `attempt_2` per test output
- **Runtime**: 12h max, GPU P100 16GB, no internet

## Architecture

### Kaggle Assets
1. **Notebook**: `karales/arc-prize-2026-arc-agi-2-submission`
   - 9 cells: setup → GPU check → model load → data load → config → helpers → solve → validate/save
2. **Solver Dataset**: `karales/loopagi-arc-solver`
   - Contains `loopagi/arc/` (45 Python modules, 516KB)
   - Minimal `loopagi/core/ollama_utils.py` stub (returns `is_ollama_running=False`)
3. **Model Dataset**: `mavicbf/qwen3-8b-unsloth-4bit-quantized`
   - Pre-downloaded Qwen3-8B 4-bit weights (~5GB)

### Solver Pipeline (Kaggle Config)
- **Phase 0**: Strict transduction (verified against training pairs)
- **Phase Y**: Iterative refinement transduction (cell-level feedback)
- **Phase CC3**: D4 symmetry voting (8 augmentations, majority vote)
- **Phase FF**: Multi-strategy voting (pass-at-K fallback)
- **Phase 0c**: Relaxed transduction (cross-validation at 95%)
- **Phase D**: Transduction cell fix (near-miss repair)
- **Main**: Code synthesis (2 hypotheses × 2 iterations)
- **Disabled**: Evolution, NL evolution, diff refine, TTT (too slow for 240 tasks)

### Time Budget
- Total: 11h (1h buffer)
- Per task: ~10 min max (165s avg target)
- Fallback: identity output if time runs out

## Local Eval Results
- **112/120 (93.3%)** on ARC-AGI-2 evaluation set
- 93% solves via transduction methods
- Avg 35s per task with HF bridge

## Resubmission Workflow

```bash
# 1. Update solver code
# 2. Repackage dataset
bash chapter-22/kaggle/package_for_kaggle.sh
kaggle datasets version -p chapter-22/kaggle/dataset/ -m "description" --dir-mode zip

# 3. Push updated notebook
kaggle kernels push -p chapter-22/kaggle/

# 4. Check status
kaggle kernels status karales/arc-prize-2026-arc-agi-2-submission

# 5. Get logs
kaggle kernels output karales/arc-prize-2026-arc-agi-2-submission -p /tmp/kaggle-output

# 6. Submit (after notebook completes successfully)
# Done automatically — the notebook writes submission.json to /kaggle/working/
```

## Key Files
- `chapter-22/kaggle/notebook.ipynb` — The Kaggle notebook
- `chapter-22/kaggle/kernel-metadata.json` — Notebook metadata (datasets, GPU, etc.)
- `chapter-22/kaggle/dataset/` — Packaged solver for upload
- `chapter-22/kaggle/package_for_kaggle.sh` — Packaging script
- `chapter-22/kaggle_submission.py` — Standalone submission script (alternative)
- `loopagi/arc/hf_bridge.py` — HuggingFace LLM bridge (replaces Ollama)

## Troubleshooting
- **409 Conflict on push**: Previous kernel version still running. Wait and retry.
- **Model not found**: Ensure `mavicbf/qwen3-8b-unsloth-4bit-quantized` is in dataset_sources.
- **Solver import error**: Check dataset extraction path in Cell 1 logs.
- **VRAM OOM**: Reduce `sample_n` or `MAX_HYPOTHESES`.
- **`total_mem` AttributeError**: Use `total_memory` (PyTorch 2.10+ naming).
