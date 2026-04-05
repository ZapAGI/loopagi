# ARC-AGI Solver: Implementation Plan

**Date:** March 19, 2026
**Author:** Alexandros Karales + Cascade AI
**Branch:** feature/audit-and-arc-agi
**Research Doc:** [ARC_POLARS_RESEARCH.md](ARC_POLARS_RESEARCH.md)
**Goal:** Get first actual solves on the 120-task training eval

---

## Phase Overview

| Phase | Name | New Files | Modified Files | Est. Time | Priority |
|---|---|---|---|---|---|
| **F** | Polars Foundation | `arc_analytics.py` | `pyproject.toml` | 1h | HIGH |
| **G** | Relaxed Stagnation | — | `llm_bridge.py` | 30m | HIGH |
| **H** | Best-of-N Sampling | `sampler.py` | `llm_bridge.py`, `synthesizer.py` | 2h | HIGH |
| **I** | Program Mutation | `mutator.py` | `solver.py`, `llm_bridge.py` | 3h | HIGH |
| **J** | Direct Transduction | `transducer.py` | `llm_bridge.py` | 2h | MEDIUM |
| **K** | Object Representation | `grid_describer.py` | `perceiver.py`, `llm_bridge.py` | 2h | MEDIUM |
| **L** | Model Upgrade | — | `llm_bridge.py`, config | 1h | MEDIUM |
| **M** | Full Eval Run | — | eval scripts | 4-6h (runtime) | HIGH |

**Total implementation:** ~12h coding + 4-6h eval runtime

---

## Phase F: Polars Foundation (1h)

**Goal:** Add Polars as a dependency and create the analytics module.

### F.1: Add Polars dependency

**File:** `pyproject.toml`

```toml
[project.optional-dependencies]
arc = [
    "polars",
    "httpx",
]
```

**Command:** `pnpm exec uv add polars` (or `uv add polars`)

### F.2: Create `loopagi/arc/arc_analytics.py`

New module providing Polars-powered analytics:

**Public API:**
```python
class ArcAnalytics:
    """Polars-powered analytics engine for ARC solver evaluation."""

    # --- Candidate tracking ---
    def add_candidate(self, task_id, hyp_id, sample_id, code, similarity, wrong_cells, exec_ms, error)
    def best_candidate(self, task_id) -> dict | None
    def top_candidates(self, task_id, n=5) -> pl.DataFrame

    # --- Iteration tracking ---
    def add_iteration(self, task_id, iteration, hyp_id, similarity, delta, stagnant)
    def improvement_curve(self, task_id) -> pl.DataFrame

    # --- Mutation tracking ---
    def add_mutation(self, task_id, parent_id, mutation_type, target, code, similarity, delta)
    def mutation_stats(self, task_id) -> pl.DataFrame

    # --- Grid analysis ---
    @staticmethod
    def grid_to_df(grid, label="") -> pl.DataFrame
    @staticmethod
    def grid_diff(expected, actual) -> pl.DataFrame
    @staticmethod
    def wrong_cell_summary(expected, actual) -> dict

    # --- Eval analytics ---
    @staticmethod
    def load_eval(jsonl_path) -> pl.LazyFrame
    @staticmethod
    def eval_summary(lf) -> pl.DataFrame
    @staticmethod
    def compare_evals(run_a, run_b) -> pl.DataFrame

    # --- Export ---
    def export_candidates(self, path: Path)
    def export_report(self, path: Path)
```

### F.3: Create `tests/test_arc_analytics.py`

**Test coverage targets:**
- `grid_to_df()` — correct shape, values
- `grid_diff()` — finds wrong cells, returns empty for identical grids
- `add_candidate()` / `best_candidate()` — ranking works
- `add_mutation()` / `mutation_stats()` — tracking works
- `load_eval()` / `eval_summary()` — JSONL loading, aggregation
- `compare_evals()` — join on task_id, compute deltas

**Estimated tests:** 15-20

### F.4: Verify

```bash
uv run pytest tests/test_arc_analytics.py -v
```

---

## Phase G: Relaxed Stagnation Detection (30m)

**Goal:** Stop abandoning near-miss hypotheses too early.

### G.1: Modify stagnation logic

**File:** `loopagi/arc/llm_bridge.py` (lines ~396-407)

