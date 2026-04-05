# Chapter 22: Building the Reasoning Engine

**Author**: Alexandros Karales
**Current Version**: v12 (solver v9, Kaggle notebook v12)
**Local Eval**: 112/120 (93.3%) on ARC-AGI-2 evaluation set

## Part VI - The Future We're Building

Code examples for the ARC-AGI challenge solver - a multi-agent reasoning engine
that attempts abstract visual reasoning puzzles using the architecture from
earlier chapters.

## Directory Structure

```
chapter-22/
  README.md                    # This file
  __init__.py                  # Package init
  docs/
    research/                  # Research and improvement plans
      arc_improvement_plan.md
      arc_improvement_research_v2.md
      arc_improvement_research_v3.md
      arc_improvement_research_v4.md
      arc_polars_research.md
      v9_improvement_research.md
      v9_implementation_plan.md
      arc_challenge_zap_agi_strategic_position.md
      ttt_best_practices.md
    reports/                   # Evaluation reports and analysis
      v7_eval_report.md
      v8_regression_analysis.md
      v8_unsolved_analysis.md
    guides/                    # How-to guides, eval commands, prompts
      how_to_run_eval.md
      run_eval_v3.md
      v4_eval_commands.md
      v5_eval_commands.md
      v7_eval_commands.md
      v8_eval_commands.md
      continue_prompt_arc_v2.md
      continue_prompt_arc_v3.md
      gcp_gpu_vm_reference.md
      gcp_tpu_reference.md
      readme_arc_old.md
  eval/
    scripts/                   # Evaluation runner scripts
      run_eval.py
      run_eval_improved.py
      run_v4_eval.sh .. run_v8_eval.sh
      run_model_benchmark_3tasks.sh
      run_tpu_eval.py
    logs/                      # Eval run logs (v4-v8)
      eval_v4.log .. eval_v8.log
      eval_v4_summary.txt .. eval_v8_summary.txt
    benchmarks/                # Model benchmark reports and data
      ARC_MODEL_SEARCH_2026.md
      MODEL_BENCHMARK_REPORT.md
      EVAL_V9_REPORT.md
      (+ per-model .json, .jsonl, .parquet, .md files)
    data/                      # ARC-AGI-2 dataset files
      ARC-AGI-2/
      arc-agi_evaluation_challenges.json
      training_index.json
  kaggle/                      # Kaggle submission system
    current -> v12             # Symlink to latest version
    v01/                       # Version 01 - first submission
      notebook.ipynb
      submission.json
    v07/                       # Version 07 - first scored attempt
      submission.json
      logs.log
    v12/                       # Version 12 - current (GPU auto-detect, fixed imports)
      notebook.ipynb           # The notebook pushed to Kaggle
      kernel-metadata.json     # Kaggle kernel config
      manual_submission_guide.md
    dataset/                   # Packaged solver code + bnb wheel for upload
    docs/                      # Kaggle reference docs
      kaggle_submission_guide.md
      kaggle_quotas_and_submission_strategy.md
      kaggle_reference_guide.md
      kaggle_upload_reference.md
      continue_kaggle_submission.md
    package_for_kaggle.sh      # Dataset packaging script
  scripts/                     # Standalone utility scripts
    demo_arc.py
    demo_solver.py
    diagnose_nearmiss.py
    benchmark_models.py
    kaggle_submission.py
    ttt_train.py
```

## What You Build

- **ARC solver pipeline** with transduction-first approach, D4 symmetry voting, multi-strategy ensemble
- **Qwen3-8B LLM bridge** with auto GPU detection (BnB 4-bit on T4, float16 on older GPUs, CPU fallback)
- **Evaluation harness** for measuring accuracy on ARC-AGI tasks
- **Kaggle submission pipeline** for the ARC Prize 2026 competition

## Key Modules

| Module | Purpose |
|--------|---------|
| `loopagi/arc/hf_bridge.py` | HuggingFace model loading with GPU auto-detection |
| `loopagi/arc/solve_improved.py` | Main solver pipeline (v9) |
| `loopagi/arc/transducer.py` | Direct grid prediction via LLM |
| `loopagi/arc/perceiver.py` | Extract structural observations from grid pairs |
| `loopagi/arc/hypothesizer.py` | Generate candidate transformation rules |
| `loopagi/arc/synthesizer.py` | Convert hypotheses to executable Python functions |
| `loopagi/arc/evaluator.py` | Test synthesized functions against training pairs |
| `loopagi/arc/refiner.py` | Iterative improvement of near-miss solutions |

## Running

```bash
# Run a demo
uv run python chapter-22/scripts/demo_arc.py

# Run evaluation (v8 config)
bash chapter-22/eval/scripts/run_v8_eval.sh

# Package and submit to Kaggle
bash chapter-22/kaggle/package_for_kaggle.sh
kaggle datasets version -p chapter-22/kaggle/dataset/ -m "description" --dir-mode zip
kaggle kernels push -p chapter-22/kaggle/current/

# Or push a specific version
kaggle kernels push -p chapter-22/kaggle/v12/

# Create new version
mkdir chapter-22/kaggle/v13
cp chapter-22/kaggle/current/notebook.ipynb chapter-22/kaggle/v13/
cp chapter-22/kaggle/current/kernel-metadata.json chapter-22/kaggle/v13/
# Edit v13/notebook.ipynb, then:
rm chapter-22/kaggle/current && ln -s v13 chapter-22/kaggle/current
```

## Kaggle Submission

See `kaggle/v12/manual_submission_guide.md` for full instructions.
Select **GPU T4 x2** in the Kaggle UI (P100 is broken with PyTorch 2.10+cu128).
