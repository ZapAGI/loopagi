# ARC-AGI Model Research: Encyclopedia of Local LLM Models

**Date:** March 18, 2026
**Author:** Alexandros Karales + Cascade AI
**Machine:** Anubix-Alienware | Ubuntu 25.10 | RTX 5080 16GB | CUDA 12.0
**Ollama:** v0.17.7

---

## System Constraints

| Resource | Value | Impact |
|----------|-------|--------|
| VRAM | 16GB GDDR7 | Max ~14B Q4_K_M fully loaded |
| RAM | 64GB DDR5 | CPU offload possible for larger models |
| GPU Arch | Blackwell (sm_120) | Flash Attention 2.0 supported |
| Ollama | v0.17.7 | GGUF format, llama.cpp backend |
| ARC budget | ~6 min/task, ~180 LLM calls | Favor speed over quality for iteration |

---

## Model Categories for ARC

### Category 1: Reasoning Models (Perceiver + Hypothesizer)

These models excel at understanding patterns, analyzing relationships, and generating hypotheses.

| Model | Params | VRAM (Q4) | Think Mode | Reasoning Score | Status |
|-------|--------|-----------|------------|-----------------|--------|
| **qwen3:8b** | 8B | ~5GB | Yes (disable!) | High | INSTALLED |
| **qwen3:14b** | 14B | ~9GB | Yes (disable!) | Very High | INSTALLED |
| **deepseek-r1:14b** | 14B | ~9GB | Yes (disable!) | Very High | INSTALLED |
| **llama3.2:latest** | 8B | ~5GB | No | Good | INSTALLED |
| nemotron-3-nano | 8B | ~5GB | Yes | High (NVIDIA optimized) | TO DOWNLOAD |
| llama-nemotron:8b | 8B | ~5GB | Optional | High (reasoning fine-tune) | TO DOWNLOAD |
| phi-4:14b | 14B | ~9GB | No | Very High (MMLU 76.2) | TO DOWNLOAD |
| mistral-small:latest | 7B | ~5GB | No | Good (fastest) | TO DOWNLOAD |
| gemma3:12b | 12B | ~8GB | No | High | TO DOWNLOAD |

### Category 2: Code Generation Models (Synthesizer)

These models are specifically trained to write correct Python code from specifications.

| Model | Params | VRAM (Q4) | HumanEval | Code Focus | Status |
|-------|--------|-----------|-----------|------------|--------|
| **qwen2.5-coder:14b** | 14B | ~9GB | ~82% | Pure code | INSTALLED |
| qwen2.5-coder:7b | 7B | ~5GB | ~76% | Pure code | TO DOWNLOAD |
| codestral:latest | 22B | ~14GB | ~80% | Code (Mistral) | TO DOWNLOAD |
| deepseek-coder-v2:16b | 16B | ~10GB | ~78% | Code + reasoning | TO DOWNLOAD |
| starcoder2:15b | 15B | ~10GB | ~72% | Code (BigCode) | TO DOWNLOAD |
| granite-code:8b | 8B | ~5GB | ~68% | Code (IBM) | TO DOWNLOAD |
| codegemma:7b | 7B | ~5GB | ~64% | Code (Google) | TO DOWNLOAD |

### Category 3: NVIDIA Optimized Models

NVIDIA's Nemotron family is specifically optimized for agentic reasoning.

| Model | Params | VRAM (Q4) | Specialty | Status |
|-------|--------|-----------|-----------|--------|
| nemotron-3-nano | 8B | ~5GB | Unified reasoning + non-reasoning | TO DOWNLOAD |
| llama-nemotron:8b | 8B | ~5GB | Reasoning fine-tune of Llama 3.1 | TO DOWNLOAD |
| nemotron-mini:4b | 4B | ~3GB | Lightweight, fast | TO DOWNLOAD |

### Category 4: Small Fast Models (Rapid Iteration)

For quick hypothesis testing where speed matters more than quality.

| Model | Params | VRAM (Q4) | Speed (est.) | Status |
|-------|--------|-----------|-------------|--------|
| phi-4-mini:3.8b | 3.8B | ~3GB | ~80 t/s | TO DOWNLOAD |
| qwen3:4b | 4B | ~3GB | ~70 t/s | TO DOWNLOAD |
| gemma3:4b | 4B | ~3GB | ~70 t/s | TO DOWNLOAD |
| smollm2:1.7b | 1.7B | ~1.5GB | ~120 t/s | TO DOWNLOAD |
| llama3.2:3b | 3B | ~2.5GB | ~90 t/s | TO DOWNLOAD |

---

## Download Plan

### Priority 1: Core ARC Models (download first)

