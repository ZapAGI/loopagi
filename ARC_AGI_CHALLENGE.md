# ARC-AGI Challenge: A LoopAGI Approach

**Author:** Alexandros Karales
**Date:** March 18, 2026
**Status:** Research & Strategy Document
**Target:** ARC Prize 2026 (or late submission to ARC Prize 2025)

---

## What Is ARC-AGI?

The **Abstraction and Reasoning Corpus** (ARC-AGI) is the only AI benchmark designed to measure *fluid intelligence*: the ability to solve novel problems you have never seen before, using only a few examples.

Created by Francois Chollet (creator of Keras), ARC is not about knowledge or memorization. It is about **reasoning from first principles**.

### The Format

Each ARC task consists of:
- **Training pairs:** 2-5 input/output grid pairs that demonstrate a pattern
- **Test input(s):** 1-2 input grids where you must produce the output
- **Grids:** Rectangular matrices of integers 0-9 (visualized as colors), max 30x30
- **Evaluation:** pass@2 (you get 2 attempts per test output, exact match required)

Example task structure:
```json
{
  "train": [
    {"input": [[0,0,1],[0,1,0],[1,0,0]], "output": [[1,0,0],[0,1,0],[0,0,1]]},
    {"input": [[0,2,0],[2,0,2],[0,2,0]], "output": [[0,2,0],[2,0,2],[0,2,0]]}
  ],
  "test": [
    {"input": [[3,0,0],[0,3,0],[0,0,3]], "output": [[0,0,3],[0,3,0],[3,0,0]]}
  ]
}
```

### The Dataset (ARC-AGI-2)