**Current:**
```python
if iteration > 0 and improvement < 0.05:
    stagnant_count += 1
    if stagnant_count >= 2:
        break
```

**New:**
```python
# Adaptive stagnation: more patience for near-misses
if prev_iter_sim >= 0.90:
    stag_threshold, max_stag = 0.01, 4
elif prev_iter_sim >= 0.70:
    stag_threshold, max_stag = 0.03, 3
else:
    stag_threshold, max_stag = 0.05, 2

if iteration > 0 and improvement < stag_threshold:
    stagnant_count += 1
    if stagnant_count >= max_stag:
        logger.info("[%s] Stagnant (adaptive: thresh=%.2f, max=%d)", ...)
        break
else:
    stagnant_count = 0
```

### G.2: Update tests

**File:** `tests/test_llm_bridge.py` (or add new test)

Test that:
- At 95% similarity, 3% improvement does NOT trigger stagnation
- At 30% similarity, 3% improvement DOES trigger stagnation
- At 95%, stagnation takes 4 iterations to trigger (not 2)

### G.3: Verify

```bash
uv run pytest tests/ -k "stagnation or stagnant" -v
```

---

## Phase H: Best-of-N Sampling (2h)

**Goal:** Generate multiple candidate programs per synthesis step.

### H.1: Create `loopagi/arc/sampler.py`

**Public API:**
```python
@dataclass
class SampleConfig:
    n_samples: int = 5
    temperature_range: tuple[float, float] = (0.3, 0.9)
    timeout_per_sample: int = 10

@dataclass
class SampleResult:
    programs: list[SynthesizedProgram]
    best: SynthesizedProgram
    best_similarity: float
    analytics: pl.DataFrame  # All candidates with scores

def sample_n_programs(
    bridge: LLMBridge,
    hypothesis: Hypothesis,
    train_pairs: list[tuple[Grid, Grid]],
    config: SampleConfig = SampleConfig(),
    analytics: ArcAnalytics | None = None,
) -> SampleResult:
    """Generate N candidate programs and return the best."""
```

### H.2: Modify `llm_bridge.py` synthesis step

**Location:** `solve_task_with_llm()` around line 374-386

Replace single synthesis call:
```python
# OLD: Single sample
llm_code = bridge.call_as(ROLE_SYNTHESIZER, synth_prompt)
program = synthesize_from_llm(current_hyp, llm_code)
```

With Best-of-N:
```python
# NEW: Best-of-N sampling
from loopagi.arc.sampler import sample_n_programs, SampleConfig
sample_result = sample_n_programs(
    bridge, current_hyp, train_pairs,
    config=SampleConfig(n_samples=5),
    analytics=analytics,
)
program = sample_result.best
```

### H.3: Add temperature variation to LLMBridge

**File:** `loopagi/arc/llm_bridge.py`

Add `call_as_with_temp(role, prompt, temperature)` method that overrides
the default temperature for diversity in Best-of-N sampling.

### H.4: Create `tests/test_sampler.py`

**Test coverage:**
- Mock LLM returns N different programs
- Best program is selected by similarity
- Temperature varies across samples
- Analytics DataFrame is populated correctly
- Edge: all samples fail → returns identity

**Estimated tests:** 10-12

### H.5: Verify

```bash
uv run pytest tests/test_sampler.py tests/test_llm_bridge.py -v
```

---

## Phase I: Program Mutation / Evolution (3h)

**Goal:** Mutate near-miss programs to find exact solutions.

### I.1: Create `loopagi/arc/mutator.py`

**Public API:**
```python
@dataclass
class Mutation:
    original: str          # Original source code
    mutated: str           # Mutated source code
    mutation_type: str     # "constant", "offset", "bound", "operator", "negate"
    target: str            # Human-readable description of what changed
    line_number: int       # Which line was modified

@dataclass
class EvolutionConfig:
    min_similarity: float = 0.90         # Only evolve programs above this
    max_generations: int = 10            # Max mutation generations
    mutations_per_generation: int = 20   # Mutations to try per parent
    max_total_mutations: int = 200       # Budget cap

@dataclass
class EvolutionResult:
    best_program: SynthesizedProgram
    best_similarity: float
    generations: int
    total_mutations: int
    solved: bool
    analytics: pl.DataFrame  # All mutations with scores

def evolve_program(
    program: SynthesizedProgram,
    train_pairs: list[tuple[Grid, Grid]],
    config: EvolutionConfig = EvolutionConfig(),
    analytics: ArcAnalytics | None = None,
) -> EvolutionResult:
    """Evolve a program through mutations to improve similarity."""

def generate_mutations(source_code: str) -> list[Mutation]:
    """Generate all single-point mutations of a program."""

def mutate_constants(source_code: str) -> list[Mutation]:
    """Sweep integer constants (color values, offsets)."""

def mutate_operators(source_code: str) -> list[Mutation]:
    """Flip comparison operators (>, >=, <, <=, ==, !=)."""

def mutate_bounds(source_code: str) -> list[Mutation]:
    """Adjust loop bounds (±1, ±2)."""

def mutate_negations(source_code: str) -> list[Mutation]:
    """Negate boolean conditions."""
```