```bash
# Code generation (best for synthesizer)
ollama pull qwen2.5-coder:7b

# Reasoning (NVIDIA optimized)
ollama pull nemotron-3-nano
ollama pull llama-nemotron:8b

# Fast iteration
ollama pull phi-4-mini
ollama pull mistral-small
```

### Priority 2: Comparison Set

```bash
# Large code models (if VRAM allows)
ollama pull codestral
ollama pull deepseek-coder-v2:16b

# Reasoning alternatives
ollama pull phi-4:14b
ollama pull gemma3:12b

# Small fast models
ollama pull qwen3:4b
ollama pull gemma3:4b
ollama pull llama3.2:3b
```

### Priority 3: Specialized

```bash
# NVIDIA family
ollama pull nemotron-mini:4b

# Niche code models
ollama pull starcoder2:15b
ollama pull granite-code:8b
ollama pull codegemma:7b

# Ultra-small
ollama pull smollm2:1.7b
```

---

## Benchmarking Protocol

### Test Set

- 20 ARC training tasks (fixed set across all models)
- Tasks selected for diversity: simple color swap, shape scaling, object manipulation, pattern completion, symmetry

### Metrics Per Model

| Metric | How Measured |
|--------|-------------|
| **Accuracy** | Avg similarity across 20 tasks |
| **Solve rate** | % of tasks with 100% similarity (exact match) |
| **Speed** | Avg seconds per LLM call |
| **Total time** | Total seconds for 20 tasks |
| **VRAM** | Peak VRAM usage (nvidia-smi) |
| **Token efficiency** | Avg response length (shorter = better for code) |
| **Code validity** | % of synthesized programs that compile |
| **Hypothesis quality** | Avg similarity from FIRST hypothesis (before refinement) |

### Benchmark Script

```bash
# Run benchmark for a model
uv run python chapter-22/demo_solver.py \
  --model MODEL_NAME \
  --dataset training \
  --limit 20 \
  --max-hyp 3 \
  --max-iter 3

# Compare two models
uv run python chapter-22/benchmark_models.py \
  --models qwen3:8b,qwen2.5-coder:14b \
  --tasks 20 \
  --output reports/MODEL_NAME.json
```

### Report Template

Each model gets a report card:

```
=== Model: qwen2.5-coder:14b ===
Category: Code Generation
Parameters: 14B (Q4_K_M)
VRAM: 9.2GB

ARC Performance (20 tasks):
  Solve rate:     X/20 (X%)
  Avg similarity: XX.X%
  Best similarity: XX.X% (task ID)
  Avg time/task:  XX.Xs
  Code validity:  XX%

Strengths: ...
Weaknesses: ...
Recommended for: Synthesizer agent
```

---

## Two-Model Architecture Plan

Based on research, the optimal configuration for RTX 5080 (16GB):

### Option A: Speed (fits 2 models simultaneously)

| Agent | Model | VRAM | Role |
|-------|-------|------|------|
| Perceiver + Hypothesizer | qwen3:8b | ~5GB | Reasoning |
| Synthesizer + Refiner | qwen2.5-coder:7b | ~5GB | Code gen |
| **Total** | | **~10GB** | Leaves 6GB for context |

### Option B: Quality (swap models, one at a time)

| Agent | Model | VRAM | Role |
|-------|-------|------|------|
| Perceiver + Hypothesizer | deepseek-r1:14b | ~9GB | Best reasoning |
| Synthesizer + Refiner | qwen2.5-coder:14b | ~9GB | Best code gen |
| **Total** | | **~9GB** (swapped) | Models swap in/out |

### Option C: Single Best (simplest)

| Agent | Model | VRAM | Role |
|-------|-------|------|------|
| All agents | qwen3:14b | ~9GB | Good at both reasoning + code |

---

## Expected Results

Based on ARC Prize 2025 data and our current 60-70% similarity:

| Optimization | Expected Accuracy Gain |
|-------------|----------------------|
| Flash Attention enabled | +0% accuracy, +20% speed |
| Grid diffs in refiner | +5-10% similarity |
| Few-shot from similar tasks | +5-15% similarity |
| Two-model approach | +10-15% similarity |
| More iterations (5-7) | +5-10% similarity |
| **Combined** | **+20-40% similarity** |

Target: From ~65% avg similarity to **85-95%** avg similarity, with **5-15%** solve rate on training tasks.

For reference, the 2025 ARC Prize winner scored ~8% on ARC-AGI-2 (which is much harder than the training set).

---

*God in the Loop - ARC Model Research*
*Copyright 2026 Alexandros Karales. All Rights Reserved.*