| Set | Tasks | Purpose |
|-----|-------|---------|
| Training | 1,000 | Learn core knowledge priors |
| Public Eval | 120 | Test your system (don't overfit) |
| Semi-Private | 120 | Kaggle leaderboard scoring |
| Private | 120 | Final prize evaluation |

### Current State of the Art (2025 Results)

| System | ARC-AGI-2 Score | Cost/Task |
|--------|-----------------|-----------|
| Human panel | ~66% (avg), 100% (ceiling) | ~$17/task |
| 1st Place (ARChitects) | ~8% | Competition budget |
| o3-preview-high (est.) | ~15-20% | $1000s/task |
| Pure LLMs | 0% | N/A |
| Grand Prize threshold | 85% | Under $50 total |

**Key insight:** The Grand Prize ($700K) requires 85% accuracy within ~$50 of compute. This means brute force is impossible. You need efficient, general reasoning.

---

## Why ARC-AGI Matters for "God in the Loop"

The book's central thesis is:

> *"Intelligence is not a property of a single system but an emergent quality of orchestrated specialists."*

ARC-AGI is the perfect test of this thesis. If a multi-agent system (like LoopAGI) can solve ARC tasks that no single LLM can solve alone, it would be the strongest possible evidence for emergence-based intelligence.

### The Connection to the Book

| Book Chapter | ARC Relevance |
|-------------|---------------|
| Ch 1: Information Theory | ARC tasks test compression and pattern recognition |
| Ch 2: Emergence | Multi-agent approach to novel reasoning |
| Ch 5: Hierarchical Routing | Route sub-problems to specialist solvers |
| Ch 7: Quality Pipeline | Generate-test-refine loop (the 2025 winning approach) |
| Ch 9: RAG | Retrieve similar solved tasks as examples |
| Ch 10: Context Engine | Build task context from training pairs |
| Ch 12: Safety | Validate outputs before submission |

### Book Integration: Appendix F or Bonus Chapter

This could be added to the book as:

**Option A: Appendix F - "The ARC-AGI Challenge"**
- 15-20 pages
- Describes the benchmark, the multi-agent approach, and results
- Includes the evaluation harness code
- Perfect for the companion code repo

**Option B: Bonus Chapter 23 - "Testing the Thesis"**
- Full chapter treatment
- Runs the emergence experiment on ARC tasks
- Compares single-agent vs multi-agent performance
- Provides concrete Phi(S) measurements on a real AGI benchmark

**Recommendation:** Option B is stronger. It turns the book's philosophical thesis into a testable, measurable experiment. "We claimed intelligence emerges from orchestration. Here is the proof on the hardest AGI benchmark in the world."

---

## The Multi-Agent ARC Solver Strategy

### Architecture Overview

```
                    +-------------------+
                    |   ARC Task Loader |
                    |   (JSON parser)   |
                    +--------+----------+
                             |
                    +--------v----------+
                    |   Pattern Analyst  |
                    |   (perceive the    |
                    |    transformation) |
                    +--------+----------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v---+  +------v------+  +----v--------+
     | Grid DSL   |  | Program     |  | Neural      |
     | Solver     |  | Synthesizer |  | Pattern     |
     | (rule-     |  | (Python     |  | Matcher     |
     |  based)    |  |  code gen)  |  | (learned)   |
     +--------+---+  +------+------+  +----+--------+
              |              |              |
              +--------------+--------------+
                             |
                    +--------v----------+
                    |   Verifier        |
                    |   (execute on     |
                    |    training pairs) |
                    +--------+----------+
                             |
                    +--------v----------+
                    |   Refinement Loop |
                    |   (iterate until  |
                    |    all train pairs |
                    |    pass)          |
                    +-------------------+
```

### The 5 Specialist Agents

#### 1. Perceiver Agent
**Role:** Analyze the training input/output pairs and describe the transformation in natural language.

**What it does:**
- Identifies grid dimensions, colors used, shapes present
- Describes what changes between input and output
- Identifies symmetries, rotations, translations, color mappings
- Outputs a structured perception report

**Key prompt strategy:**
```
Given these input/output grid pairs, describe the transformation rule:
- What stays the same?
- What changes?
- Is there a spatial pattern (rotation, reflection, translation)?
- Is there a color mapping?
- Are there objects that interact?
```

#### 2. Hypothesizer Agent
**Role:** Generate multiple candidate transformation hypotheses from the perception.

**What it does:**
- Takes the Perceiver's report
- Generates 3-5 candidate hypotheses as natural language rules
- Ranks them by specificity and coverage
- Each hypothesis is a testable prediction

**Key insight from 2025 winners:** The "refinement loop" approach generates many candidates and iteratively filters them. This is exactly what a quality pipeline does.

#### 3. Program Synthesizer Agent
**Role:** Convert a natural language hypothesis into executable Python code.

**What it does:**
- Takes a hypothesis ("rotate the grid 90 degrees clockwise")
- Writes a Python function: `def transform(grid: list[list[int]]) -> list[list[int]]`
- The function must handle arbitrary grid sizes
- Uses numpy for grid operations

**This is where LoopAGI's coder agent shines.** The coder agent is already trained to write Python from specifications.

#### 4. Verifier Agent
**Role:** Execute the synthesized program against ALL training pairs.

**What it does:**
- Runs the transform function on each training input
- Compares output to expected output (exact match)
- Reports which pairs pass and which fail
- Provides diagnostic information on failures (wrong dimensions, wrong colors, partial match percentage)

**This is the critical feedback loop.** The 2025 winning approaches all used verification against training pairs as their fitness function.

#### 5. Refiner Agent
**Role:** When verification fails, analyze the error and refine the hypothesis.

**What it does:**
- Takes the failed verification report
- Compares expected vs actual output
- Identifies what the current hypothesis gets wrong
- Suggests a refined hypothesis or code fix
- Feeds back into the Program Synthesizer

**This creates the refinement loop that won ARC Prize 2025.**

### The Refinement Loop (Core Algorithm)

```python
def solve_arc_task(task, max_iterations=10):
    # Phase 1: Perceive
    perception = perceiver.analyze(task["train"])

    # Phase 2: Hypothesize
    hypotheses = hypothesizer.generate(perception, n=5)

    for hypothesis in hypotheses:
        for iteration in range(max_iterations):
            # Phase 3: Synthesize
            program = synthesizer.code(hypothesis)

            # Phase 4: Verify
            results = verifier.test(program, task["train"])

            if results.all_pass:
                # Apply to test inputs
                return [program(test["input"])
                        for test in task["test"]]

            # Phase 5: Refine
            hypothesis = refiner.improve(
                hypothesis, program, results
            )

    return None  # Failed to solve
```

### Why Multi-Agent Beats Single-Agent on ARC

| Challenge | Single LLM | Multi-Agent LoopAGI |
|-----------|-----------|-------------------|
| Pattern perception | One-shot, often misses subtle patterns | Perceiver agent specializes in visual analysis |
| Hypothesis generation | Generates one guess | Hypothesizer generates 5 ranked candidates |
| Code generation | May produce buggy code | Coder agent specialized in correct Python |
| Verification | Cannot execute its own code | Verifier runs real Python on training pairs |
| Refinement | No feedback loop | Refiner iterates based on concrete failures |
| Efficiency | One expensive inference per attempt | Many small, focused inferences |

---

## Technical Implementation Plan

### Phase 1: ARC Task Loader and Evaluator (Week 1)

Build the infrastructure to load, visualize, and evaluate ARC tasks.

```
chapter-22/
    arc_loader.py          # Load ARC-AGI-2 JSON tasks
    arc_visualizer.py      # ASCII + matplotlib grid visualization
    arc_evaluator.py       # Score predictions against ground truth
    arc_runner.py          # Run solver on eval set, produce submission.json
    README.md
```

**Data source:** `https://github.com/arcprize/ARC-AGI-2` (clone into `data/arc-agi-2/`)

### Phase 2: Grid DSL and Primitives (Week 1-2)

Build a domain-specific language for grid transformations.

```python
# Core Knowledge Priors (from Chollet's paper)
# These are operations humans find intuitive:

class GridOps:
    # Object recognition
    def find_objects(grid) -> list[Object]
    def find_background(grid) -> int

    # Geometric transforms
    def rotate(grid, degrees) -> Grid
    def reflect(grid, axis) -> Grid
    def translate(obj, dx, dy) -> Grid
    def scale(grid, factor) -> Grid

    # Color operations
    def recolor(grid, mapping) -> Grid
    def flood_fill(grid, x, y, color) -> Grid

    # Pattern operations
    def tile(pattern, rows, cols) -> Grid
    def overlay(grid_a, grid_b) -> Grid
    def crop(grid, bbox) -> Grid
    def pad(grid, color, size) -> Grid

    # Logical operations
    def mask(grid, condition) -> Grid
    def count_by_color(grid) -> dict
    def symmetry_check(grid) -> dict
```

### Phase 3: Multi-Agent Solver (Week 2-3)

Wire the 5 specialist agents with the refinement loop.

```
loopagi/arc/
    __init__.py
    perceiver.py        # Grid analysis agent
    hypothesizer.py     # Hypothesis generation
    synthesizer.py      # Python code generation
    verifier.py         # Execute and verify against training pairs
    refiner.py          # Error analysis and hypothesis refinement
    solver.py           # Orchestrator with refinement loop
    grid_ops.py         # Grid DSL primitives
    submission.py       # Generate submission.json
```

### Phase 4: Evaluation and Optimization (Week 3-4)

- Run on ARC-AGI-2 training set (1,000 tasks) to measure baseline
- Run on public eval set (120 tasks) to measure real performance
- Profile compute cost per task
- Optimize prompt engineering for each agent
- Add RAG: retrieve similar solved tasks as few-shot examples

### Phase 5: Kaggle Submission (Week 4+)

- Package as a Kaggle notebook (no internet, L4x4 GPU)
- Ensure all dependencies are bundled
- Generate `submission.json` in the required format
- Target: Beat the current SOTA (~8% on ARC-AGI-2)

---

## Compute Budget Analysis

The Kaggle competition allows:
- **GPU:** L4x4 (96GB VRAM)
- **Time:** 12 hours
- **Internet:** None
- **Budget equivalent:** ~$50

### What fits in 96GB VRAM?

| Model | Size | Fits? | Quality |
|-------|------|-------|---------|
| Qwen3-8B (Q4) | ~5GB | Yes (19x) | Good for code gen |
| Qwen2.5-Coder-14B (Q4) | ~9GB | Yes (10x) | Best for code |
| DeepSeek-R1-14B (Q4) | ~9GB | Yes (10x) | Best for reasoning |
| Qwen3-32B (Q4) | ~20GB | Yes (4x) | High quality |
| Llama-70B (Q4) | ~40GB | Yes (2x) | Highest quality |

**Strategy:** Use a small model (8B) for the Perceiver and Verifier (fast, many calls), and a larger model (14B-32B) for the Synthesizer and Refiner (quality matters more).

### Time Budget

- 120 eval tasks in 12 hours = 6 minutes per task
- At ~2 seconds per LLM call with 8B model
- Budget: ~180 LLM calls per task
- Refinement loop: 5 hypotheses x 10 iterations x 3 calls = 150 calls
- This fits within budget

---

## What Makes This Approach Novel

### 1. Multi-Agent Emergence on ARC

No ARC Prize submission has used a multi-agent architecture with specialist agents. All current approaches use either:
- Single LLM with prompting (0% on ARC-AGI-2)
- Evolutionary program synthesis (single-loop)
- Test-time training (fine-tuning on the task)

A multi-agent approach where **emergence** produces better solutions than any individual agent is genuinely novel.

### 2. The Quality Pipeline as a Refinement Loop

The book's quality pipeline (plan -> code -> test -> review) maps directly onto the ARC refinement loop (perceive -> hypothesize -> synthesize -> verify -> refine). This is not a coincidence. Both are instances of the same pattern: iterative improvement through specialist collaboration.

### 3. Grid DSL as a Shared Language

By giving all agents access to a Grid DSL with named operations (rotate, reflect, recolor, tile), we create a shared vocabulary that makes hypotheses more precise and programs more correct. This is the "tool use" that LoopAGI already supports.

### 4. RAG for Task Similarity

Use the 1,000 training tasks as a RAG corpus. When a new eval task arrives, retrieve the 3 most similar solved tasks as few-shot examples. This is exactly what LoopAGI's RAG engine already does.

---

## Connection to ARC Prize Paper Award

The Paper Award ($75K) is evaluated on 6 criteria. Here's how a "God in the Loop" approach scores:

| Criterion | Score Potential | Why |
|-----------|----------------|-----|
| **Accuracy** | Medium | Multi-agent adds overhead but catches errors single-agent misses |
| **Universality** | High | The approach generalizes to any reasoning task, not just ARC |
| **Progress** | High | Novel architecture direction, not incremental prompt engineering |
| **Theory** | Very High | Grounded in emergence theory (Ch 2), information theory (Ch 1), and the book's full philosophical framework |
| **Completeness** | High | Full book + companion code + measured emergence ratios |
| **Novelty** | Very High | No prior ARC submission uses multi-agent emergence |

**The paper award may be more achievable than the top score.** A well-written paper about multi-agent emergence on ARC, backed by the book's theoretical framework, could win the Paper Award even with a modest accuracy score.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM cannot perceive grid patterns | High | Critical | Add vision model or grid-to-text converter |
| Refinement loop does not converge | Medium | High | Limit iterations, fall back to best candidate |
| Compute budget exceeded | Medium | High | Profile early, use smaller models |
| Code synthesis produces invalid Python | Medium | Medium | Sandbox execution, syntax validation |
| Approach scores 0% | Low-Medium | High | Even 1% with a novel approach wins Paper Award |
| ARC-AGI-2 tasks resist multi-agent | Medium | Medium | Compare single vs multi to quantify delta |

---

## Recommended Timeline

### Month 1: Infrastructure (DONE - March 18, 2026)
- [x] Clone ARC-AGI-2 dataset (1000 training + 120 eval)
- [x] Build task loader and evaluator (arc_loader.py, arc_evaluator.py)
- [x] Build grid DSL with core primitives (grid_ops.py: 37 funcs, grid_objects.py: 18 funcs)
- [x] Build ASCII and matplotlib visualizer (arc_visualizer.py)
- [x] Build runner + submission.json generator (arc_runner.py)
- [x] Implement 5 specialist agents (perceiver, hypothesizer, synthesizer, verifier, refiner)
- [x] Build the refinement loop (solver.py)
- [x] Add RAG for task similarity (task_similarity.py: feature vectors + k-NN)
- [x] 541 tests passing (236 new ARC tests)
- [ ] Run on full training set (1,000 tasks) with LLM
- [ ] Measure single-agent vs multi-agent accuracy

### Month 2: Optimization
- [ ] Profile compute cost per task
- [ ] Optimize prompts for each agent
- [ ] Add Grid DSL to agent toolbox
- [ ] Run on public eval set (120 tasks)
- [ ] Package for Kaggle submission

### Month 4: Paper and Submission
- [ ] Write paper connecting emergence theory to ARC results
- [ ] Submit to Kaggle
- [ ] Submit paper for Paper Award
- [ ] Add results as Appendix F or Bonus Chapter to the book

---

## Quick Start: Try It Today

Even before building the full solver, you can test the approach manually:

1. Go to [arcprize.org/play](https://arcprize.org/play) and pick a task
2. Open LoopAGI: `uv run loopagi --model qwen3:8b`
3. Describe the task to the planner agent
4. Ask the coder to write a transform function
5. Use `/python` to test it against the training pairs
6. Use the reviewer to check for edge cases
7. Iterate until all training pairs pass

This manual process IS the multi-agent ARC solver. The automation just makes it faster.

---

## References

- Chollet, F. (2019). "On the Measure of Intelligence." arXiv:1911.01547
- ARC-AGI-2 Dataset: https://github.com/arcprize/ARC-AGI-2
- ARC Prize 2025 Results: https://arcprize.org/blog/arc-prize-2025-results-analysis
- ARC Prize 2026 (upcoming): https://arcprize.org
- Kaggle Competition: https://kaggle.com/competitions/arc-prize-2025
- Berman, J. (2025). "Evolutionary Test-Time Compute" (1st place approach)
- Pang, E. (2025). "Evolutionary Program Synthesis" (paper award)

---

*God in the Loop - ARC-AGI Challenge Strategy*
*Copyright 2026 Alexandros Karales. All Rights Reserved.*