### I.2: Wire into solver loop

**File:** `loopagi/arc/llm_bridge.py`

After the main hypothesis loop, if `best_sim >= 0.90` and not solved:

```python
# Post-loop evolution for near-misses
if best_sim >= 0.90 and best_program and not result.solved:
    from loopagi.arc.mutator import evolve_program, EvolutionConfig
    logger.info("[%s] Evolving near-miss (sim=%.1f%%)...", task.task_id, best_sim * 100)
    evo_result = evolve_program(
        best_program, train_pairs,
        config=EvolutionConfig(min_similarity=0.90),
        analytics=analytics,
    )
    if evo_result.best_similarity > best_sim:
        best_sim = evo_result.best_similarity
        best_program = evo_result.best_program
    if evo_result.solved:
        result.solved = True
        result.best_similarity = 1.0
        result.best_program = best_program
        result.predictions = _apply_program_to_tests(best_program, task, max_attempts)
```

### I.3: Create `tests/test_mutator.py`

**Test coverage:**
- `mutate_constants()` — finds integer literals, generates variants
- `mutate_operators()` — finds comparisons, generates flips
- `mutate_bounds()` — adjusts range() arguments
- `mutate_negations()` — adds/removes `not`
- `evolve_program()` — mock verifier, tracks generations
- Edge: program with no mutatable elements
- Edge: evolution budget cap respected

**Estimated tests:** 18-22

### I.4: Verify

```bash
uv run pytest tests/test_mutator.py -v
```

---

## Phase J: Direct Transduction (2h)

**Goal:** Try predicting the output grid directly before code synthesis.

### J.1: Create `loopagi/arc/transducer.py`

**Public API:**
```python
@dataclass
class TransductionResult:
    predicted_grid: Grid | None
    confidence: float          # Based on training pair validation
    valid: bool                # Passes training verification
    similarity: float          # Against training outputs

def transduce(
    bridge: LLMBridge,
    task: ArcTask,
    train_pairs: list[tuple[Grid, Grid]],
) -> TransductionResult:
    """Ask the LLM to directly predict the test output grid."""

def format_transduction_prompt(task: ArcTask) -> str:
    """Format compact prompt showing all I/O pairs + test input."""

def parse_grid_from_response(response: str) -> Grid | None:
    """Extract a 2D grid from LLM response (JSON array of arrays)."""

def validate_transduction(
    transform_fn,
    train_pairs: list[tuple[Grid, Grid]],
) -> float:
    """Apply transduced logic to training inputs and measure accuracy."""
```

### J.2: Wire into solver as Phase 0

**File:** `loopagi/arc/llm_bridge.py`

Before the hypothesis loop:

```python
# Phase 0: Try direct transduction (fast, cheap)
if not bridge.is_mock:
    from loopagi.arc.transducer import transduce
    trans_result = transduce(bridge, task, train_pairs)
    if trans_result.valid and trans_result.similarity >= 0.95:
        logger.info("[%s] Transduction succeeded (sim=%.1f%%)!", task.task_id, trans_result.similarity * 100)
        # Use transduction as a candidate; still try synthesis for verification
        # ... (convert predicted grid to SynthesizedProgram wrapper)
```

### J.3: Create `tests/test_transducer.py`

**Test coverage:**
- `format_transduction_prompt()` — correct format, all pairs included
- `parse_grid_from_response()` — valid JSON, edge cases (markdown fences, whitespace)
- `transduce()` — mock LLM returns grid, validation passes/fails
- Edge: LLM returns invalid JSON
- Edge: LLM returns wrong shape

