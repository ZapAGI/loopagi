# ARC-AGI Solver Improvements: Research and Implementation Plan

**Date:** March 18, 2026
**Author:** Alexandros Karales + Cascade AI
**Status:** Research complete, ready for implementation
**Branch:** feature/audit-and-arc-agi

---

## Current State

The multi-agent ARC solver (Phases 1-5) is working end-to-end with real LLM inference.

| Metric | Value |
|--------|-------|
| Modules | 15 in `loopagi/arc/` |
| Tests | 541 passing |
| Best similarity | 94.1% (task 00d62c1b) |
| Average similarity | ~60-70% on 5 training tasks |
| Tasks solved | 0 (exact match required) |
| LLM speed | ~1.8s/call with qwen3:8b (think=False) |
| Total time/task | ~12-30s |

### Root Causes of Failure

1. **Hypothesis too vague**: The perceiver describes the transformation but not precisely enough for code generation
2. **No examples in context**: The synthesizer doesn't see the actual grids when generating code
3. **Refinement doesn't show diffs**: The refiner says "wrong shape" but doesn't show exactly which cells differ
4. **Single model for all roles**: Using qwen3:8b for both reasoning and coding (not optimized for either)
5. **No few-shot from similar tasks**: The task similarity index exists but isn't wired into prompts

---

## Improvement 1: Feed Grid Diffs to Refiner

### Problem

The refiner currently gets:
```
Pair 0: FAIL (shape: (3,3) vs (3,3), similarity: 88.6%)
```

This tells the LLM *something* is wrong but not *what*. The model has to guess which cells are incorrect.

### Solution

Show the actual vs expected grids side-by-side with a diff mask:

```
Pair 0: FAIL
Expected:     Actual:       Diff (X = wrong):
1 2 3         1 2 3         . . .
4 5 6         4 0 6         . X .
7 8 9         7 8 9         . . .
```

### Implementation

1. Add `format_grid_diff()` to `verifier.py` that renders expected/actual/diff
2. Include diff output in `VerificationResult.failure_report()`
3. Feed the diff into `format_refinement_prompt()` in `refiner.py`
4. The LLM can now see *exactly* which cells are wrong

### Expected Impact

High. The LLM will know "cell (1,1) should be 5 but got 0" instead of "something is wrong."

---

## Improvement 2: Few-Shot from Similar Tasks

### Problem

The task similarity index (`task_similarity.py`) is built but not used. When solving a new task, the solver doesn't look at similar solved tasks for inspiration.

### Solution

Before synthesizing code, retrieve the 2-3 most similar training tasks and include their solutions as few-shot examples in the synthesis prompt:

```
Similar solved task (90% similar):
  Rule: "Replace color 2 with color 5 in enclosed regions"
  Code: def transform(grid): ...

Now solve THIS task:
  Rule: "Replace color 3 with color 7 in enclosed regions"
  [training pairs shown]
```

### Implementation

