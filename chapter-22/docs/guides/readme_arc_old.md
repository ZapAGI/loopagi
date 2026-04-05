# Chapter ARC: The ARC-AGI Challenge

**A Multi-Agent Emergence Solver for the ARC Prize**

This chapter implements a multi-agent approach to the [ARC-AGI](https://arcprize.org) benchmark,
the hardest AI reasoning test in existence. It serves as the ultimate test of the book's thesis:
*"Intelligence emerges from orchestrated specialists."*

## Quick Start

```bash
# Visualize a task
uv run python chapter-22/demo_arc.py --task 0934a4d8

# Visualize with matplotlib
uv run python chapter-22/demo_arc.py --task 0934a4d8 --plot

# Run identity baseline on evaluation set
uv run python chapter-22/demo_arc.py --solver identity

# Run most-common-output baseline
uv run python chapter-22/demo_arc.py --solver most_common_output --limit 20

# Generate a submission.json
uv run python chapter-22/demo_arc.py --solver identity --submit submission.json

# Run tests
uv run pytest tests/test_arc_loader.py tests/test_arc_evaluator.py tests/test_arc_runner.py -v
```

## Data Setup

The ARC-AGI-2 dataset is cloned into `chapter-22/data/ARC-AGI-2/`:

```
chapter-22/data/
    ARC-AGI-2/                          # Cloned from github.com/arcprize/ARC-AGI-2
        data/training/                  # 1,000 training tasks (individual JSONs)
        data/evaluation/                # 120 eval tasks (individual JSONs)
    arc-agi_evaluation_challenges.json  # Combined eval JSON (Kaggle format)
```

To clone the dataset yourself:
```bash
git clone --depth 1 https://github.com/arcprize/ARC-AGI-2.git chapter-22/data/ARC-AGI-2
```

## Architecture

### Phase 1: Infrastructure (complete)

| Module | Location | Purpose |
|--------|----------|---------|
| `arc_loader` | `loopagi/arc/arc_loader.py` | Load/validate ARC tasks from JSON |
| `arc_visualizer` | `loopagi/arc/arc_visualizer.py` | Rich terminal + matplotlib grid display |
| `arc_evaluator` | `loopagi/arc/arc_evaluator.py` | Exact match scoring, pass@2, similarity |
| `arc_runner` | `loopagi/arc/arc_runner.py` | Solver orchestration, submission.json |

### Phase 2: Grid DSL (complete)

| Module | Location | Purpose |
|--------|----------|---------|
| `grid_ops` | `loopagi/arc/grid_ops.py` | 37 composable grid transforms (rotate, reflect, translate, scale, crop, pad, tile, recolor, flood_fill, overlay, mask, symmetry) |
| `grid_objects` | `loopagi/arc/grid_objects.py` | Object detection (4/8-connected), extraction, placement, relationships |

### Phase 3: Multi-Agent Solver (complete)

5 specialist agents with a refinement loop:

| Module | Location | Purpose |
|--------|----------|---------|
| `perceiver` | `loopagi/arc/perceiver.py` | Analyze training pairs, extract patterns |
| `hypothesizer` | `loopagi/arc/hypothesizer.py` | Generate ranked candidate rules |
| `synthesizer` | `loopagi/arc/synthesizer.py` | Convert hypothesis to executable Python |
| `verifier` | `loopagi/arc/verifier.py` | Run code against ALL training pairs |
| `refiner` | `loopagi/arc/refiner.py` | Analyze failures, improve hypothesis |
| `solver` | `loopagi/arc/solver.py` | Orchestrator with refinement loop |

### Phase 4: Task Similarity RAG (complete)

| Module | Location | Purpose |
|--------|----------|---------|
| `task_similarity` | `loopagi/arc/task_similarity.py` | Feature-based task similarity, index, k-NN search |

### Phase 5: Kaggle Submission + Paper (planned)

Package for Kaggle (L4x4 GPU, no internet, 12 hours).
Write paper for Paper Award ($75K).

## ARC-AGI Format

Each task has:
- **Training pairs**: 2-5 input/output grid pairs demonstrating a pattern
- **Test inputs**: 1-2 inputs where you produce the output
- **Grids**: Rectangular int matrices (0-9), max 30x30
- **Evaluation**: pass@2 (2 attempts per test output, exact match)

## Connection to the Book

| Book Chapter | ARC Relevance |
|-------------|---------------|
| Ch 1: Information Theory | Pattern recognition and compression |
| Ch 2: Emergence | Multi-agent reasoning > single-agent |
| Ch 5: Hierarchical Routing | Route sub-problems to specialists |
| Ch 7: Quality Pipeline | Generate-test-refine loop |
| Ch 9: RAG | Retrieve similar solved tasks |

## References

- [ARC-AGI-2 Dataset](https://github.com/arcprize/ARC-AGI-2)
- [ARC Prize](https://arcprize.org)
- [On the Measure of Intelligence](https://arxiv.org/abs/1911.01547) (Chollet, 2019)
- [ARC_AGI_CHALLENGE.md](../ARC_AGI_CHALLENGE.md) (full strategy document)