**Estimated tests:** 12-15

### J.4: Verify

```bash
uv run pytest tests/test_transducer.py -v
```

---

## Phase K: Object Representation (2h)

**Goal:** Enhance perceiver prompts with object-centric grid descriptions.

### K.1: Create `loopagi/arc/grid_describer.py`

**Public API:**
```python
@dataclass
class GridDescription:
    shape: tuple[int, int]
    background_color: int
    num_colors: int
    objects: list[ObjectInfo]
    spatial_relations: list[str]
    text: str                  # Formatted for LLM prompt

@dataclass
class ObjectInfo:
    object_id: int
    color: int
    cells: list[tuple[int, int]]
    bbox: tuple[int, int, int, int]  # r1, c1, r2, c2
    shape_name: str            # "rectangle", "L-shape", "line", "dot", "irregular"
    cell_count: int

def describe_grid(grid: Grid) -> GridDescription:
    """Parse a grid into an object-centric description."""

def describe_transform(
    input_desc: GridDescription,
    output_desc: GridDescription,
) -> str:
    """Describe how objects changed between input and output."""

def format_object_prompt(task: ArcTask) -> str:
    """Generate an object-aware perception prompt for a task."""
```

### K.2: Integrate with perceiver

**File:** `loopagi/arc/llm_bridge.py` — `format_perception_prompt()`

Add object description to the perception prompt:

```python
# Before: just compact grids
# After: compact grids + object-centric description
from loopagi.arc.grid_describer import describe_grid, describe_transform

for pair in task.train:
    input_desc = describe_grid(pair.input)
    output_desc = describe_grid(pair.output)
    transform_desc = describe_transform(input_desc, output_desc)
    # Append to perception prompt
```

### K.3: Use Polars for cross-pair object analysis

Create Polars DataFrames of objects across all training pairs to identify
consistent transform patterns (e.g., "color 2 always becomes color 5"):

```python
def object_pattern_analysis(task: ArcTask) -> pl.DataFrame:
    """Analyze object patterns across all training pairs."""
```

### K.4: Create `tests/test_grid_describer.py`

**Test coverage:**
- `describe_grid()` — detects objects, background, shapes
- `describe_transform()` — identifies moves, color changes, size changes
- `format_object_prompt()` — includes both grid and object info
- Object shape classification (rectangle, L-shape, line, dot)
- Edge: empty grid, single-color grid, 30x30 max-size grid

**Estimated tests:** 15-18

### K.5: Verify

```bash
uv run pytest tests/test_grid_describer.py -v
```

---

## Phase L: Model Upgrade (1h)

**Goal:** Use larger models for key roles.

### L.1: Download models

```bash
ollama pull qwen3:14b
ollama pull qwen2.5-coder:14b
```

### L.2: Update ModelConfig

**File:** `loopagi/arc/llm_bridge.py`

```python
DEFAULT_MODEL_CONFIG = {
    ROLE_PERCEIVER: ModelConfig("qwen3:14b", temperature=0.3),
    ROLE_HYPOTHESIZER: ModelConfig("qwen3:14b", temperature=0.5),
    ROLE_SYNTHESIZER: ModelConfig("qwen2.5-coder:14b", temperature=0.3),
    ROLE_REFINER: ModelConfig("qwen3:14b", temperature=0.3),
}
```

### L.3: Benchmark 14B vs 8B

Run a quick 10-task comparison:
```bash
uv run python chapter-22/benchmark_models.py --models qwen3:14b,qwen2.5-coder:14b --tasks 10
```

### L.4: Verify VRAM fits

```bash
nvidia-smi  # Check VRAM after loading both models
```

---

## Phase M: Full Evaluation Run (4-6h runtime)

**Goal:** Run the improved solver on all 120 training tasks.

### M.1: Run eval

```bash
uv run python chapter-22/eval_arc.py \
    --tasks 120 \
    --output chapter-22/ARC_MODEL_REPORTS/eval_improved.json \
    --resume \
    --best-of-n 5 \
    --evolve \
    --transduce \
    --adaptive-stagnation \
    --object-prompts
```

### M.2: Compare results