1. Pre-build the task similarity index from the 1000 training tasks
2. For each eval task, retrieve top 3 similar training tasks
3. Include the solved task's perception + hypothesis in the synthesis prompt
4. No actual solved code needed (we don't have solved code), but the hypotheses guide the LLM

### Expected Impact

Medium-High. Few-shot examples are the #1 way to improve LLM accuracy. Even showing similar task descriptions helps.

---

## Improvement 3: Two-Model Approach

### Problem

Using qwen3:8b for everything means we get mediocre reasoning AND mediocre code generation. Reasoning models (deepseek-r1) are better at perceiving patterns. Code models (qwen2.5-coder) are better at writing Python.

### Solution

Use different models for different agents:

| Agent | Best Model Type | Recommended |
|-------|----------------|-------------|
| **Perceiver** | Reasoning | deepseek-r1:14b or qwen3:14b |
| **Hypothesizer** | Reasoning | deepseek-r1:14b or qwen3:14b |
| **Synthesizer** | Code generation | qwen2.5-coder:14b |
| **Refiner** | Reasoning + code | qwen3:14b |

### Implementation

1. Add `model_config` dict to `LLMBridge` mapping agent role to model name
2. Create separate Ollama call functions per model
3. Keep models loaded in VRAM (Ollama's `OLLAMA_MAX_LOADED_MODELS=2`)
4. Profile: can we fit 2 models in 16GB? (14B Q4 = ~9GB, tight but possible one at a time)

### Expected Impact

High. Code-specialized models generate 10-20% more correct code. Reasoning models perceive patterns better.

---

## Improvement 4: Increase Iterations for Hard Tasks

### Problem

Currently using 2-3 iterations per hypothesis and 2 hypotheses. Many tasks need more exploration to converge.

### Solution

Adaptive iteration count based on task complexity:

| Task Complexity | Hypotheses | Iterations | Total LLM Calls |
|----------------|-----------|------------|-----------------|
| Simple (same shape, few colors) | 3 | 3 | ~30 |
| Medium (shape changes, objects) | 5 | 5 | ~75 |
| Hard (complex patterns) | 7 | 7 | ~150 |

Complexity is estimated from the perception report (grid size, color count, object count, shape changes).

### Implementation

1. Add `estimate_complexity()` to `perceiver.py` returning low/medium/high
2. Map complexity to iteration/hypothesis counts in `solve_task_with_llm()`
3. Add early termination: if similarity improves < 5% between iterations, try next hypothesis

### Expected Impact

Medium. More iterations = more chances to converge, but diminishing returns after ~5.

---

## Improvement 5: Ollama Performance Optimization

### Current Setup

```
Machine:  Anubix-Alienware
OS:       Ubuntu 25.10 (Questing Quokka)
GPU:      NVIDIA GeForce RTX 5080, 16GB VRAM, CUDA 12.0, Compute 12.0
Ollama:   v0.17.7
Backend:  llama.cpp (built into Ollama, uses GGUF format)
Service:  systemd (/etc/systemd/system/ollama.service)
```

### CRITICAL FINDING: Flash Attention NOT Enabled

The systemd service has **no** `OLLAMA_FLASH_ATTENTION=1` environment variable. This means Ollama is NOT using Flash Attention 2.0, which:

- Reduces memory usage by ~30% for long contexts
- Speeds up inference by 10-30% on Ampere+ GPUs (RTX 5080 is Blackwell, supports FA)
- Enables longer context windows in the same VRAM

### Ollama Architecture: llama.cpp Under the Hood

Ollama IS llama.cpp. It's not a wrapper around a separate llama.cpp binary. Ollama compiles llama.cpp's GGML backend directly into its Go binary. Running llama.cpp separately would NOT give 80% speedup because:

1. **Same inference engine**: Ollama uses the same CUDA kernels as standalone llama.cpp
2. **Same quantization**: Both use GGUF format with identical dequantization
3. **Ollama overhead is minimal**: The Go HTTP server adds < 1ms per request
4. **Where llama.cpp standalone wins**: Custom compilation flags (e.g., specific CUDA arch), batch scheduling, and avoiding Ollama's model management overhead

### Performance Optimizations to Apply

#### 1. Enable Flash Attention (immediate, high impact)

```bash
# Edit the systemd service
sudo systemctl edit ollama

# Add:
[Service]
Environment="OLLAMA_FLASH_ATTENTION=1"

# Restart
sudo systemctl restart ollama
```

Expected: **10-30% faster inference, 30% less VRAM for long contexts**

#### 2. Set Optimal Context Window

For ARC tasks, prompts are ~500-2000 tokens. Default context is 2048-4096. Setting it explicitly avoids wasted VRAM:

```json
{"options": {"num_ctx": 4096}}
```

#### 3. Enable Parallel Requests

```bash
sudo systemctl edit ollama

[Service]
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_MAX_LOADED_MODELS=2"
```

This lets us keep 2 models loaded (reasoning + code) and serve requests in parallel.

#### 4. Quantization Strategy

For RTX 5080 (16GB VRAM):

| Model | Q4_K_M Size | Q5_K_M Size | Fits? |
|-------|------------|------------|-------|
| 7-8B models | ~5GB | ~6GB | Yes (3x) |
| 14B models | ~9GB | ~11GB | Yes (1-2x) |
| 32B models | ~20GB | ~24GB | No (partial offload) |

**Recommendation**: Use Q4_K_M for speed, Q5_K_M only if accuracy drops noticeably.

---

## Improvement 6: llama.cpp Standalone vs Ollama

### Verdict: Stay with Ollama

The claim that "llama.cpp is 80% faster" is a myth. Ollama IS llama.cpp. The only scenarios where standalone llama.cpp wins:

1. **Custom CUDA arch compilation**: Building for `sm_120` (Blackwell) specifically. Check if Ollama's bundled build already targets this.
2. **ik_llama.cpp fork**: Uses improved quantization for hybrid CPU+GPU inference. Only relevant if offloading to CPU.
3. **vLLM**: For high-throughput batch inference (many tasks simultaneously). overkill for our use case.
4. **Speculative decoding**: llama.cpp supports this natively; Ollama doesn't expose it yet.

### When to Switch

Switch to standalone llama.cpp or vLLM ONLY if:
- Running 100+ tasks in batch (Kaggle submission)
- Need speculative decoding for faster generation
- Need custom CUDA compilation for Blackwell-specific optimizations

For development and iteration, Ollama's API convenience outweighs any marginal speed gain.

---

## Implementation Roadmap

### Phase A: Quick Wins (1-2 hours)

- [ ] Enable Flash Attention in Ollama systemd service
- [ ] Set OLLAMA_NUM_PARALLEL=2, OLLAMA_MAX_LOADED_MODELS=2
- [ ] Add grid diff visualization to refiner prompts
- [ ] Add complexity estimator for adaptive iterations

### Phase B: Few-Shot Integration (2-3 hours)

- [ ] Pre-build task similarity index from 1000 training tasks (cache to disk)
- [ ] Wire similar task retrieval into synthesis prompts
- [ ] Add perception reports from similar tasks as context

### Phase C: Two-Model Approach (2-3 hours)

- [ ] Add per-agent model config to LLMBridge
- [ ] Download and test qwen2.5-coder:14b for synthesis
- [ ] Download and test deepseek-r1:14b for perception/hypothesis
- [ ] Profile VRAM usage with 2 models

### Phase D: Model Benchmarking (4-6 hours)

- [ ] Download all candidate models (see ARC_MODEL_RESEARCH.md)
- [ ] Run each model on 20 training tasks
- [ ] Record: similarity, time/task, LLM calls, VRAM usage
- [ ] Compile results into benchmark report
- [ ] Select optimal model(s) for each agent role

### Phase E: Full Evaluation (2-3 hours)

- [ ] Run optimized solver on all 120 eval tasks
- [ ] Measure accuracy, compute cost, time
- [ ] Compare single-agent vs multi-agent performance
- [ ] Write results for book chapter

---

## References

1. **Ollama Performance Tuning**: collabnix.com/ollama-performance-tuning-gpu-optimization-techniques-for-production/
2. **llama.cpp CUDA Performance**: github.com/ggml-org/llama.cpp/discussions/15013
3. **vLLM vs llama.cpp vs Ollama**: arsturn.com/blog/multi-gpu-showdown-benchmarking-vllm-llama-cpp-ollama-for-maximum-performance
4. **Best Local LLM Models 2026**: sitepoint.com/best-local-llm-models-2026/
5. **ARC Prize 2025 Research Review**: lewish.io/posts/arc-agi-2025-research-review

---

*God in the Loop - ARC Solver Improvements Research*
*Copyright 2026 Alexandros Karales. All Rights Reserved.*
