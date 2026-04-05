# ARC-AGI Solver: Polars Integration & Improvement Research

**Date:** March 19, 2026
**Author:** Alexandros Karales + Cascade AI
**Branch:** feature/audit-and-arc-agi
**Status:** Research complete — ready for implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Polars for ARC-AGI](#polars-for-arc-agi)
4. [Improvement 1: Best-of-N Sampling](#improvement-1-best-of-n-sampling)
5. [Improvement 2: Direct Grid Transduction](#improvement-2-direct-grid-transduction)
6. [Improvement 3: Program Mutation / Evolution](#improvement-3-program-mutation--evolution)
7. [Improvement 4: Larger Model for Synthesis](#improvement-4-larger-model-for-synthesis)
8. [Improvement 5: Relaxed Stagnation Detection](#improvement-5-relaxed-stagnation-detection)
9. [Improvement 6: Grid-as-Object Representation](#improvement-6-grid-as-object-representation)
10. [Polars Data Pipeline Architecture](#polars-data-pipeline-architecture)
11. [References](#references)

---

## Executive Summary

Our ARC-AGI multi-agent solver currently achieves **66.98% mean similarity** across
120 training tasks with **0 exact solves**. We have **10 tasks at 95%+ similarity**
and **33 tasks at 90%+** — tantalizingly close to actual solves.

This document researches two parallel tracks:

1. **Polars DataFrames** as the analytical backbone for grid analysis, eval tracking,
   candidate ranking, and similarity computation
2. **Six solver improvements** informed by ARC Prize 2025 winning techniques
   (refinement loops, evolutionary synthesis, transduction)

The 2025 ARC Prize theme was **"Year of the Refinement Loop"** — our architecture
already implements this. The gap is in *how many candidates we explore* and
*how we select among them*. Polars gives us the fast, parallel data engine to
close that gap.

---

## Current State Analysis

### Eval Results (No-Few-Shot Baseline)

| Metric | Value |
|---|---|
| Model | qwen3:8b (think=False) |
| Tasks evaluated | 120 |
| Solve rate | 0.0% |
| Mean similarity | 66.98% |
| Tasks ≥ 95% similarity | 10 |
| Tasks ≥ 90% similarity | 33 |
| Tasks ≥ 80% similarity | 52 |
| Tasks ≥ 50% similarity | 85 |
| Mean iterations | 14.8 |
| Time/task | 110.9s |

### Near-Miss Analysis (Top 10)

| Task ID | Similarity | Iterations | Time | Complexity |
|---|---|---|---|---|
| 8e5c0c38 | 98.7% | 11 | 152s | medium |
| 135a2760 | 98.2% | 13 | 100s | medium |
| 38007db0 | 98.1% | 27 | 149s | high |
| 9bbf930d | 97.5% | 21 | 180s | high |
| 409aa875 | 97.4% | 11 | 77s | medium |
| 7b80bb43 | 97.3% | 13 | 76s | medium |
| e376de54 | 96.5% | 13 | 147s | medium |
| 97d7923e | 96.1% | 11 | 75s | medium |
| 3e6067c3 | 95.9% | 15 | 107s | high |
| 332f06d7 | 95.3% | 11 | 94s | medium |

**Key insight:** These tasks are 1-5 cells away from perfect. The solver finds
the right *pattern* but makes small errors in the generated code.

### Root Causes of Near-Misses

1. **Off-by-one in loop bounds** — correct pattern, wrong iteration count
2. **Color constant errors** — correct logic, wrong color value substituted
3. **Edge handling** — correct interior transform, border cells missed
4. **Output shape** — correct values, wrong grid dimensions
5. **Single-sample fragility** — one code generation attempt, no diversity

---

## Polars for ARC-AGI

### Why Polars?

**Polars** (v1.39.2, Feb 2026) is a Rust-backed DataFrame library designed for
analytical workloads. It outperforms pandas by 10-100x on typical operations
due to:

- **Parallel execution** — automatic multi-threaded operations using all CPU cores
- **Lazy evaluation** — query optimization before execution (predicate pushdown,
  projection pushdown, common subexpression elimination)
- **Apache Arrow memory** — columnar format, zero-copy operations
- **Expression DSL** — composable, functional data transformations
- **Streaming** — handles larger-than-RAM datasets

**Source:** [pola.rs](https://pola.rs), [PyPI polars 1.39.2](https://pypi.org/project/polars/)

### How Polars Fits the ARC Solver

Polars serves **three roles** in the improved ARC solver:

#### Role 1: Grid Analysis Engine

ARC grids are 2D integer arrays (max 30x30). Polars can represent grid data
as structured DataFrames for fast vectorized analysis:

```python
import polars as pl

# Represent a grid as a Polars DataFrame
def grid_to_df(grid: list[list[int]], label: str = "") -> pl.DataFrame:
    """Convert a 2D grid to a Polars DataFrame with row/col/value columns."""
    rows, cols, vals = [], [], []
    for r, row in enumerate(grid):
        for c, val in enumerate(row):
            rows.append(r)
            cols.append(c)
            vals.append(val)
    return pl.DataFrame({
        "row": rows,
        "col": cols,
        "value": vals,
        "label": [label] * len(rows),
    })

# Vectorized grid comparison
def grid_diff_df(expected: list[list[int]], actual: list[list[int]]) -> pl.DataFrame:
    """Compute cell-level diff between two grids using Polars."""
    exp_df = grid_to_df(expected, "expected")
    act_df = grid_to_df(actual, "actual")
    return (
        exp_df.join(act_df, on=["row", "col"], suffix="_actual")
        .with_columns([
            (pl.col("value") != pl.col("value_actual")).alias("is_wrong"),
            (pl.col("value") - pl.col("value_actual")).alias("delta"),
        ])
        .filter(pl.col("is_wrong"))
    )
```

**Benefits:**
- Vectorized diff computation across all training pairs simultaneously
- Fast aggregation: count wrong cells, group by color, identify spatial patterns
- Lazy evaluation means grid analysis chains don't materialize intermediate results

#### Role 2: Candidate Ranking & Selection

When generating multiple candidate programs (Best-of-N), Polars provides
fast ranking across all candidates:

```python
def rank_candidates(candidates: list[dict]) -> pl.DataFrame:
    """Rank candidate programs by similarity, with tiebreaking."""
    return (
        pl.DataFrame(candidates)
        .with_columns([
            pl.col("similarity").rank(descending=True).alias("sim_rank"),
            pl.col("wrong_cells").rank().alias("cell_rank"),
            (pl.col("similarity") * 0.7 + (1 - pl.col("wrong_cells") / pl.col("total_cells")) * 0.3)
                .alias("composite_score"),
        ])
        .sort("composite_score", descending=True)
    )
```

**Benefits:**
- Multi-criteria ranking (similarity, wrong cells, shape match, execution time)
- Window functions for tracking improvement over iterations
- Lazy groupby for per-task and per-hypothesis analysis

#### Role 3: Evaluation Analytics

Replace JSON-based eval tracking with Polars DataFrames for real-time
analysis during evaluation runs:

```python
def load_eval_results(jsonl_path: str) -> pl.LazyFrame:
    """Load JSONL eval results into a Polars LazyFrame."""
    return pl.scan_ndjson(jsonl_path)

def eval_summary(lf: pl.LazyFrame) -> pl.DataFrame:
    """Compute comprehensive eval summary."""
    return (
        lf.group_by("complexity")
        .agg([
            pl.col("similarity").mean().alias("mean_sim"),
            pl.col("similarity").median().alias("median_sim"),
            (pl.col("similarity") >= 0.9).sum().alias("near_misses"),
            (pl.col("similarity") >= 1.0).sum().alias("solved"),
            pl.col("iterations").mean().alias("mean_iters"),
            pl.col("time_seconds").sum().alias("total_time"),
            pl.len().alias("task_count"),
        ])
        .sort("complexity")
        .collect()
    )
```

**Benefits:**
- `scan_ndjson()` for lazy JSONL loading — no need to load full file into memory
- Real-time streaming analytics during long eval runs
- Easy comparison between eval runs (join on task_id)

### Polars vs Alternatives

| Feature | Polars | pandas | NumPy |
|---|---|---|---|
| **Speed** | 10-100x faster | Baseline | Fast for numerics |
| **Lazy eval** | ✅ Full query optimizer | ❌ | ❌ |
| **Parallel** | ✅ Auto multi-thread | ❌ Single-thread | Limited |
| **Memory** | Arrow columnar | Python objects | Contiguous C arrays |
| **Streaming** | ✅ Larger-than-RAM | ❌ | ❌ |
| **Expression API** | ✅ Composable DSL | Chaining only | Array ops |
| **Grid analysis** | Good (structured) | Good (structured) | Best (raw arrays) |
| **Candidate ranking** | Excellent | Good | Poor |
| **JSONL loading** | `scan_ndjson()` native | `read_json()` slow | ❌ |

**Verdict:** Polars is the best choice for eval analytics and candidate ranking.
For raw grid operations (pixel-level transforms), NumPy remains faster. We use
**both**: NumPy for grid transforms, Polars for everything above grid-level.

---

## Improvement 1: Best-of-N Sampling

### Research

The #1 technique from ARC Prize 2025. Ryan Greenblatt's approach scored 43%
on ARC-AGI-1 by having GPT-4o generate **k=2,048 solution programs per task**
and deterministically verifying them.

The relationship between k (sample count) and accuracy follows a **log-linear**
curve — more samples = more solves, with diminishing returns.

**Source:** [ARC Prize 2025 Results](https://arcprize.org/blog/arc-prize-2025-results-analysis)

Our solver currently generates **1 program per iteration**. Even generating
**5 programs per synthesis step** would dramatically increase our chances
of hitting 100% similarity for near-miss tasks.

### How It Works

```
For each hypothesis:
  For each iteration:
    Generate N candidate programs (not just 1)
    Verify ALL N against training pairs
    Keep the best-scoring candidate
    If any candidate scores 100% → solved
    Use the best candidate's failures for refinement
```

### Polars Role

Polars manages the **candidate pool** — a DataFrame of all generated programs
with their verification scores, execution times, and failure details:

```python
import polars as pl

candidate_schema = {
    "hypothesis_id": pl.Int32,
    "iteration": pl.Int32,
    "sample_id": pl.Int32,
    "source_code": pl.Utf8,
    "similarity": pl.Float64,
    "wrong_cells": pl.Int32,
    "shape_match": pl.Boolean,
    "exec_time_ms": pl.Float64,
    "error": pl.Utf8,
}

def select_best_candidate(pool: pl.DataFrame) -> pl.DataFrame:
    """Select the best candidate using composite scoring."""
    return (
        pool
        .filter(pl.col("error").is_null())  # Only valid programs
        .with_columns([
            # Composite: 70% similarity + 20% shape match + 10% speed
            (
                pl.col("similarity") * 0.7
                + pl.col("shape_match").cast(pl.Float64) * 0.2
                + (1.0 / (1.0 + pl.col("exec_time_ms") / 1000)).alias("speed_score") * 0.1
            ).alias("composite"),
        ])
        .sort("composite", descending=True)
        .head(1)
    )
```

### Expected Impact

- **Near-misses (95%+):** With N=5, probability of at least one perfect sample
  increases from ~2% to ~10% per iteration (rough estimate)
- **Medium tasks (70-90%):** Best-of-N smooths out code generation variance
- **Cost:** 5x more LLM calls per iteration. At ~1.8s/call, adds ~9s/iteration.
  Acceptable for 10-15 iterations.

### Key Parameters

| Parameter | Conservative | Aggressive |
|---|---|---|
| Samples per synthesis | 3 | 8 |
| Samples per refinement | 2 | 5 |
| Temperature for diversity | 0.3-0.8 | 0.1-1.0 |
| Max total candidates/task | 50 | 200 |

---

## Improvement 2: Direct Grid Transduction

### Research

Instead of synthesizing a Python `transform()` function, ask the LLM to
**directly predict the output grid**. This is the "transductive" approach
that frontier models (O3, Gemini) use on ARC.

For simple tasks (color swaps, reflections, fills), the LLM can often
"see" the pattern and produce the correct output without writing code.

**Source:** [How to Beat ARC-AGI](https://arcprize.org/blog/beat-arc-agi-deep-learning-and-program-synthesis) — Chollet & Knoop discuss combining DL perception with program synthesis. The transductive approach is the "system 1" (fast, intuitive) counterpart to program synthesis ("system 2").

### How It Works

```
Phase 0: Try direct transduction first
  Show the LLM all training I/O pairs
  Ask it to predict the test output directly (as a grid)
  Verify the prediction against training pairs
  If training verification passes → use as prediction

Phase 1-5: Fall back to program synthesis (existing pipeline)
  Only if transduction fails
```

### Prompt Format

```
Task: Given these input-output pairs, predict the output for the test input.

Train 1:
Input:  [[0,0,1],[0,1,0],[1,0,0]]
Output: [[1,0,0],[0,1,0],[0,0,1]]

Train 2:
Input:  [[0,2,0],[2,0,2],[0,2,0]]
Output: [[0,2,0],[2,0,2],[0,2,0]]

Test Input: [[3,0,0],[0,3,0],[0,0,3]]

Reply with ONLY the output grid as a JSON array of arrays.
```

### Polars Role

Polars validates transduction results by comparing predicted grids against
all training pairs simultaneously:

```python
def validate_transduction(
    predicted: list[list[int]],
    train_pairs: list[tuple[list, list]],
) -> pl.DataFrame:
    """Validate a transduced output against training pairs."""
    results = []
    for i, (inp, expected_out) in enumerate(train_pairs):
        diff = grid_diff_df(expected_out, predicted)
        results.append({
            "pair_idx": i,
            "total_cells": len(expected_out) * len(expected_out[0]),
            "wrong_cells": diff.height,
            "similarity": 1.0 - diff.height / (len(expected_out) * len(expected_out[0])),
        })
    return pl.DataFrame(results)
```

### Expected Impact

- **Simple tasks (low complexity):** 20-30% could be solved directly
- **Medium/high tasks:** Transduction fails, falls through to code synthesis
- **Cost:** 1 extra LLM call per task (cheap). If it works, saves all
  synthesis/refinement iterations
- **Risk:** Low — it's a fast first-pass that doesn't replace existing pipeline

---

## Improvement 3: Program Mutation / Evolution

### Research

**SOAR** (Self-improving language models for evolutionary program synthesis)
achieved **52% on ARC-AGI-1 public test** by combining:

1. **Evolutionary search** — mutate and recombine candidate programs
2. **Self-improving LLM** — fine-tune on successful synthesis attempts
3. **Hindsight learning** — convert failed attempts into training data

We can't fine-tune locally, but we CAN implement the evolutionary search:
**take high-similarity programs and systematically mutate them**.

**Source:** [SOAR Paper](https://arxiv.org/abs/2507.14172) — Pourcel, Colas, Oudeyer (2025)

The ARC Prize 2025 report confirms: "Evolutionary Test-Time Compute" and
"Evolutionary Program Synthesis" were the **central theme** driving AGI
progress in 2025.

**Source:** [ARC Prize 2025 Results](https://arcprize.org/blog/arc-prize-2025-results-analysis)

### How It Works

When a program achieves ≥ 90% similarity:

```
1. Parse the program AST
2. Identify mutable elements:
   - Integer constants (color values, offsets, sizes)
   - Comparison operators (>, >=, <, <=, ==, !=)
   - Loop bounds (range start, stop, step)
   - Boolean conditions (and/or, negate)
3. Generate N mutations (change one element at a time)
4. Verify each mutation against training pairs
5. Keep mutations that improve similarity
6. Repeat until 100% or budget exhausted
```

### Mutation Types

| Mutation | Example | When |
|---|---|---|
| **Constant sweep** | Change `color = 3` to `color = 1,2,4,5,...` | Color errors |
| **Offset adjust** | Change `r + 1` to `r + 0` or `r + 2` | Off-by-one |
| **Bound fix** | Change `range(n)` to `range(n-1)` or `range(n+1)` | Edge handling |
| **Operator flip** | Change `>` to `>=` or `<` to `<=` | Boundary conditions |
| **Negate** | Change `if cond:` to `if not cond:` | Logic inversion |

### Polars Role

Polars tracks the **mutation population** — every variant, its lineage, and
its verification score:

```python
mutation_schema = {
    "parent_id": pl.Int32,
    "mutation_type": pl.Utf8,       # "constant", "offset", "bound", "operator", "negate"
    "mutation_target": pl.Utf8,     # What was mutated (e.g., "line 5, color=3→5")
    "source_code": pl.Utf8,
    "similarity": pl.Float64,
    "improvement": pl.Float64,      # Delta from parent
    "generation": pl.Int32,
}

def evolve_population(pop: pl.DataFrame) -> pl.DataFrame:
    """Select top candidates for next generation."""
    return (
        pop
        .sort("similarity", descending=True)
        .head(10)  # Keep top 10 as parents for next generation
        .with_columns(pl.col("generation") + 1)
    )
```

### Expected Impact

- **95%+ tasks:** HIGH — these are 1-5 cells wrong, often fixable by sweeping
  a single constant
- **90-95% tasks:** MEDIUM — may need 2-3 mutations combined
- **Cost:** Mutations are verified by executing code (no LLM call needed),
  so thousands of mutations per second are feasible
- **This is the single highest-ROI improvement for getting first solves**

---

## Improvement 4: Larger Model for Synthesis

### Research

Our benchmark shows qwen3:8b achieves 79.4% best accuracy across 5 test tasks.
The 14B parameter class offers meaningfully better code generation:

- **qwen3:14b** — same architecture, ~1.75x parameters, Q4_K_M ≈ 9GB VRAM
- **qwen2.5-coder:14b** — code-specialized, excellent at Python generation
- **deepseek-r1:14b** — reasoning model, better at pattern perception

We already have `ModelConfig` and `LLMBridge.call_as(role, prompt)` — the
infrastructure for per-agent model routing exists.

**Hardware:** RTX 5080 16GB VRAM. Two models fit if both are 7-8B (Q4_K_M ≈ 5GB each).
One 14B model fits alone (Q4_K_M ≈ 9GB). With `OLLAMA_MAX_LOADED_MODELS=2`,
we can hot-swap between a reasoning model and a code model.

### Recommended Model Configuration

| Agent | Current | Proposed | Rationale |
|---|---|---|---|
| Perceiver | qwen3:8b | qwen3:14b | Better pattern description |
| Hypothesizer | qwen3:8b | qwen3:14b | Better abstract reasoning |
| Synthesizer | qwen3:8b | **qwen2.5-coder:14b** | Code-specialized |
| Verifier | N/A (deterministic) | N/A | No LLM needed |
| Refiner | qwen3:8b | qwen3:14b | Better error analysis |

### Polars Role

Polars tracks per-model performance across tasks for A/B comparison:

```python
model_perf_schema = {
    "task_id": pl.Utf8,
    "model": pl.Utf8,
    "role": pl.Utf8,
    "similarity": pl.Float64,
    "latency_ms": pl.Float64,
    "tokens_in": pl.Int32,
    "tokens_out": pl.Int32,
}

def compare_models(perf: pl.DataFrame) -> pl.DataFrame:
    """Compare model performance by role."""
    return (
        perf
        .group_by(["model", "role"])
        .agg([
            pl.col("similarity").mean().alias("mean_sim"),
            pl.col("latency_ms").mean().alias("mean_latency"),
            pl.col("latency_ms").quantile(0.95).alias("p95_latency"),
            pl.len().alias("n_tasks"),
        ])
        .sort(["role", "mean_sim"], descending=[False, True])
    )
```

### Expected Impact

- **Synthesis quality:** +10-15% similarity for code generation (based on
  benchmarking 7B vs 14B code models)
- **Perception quality:** Better hypothesis = better code = more solves
- **Cost:** ~2x slower per call (14B vs 8B), but fewer iterations needed
  if quality improves. Net time may be similar.

---

## Improvement 5: Relaxed Stagnation Detection

### Research

Our current stagnation detection:
- Abandons hypothesis after **2 consecutive iterations** with < 5% improvement
- This is correct for low-similarity tasks (exploring more hypotheses is better)
- But **wrong for near-misses** — at 95% similarity, a 2% improvement is huge

### Current Code (llm_bridge.py:396-407)

```python
improvement = verification.avg_similarity - prev_iter_sim
prev_iter_sim = verification.avg_similarity
if iteration > 0 and improvement < 0.05:
    stagnant_count += 1
    if stagnant_count >= 2:
        break  # Abandon hypothesis
else:
    stagnant_count = 0
```

### Proposed Fix: Adaptive Stagnation

```python
# Adaptive stagnation threshold based on current similarity
if prev_iter_sim >= 0.90:
    stagnation_threshold = 0.01   # 1% improvement matters at 90%+
    max_stagnant = 4              # More patience for near-misses
elif prev_iter_sim >= 0.70:
    stagnation_threshold = 0.03   # 3% threshold for medium tasks
    max_stagnant = 3
else:
    stagnation_threshold = 0.05   # Current behavior for low tasks
    max_stagnant = 2

improvement = verification.avg_similarity - prev_iter_sim
if iteration > 0 and improvement < stagnation_threshold:
    stagnant_count += 1
    if stagnant_count >= max_stagnant:
        break
else:
    stagnant_count = 0
```

### Polars Role

Polars tracks iteration-over-iteration improvement curves:

```python
def iteration_curves(results: pl.DataFrame) -> pl.DataFrame:
    """Analyze improvement curves across iterations."""
    return (
        results
        .sort(["task_id", "iteration"])
        .with_columns([
            pl.col("similarity")
                .diff()
                .over("task_id")
                .alias("delta_sim"),
            pl.col("similarity")
                .rolling_mean(window_size=3)
                .over("task_id")
                .alias("rolling_sim"),
        ])
    )
```

### Expected Impact

- **Trivial to implement** — single code change
- **Near-misses:** +5-10% chance of solving per task (more iterations at
  the critical 95%+ range)
- **Cost:** Slightly longer per task for high-similarity cases (1-2 extra
  iterations × ~10s each)

---

## Improvement 6: Grid-as-Object Representation

### Research

Raw grids are hard for LLMs to parse. Object-centric representations can
**double LLM performance** on ARC tasks.

**Source:** [ARC-AGI 2025 Research Review](https://lewish.io/posts/arc-agi-2025-research-review) — "one person claimed a doubling of O1 performance by mapping ARC grids into an abstract, object centric representation using a set of hand crafted heuristics"

We already have `loopagi/arc/grid_objects.py` (18 functions for object
detection) and `loopagi/arc/grid_ops.py` (37 grid operations). The gap is
that the **perceiver and synthesizer prompts don't use them**.

### Object Representation Format

Instead of:
```
[[0,0,0,1,0],[0,0,1,1,0],[0,1,1,1,0],[0,0,0,0,0]]
```

Send:
```
Grid: 4x5, background=0 (black), 2 colors used
Objects:
  - Object 1: L-shaped, color=1 (blue), cells={(0,3),(1,2),(1,3),(2,1),(2,2),(2,3)}, bbox=(0,1)→(2,3)
Spatial: Object 1 is a right-triangle growing down-left
```

### How It Works

```
1. Parse grid into objects using grid_objects.py (connected components)
2. Compute object properties (shape, color, size, bbox, centroid)
3. Compute spatial relationships (above, below, left, right, contains, overlaps)
4. Format as structured text for the LLM
5. Include BOTH object representation AND compact grid in prompts
```

### Polars Role

Polars manages the **object database** for each task — every detected object
with its properties, enabling fast cross-pair analysis:

```python
object_schema = {
    "pair_idx": pl.Int32,
    "grid_type": pl.Utf8,       # "input" or "output"
    "object_id": pl.Int32,
    "color": pl.Int32,
    "cell_count": pl.Int32,
    "bbox_r1": pl.Int32,
    "bbox_c1": pl.Int32,
    "bbox_r2": pl.Int32,
    "bbox_c2": pl.Int32,
    "centroid_r": pl.Float64,
    "centroid_c": pl.Float64,
    "shape": pl.Utf8,           # "rectangle", "L-shape", "line", "irregular"
}

def object_transforms(objects: pl.DataFrame) -> pl.DataFrame:
    """Detect how objects change between input and output."""
    inputs = objects.filter(pl.col("grid_type") == "input")
    outputs = objects.filter(pl.col("grid_type") == "output")

    return (
        inputs.join(outputs, on=["pair_idx", "color"], suffix="_out")
        .with_columns([
            (pl.col("centroid_r_out") - pl.col("centroid_r")).alias("move_r"),
            (pl.col("centroid_c_out") - pl.col("centroid_c")).alias("move_c"),
            (pl.col("cell_count_out") - pl.col("cell_count")).alias("size_delta"),
            (pl.col("color") != pl.col("color_out")).alias("color_changed"),
        ])
    )
```

### Expected Impact

- **Perception quality:** +20-40% better hypothesis generation (LLM understands
  objects, not just pixels)
- **Synthesis quality:** Object-aware code is more likely to be correct
- **Cost:** Small — object detection is O(n²) for grid size, negligible vs LLM calls
- **Existing infrastructure:** `grid_objects.py` already implements connected
  components, bounding boxes, and basic shape detection

---

## Polars Data Pipeline Architecture

### Overview

```
                                    ┌─────────────────────┐
                                    │   ARC Task Loader    │
                                    │   (arc_loader.py)    │
                                    └──────────┬──────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │   Grid → Polars DF   │
                                    │   (grid_to_df)       │
                                    │   Object Detection   │
                                    └──────────┬──────────┘
                                               │
                              ┌────────────────┼────────────────┐
                              │                │                │
                   ┌──────────▼─────┐  ┌───────▼──────┐  ┌─────▼──────────┐
                   │  Transduction  │  │  Code Synth  │  │   Evolution    │
                   │  (Imp #2)      │  │  (Imp #1)    │  │   (Imp #3)     │
                   │  Direct grid   │  │  Best-of-N   │  │   Mutations    │
                   │  prediction    │  │  sampling     │  │   on near-miss │
                   └──────────┬─────┘  └───────┬──────┘  └─────┬──────────┘
                              │                │                │
                              └────────────────┼────────────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │   Candidate Pool     │
                                    │   (Polars DataFrame) │
                                    │   Rank & Select      │
                                    └──────────┬──────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │   Verification       │
                                    │   (verifier.py)      │
                                    │   Grid diff → Polars │
                                    └──────────┬──────────┘
                                               │
                              ┌────────────────┼────────────────┐
                              │                │                │
                        ┌─────▼─────┐   ┌──────▼──────┐  ┌─────▼─────┐
                        │  Solved!  │   │  Refine     │  │  Evolve   │
                        │  100%     │   │  (Imp #5)   │  │  (Imp #3) │
                        └───────────┘   │  Adaptive   │  └───────────┘
                                        │  stagnation │
                                        └─────────────┘
```

### Core Polars Module: `arc_analytics.py`

A new module that provides the Polars-powered analytics layer:

```python
# loopagi/arc/arc_analytics.py

import polars as pl
from pathlib import Path

class ArcAnalytics:
    """Polars-powered analytics engine for ARC solver."""

    def __init__(self):
        self.candidates: pl.DataFrame = pl.DataFrame()
        self.iterations: pl.DataFrame = pl.DataFrame()
        self.mutations: pl.DataFrame = pl.DataFrame()

    def add_candidate(self, task_id, hyp_id, sample_id, code, sim, **kwargs): ...
    def add_iteration(self, task_id, iteration, similarity, **kwargs): ...
    def add_mutation(self, task_id, parent_id, mutation_type, code, sim): ...
    def best_candidate(self, task_id) -> dict: ...
    def near_misses(self, threshold=0.9) -> pl.DataFrame: ...
    def improvement_curve(self, task_id) -> pl.DataFrame: ...
    def export_report(self, path: Path): ...
    def compare_runs(self, other_jsonl: str) -> pl.DataFrame: ...
```

---

## References

1. **ARC Prize 2025 Results & Analysis** — arcprize.org/blog/arc-prize-2025-results-analysis
   - "Year of the Refinement Loop" — evolutionary search + verification loops
   - Ryan Greenblatt: k=2048 samples, 43% solve rate, log-linear scaling
   - SOAR: 52% on public test set via evolutionary program synthesis

2. **How to Beat ARC-AGI** — arcprize.org/blog/beat-arc-agi-deep-learning-and-program-synthesis
   - Chollet & Knoop: combine DL perception (System 1) with program synthesis (System 2)
   - Program space embedding for efficient search
   - "ARC can be beaten with a 7B model and <10k LOC"

3. **SOAR Paper** — arxiv.org/abs/2507.14172 (Pourcel, Colas, Oudeyer)
   - Self-improving evolutionary loop: search + hindsight learning
   - 52% on ARC-AGI-1 public test
   - Key: program mutation + recombination guided by LLM

4. **ARC-AGI 2025 Research Review** — lewish.io/posts/arc-agi-2025-research-review
   - Object-centric representations double LLM performance
   - Grid → abstract representation → solve → decode pipeline
   - Iterative grid refinement for linear-dependent transforms

5. **Polars Documentation** — pola.rs, docs.pola.rs
   - v1.39.2 (Feb 2026)
   - Lazy evaluation, parallel execution, Apache Arrow memory
   - `scan_ndjson()` for streaming JSONL analysis

6. **Practical Polars (2026)** — endjin.com/blog/2026/01/practical-polars-code-examples-everyday-data-tasks
   - Expression DSL: composable, functional transformations
   - "Come for the speed, stay for the API"
   - Streaming execution for larger-than-RAM workloads

---

*ARC-AGI Solver: Polars Integration & Improvement Research*
*Copyright 2026 Alexandros Karales. All Rights Reserved.*