```python
import polars as pl

old = pl.scan_ndjson("chapter-22/ARC_MODEL_REPORTS/eval_no_fewshot.jsonl")
new = pl.scan_ndjson("chapter-22/ARC_MODEL_REPORTS/eval_improved.jsonl")

comparison = (
    old.select(["task_id", "similarity"]).rename({"similarity": "old_sim"})
    .join(
        new.select(["task_id", "similarity"]).rename({"similarity": "new_sim"}),
        on="task_id",
    )
    .with_columns((pl.col("new_sim") - pl.col("old_sim")).alias("delta"))
    .sort("delta", descending=True)
    .collect()
)
```

### M.3: Generate comparison report

**Output:** `chapter-22/ARC_MODEL_REPORTS/EVAL_IMPROVED_REPORT.md`

---

## Dependency Summary

### New Python Dependencies

| Package | Version | Purpose |
|---|---|---|
| **polars** | latest (1.39.2+) | DataFrame analytics, candidate ranking, eval analysis |

### New Files

| File | Module | Phase |
|---|---|---|
| `loopagi/arc/arc_analytics.py` | Polars analytics engine | F |
| `loopagi/arc/sampler.py` | Best-of-N candidate sampling | H |
| `loopagi/arc/mutator.py` | Program mutation / evolution | I |
| `loopagi/arc/transducer.py` | Direct grid prediction | J |
| `loopagi/arc/grid_describer.py` | Object-centric descriptions | K |
| `tests/test_arc_analytics.py` | Tests for analytics | F |
| `tests/test_sampler.py` | Tests for sampler | H |
| `tests/test_mutator.py` | Tests for mutator | I |
| `tests/test_transducer.py` | Tests for transducer | J |
| `tests/test_grid_describer.py` | Tests for describer | K |

### Modified Files

| File | Phase | Change |
|---|---|---|
| `pyproject.toml` | F | Add polars dependency |
| `loopagi/arc/llm_bridge.py` | G,H,I,J,K,L | Stagnation, sampling, evolution, transduction, objects, models |
| `loopagi/arc/synthesizer.py` | H | Temperature parameter for diversity |
| `loopagi/arc/solver.py` | I | Evolution post-loop |
| `loopagi/arc/perceiver.py` | K | Object-aware prompts |

---

## Expected Outcomes

### Conservative Estimate

| Metric | Current | After Improvements |
|---|---|---|
| Solve rate | 0.0% | **3-5%** (4-6 tasks) |
| Mean similarity | 66.98% | **72-75%** |
| Tasks ≥ 95% | 10 | **15-18** |
| Tasks ≥ 90% | 33 | **40-45** |
| Time/task | 110.9s | ~150s (more work per task) |

### Optimistic Estimate

| Metric | Current | After Improvements |
|---|---|---|
| Solve rate | 0.0% | **8-12%** (10-15 tasks) |
| Mean similarity | 66.98% | **75-80%** |
| Tasks ≥ 95% | 10 | **20-25** |
| Tasks ≥ 90% | 33 | **50-55** |

### Why These Estimates?

- **Program mutation alone** should convert 3-5 of the 10 tasks at 95%+
  (these are 1-5 cells wrong, often a single constant)
- **Best-of-N** smooths out variance, pushing more tasks into the 90%+ range
- **Transduction** should solve 2-3 simple tasks directly
- **Larger models** improve all tasks incrementally
- **Object representation** specifically helps medium/high complexity tasks

---

## Execution Order (Recommended)

```
Phase G (30m)  → trivial, immediate impact on near-misses
Phase F (1h)   → foundation for everything else
Phase I (3h)   → highest ROI: mutation converts near-misses to solves
Phase H (2h)   → second highest ROI: more candidates = more chances
Phase J (2h)   → cheap first-pass before expensive synthesis
Phase K (2h)   → improves perception quality for all tasks
Phase L (1h)   → model upgrade, incremental quality gain
Phase M (4-6h) → full eval run with all improvements
```

**Start with G → F → I → H for maximum impact in minimum time.**

---

## Success Criteria

- [ ] **At least 1 exact solve** on the 120-task training set
- [ ] **Mean similarity ≥ 72%** (up from 66.98%)
- [ ] **Tasks ≥ 90% ≥ 40** (up from 33)
- [ ] All new modules have ≥ 90% test coverage
- [ ] All existing 582 tests still pass
- [ ] Polars analytics module working and producing reports

---

*ARC-AGI Solver: Implementation Plan*
*Copyright 2026 Alexandros Karales. All Rights Reserved.*
