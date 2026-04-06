"""ARC-AGI Challenge: Multi-agent emergence solver for the ARC Prize.

This package provides:
- arc_loader: Load and validate ARC-AGI-2 tasks from JSON
- arc_visualizer: Render grids as colored terminal art or matplotlib plots
- arc_evaluator: Score predictions with exact match and pass@2
- arc_runner: Orchestrate solving, evaluation, and submission generation
- grid_ops: Core grid transformation primitives (DSL)
- grid_objects: Object detection and manipulation
- perceiver: Grid analysis agent
- hypothesizer: Hypothesis generation agent
- synthesizer: Python code generation agent
- verifier: Execute and verify against training pairs
- refiner: Error analysis and hypothesis refinement
- solver: Multi-agent orchestrator with refinement loop
- task_similarity: Feature-based task similarity for RAG
"""

from loopagi.arc.arc_loader import (
    ArcDataset,
    ArcTask,
    Grid,
    GridPair,
    TestInput,
    load_default_datasets,
)
from loopagi.arc.solver import MultiAgentArcSolver

__all__ = [
    "ArcDataset",
    "ArcTask",
    "Grid",
    "GridPair",
    "MultiAgentArcSolver",
    "TestInput",
    "load_default_datasets",
]
