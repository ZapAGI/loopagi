"""ARC-AGI Model Benchmarking Script.

Runs each model on a fixed set of training tasks and records:
- Accuracy (avg similarity, solve rate)
- Speed (time per call, total time)
- VRAM usage
- Code validity
- Hypothesis quality (first hypothesis similarity)

Usage:
    uv run python chapter-22/benchmark_models.py
    uv run python chapter-22/benchmark_models.py --models qwen3:8b,qwen2.5-coder:7b
    uv run python chapter-22/benchmark_models.py --tasks 10 --output reports/
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loopagi.arc.arc_loader import load_default_datasets
from loopagi.arc.llm_bridge import ModelConfig, create_llm_bridge, solve_task_with_llm

logger = logging.getLogger(__name__)

# Fixed benchmark task IDs (diverse set from training)
# Selected for variety: color swap, shape scaling, object manipulation,
# pattern completion, symmetry, rotation, fill, etc.
DEFAULT_BENCHMARK_TASKS = [
    "00d62c1b", "007bbfb7", "00576224", "009d5c81", "0520fde7",
    "05269061", "05f2a901", "06df4c85", "08ed6ac7", "0962bcdd",
    "09629e4f", "0a938d79", "0b148d64", "0c786b71", "0ca9ddb6",
    "0d3d703e", "0dfd9992", "0e206a2e", "10fcaaa3", "11852cab",
]


@dataclass
class ModelBenchmarkResult:
    """Results from benchmarking a single model."""

    model: str
    num_tasks: int = 0
    num_solved: int = 0
    avg_similarity: float = 0.0
    best_similarity: float = 0.0
    best_task_id: str = ""
    avg_time_per_task: float = 0.0
    total_time: float = 0.0
    total_llm_calls: int = 0
    avg_time_per_call: float = 0.0
    vram_peak_mb: int = 0
    code_valid_pct: float = 0.0
    first_hyp_avg_sim: float = 0.0
    task_results: list[dict] = field(default_factory=list)

    @property
    def solve_rate(self) -> float:
        return self.num_solved / max(self.num_tasks, 1)

    def summary(self) -> str:
        lines = [
            f"=== Model: {self.model} ===",
            f"Tasks: {self.num_tasks}",
            f"Solve rate: {self.num_solved}/{self.num_tasks} ({self.solve_rate:.0%})",
            f"Avg similarity: {self.avg_similarity:.1%}",
            f"Best similarity: {self.best_similarity:.1%} ({self.best_task_id})",
            f"Avg time/task: {self.avg_time_per_task:.1f}s",
            f"Total time: {self.total_time:.0f}s",
            f"LLM calls: {self.total_llm_calls}",
            f"Avg time/call: {self.avg_time_per_call:.1f}s",
            f"VRAM peak: {self.vram_peak_mb}MB",
        ]
        return "\n".join(lines)


def get_vram_usage_mb() -> int:
    """Get current GPU VRAM usage in MB."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        return int(result.stdout.strip())
    except Exception:
        return 0


def benchmark_model(
    model: str,
    task_ids: list[str],
    max_hyp: int = 3,
    max_iter: int = 3,
    model_config: ModelConfig | None = None,
) -> ModelBenchmarkResult:
    """Run a benchmark on a single model across a set of tasks."""
    datasets = load_default_datasets(validate=False)
    if "training" not in datasets:
        print("ERROR: Training data not available")
        sys.exit(1)

    dataset = datasets["training"]
    available_ids = set(dataset.task_ids())

    bridge = create_llm_bridge(model=model, model_config=model_config)
    if bridge.is_mock:
        print(f"  WARNING: {model} not available, using mock mode")

    bench = ModelBenchmarkResult(model=model)
    similarities: list[float] = []
    times: list[float] = []
    first_hyp_sims: list[float] = []
    vram_peak = 0

    for i, task_id in enumerate(task_ids):
        if task_id not in available_ids:
            logger.warning("Task %s not in dataset, skipping", task_id)
            continue

        task = dataset.get_task(task_id)
        print(f"  [{i + 1}/{len(task_ids)}] {task_id}...", end=" ", flush=True)

        start = time.monotonic()
        output = solve_task_with_llm(
            task, bridge,
            max_hypotheses=max_hyp,
            max_iterations=max_iter,
            adaptive=False,
        )
        elapsed = time.monotonic() - start

        result = output["result"]
        sim = result.best_similarity
        similarities.append(sim)
        times.append(elapsed)

        # Track first hypothesis similarity
        if result.iterations:
            first_hyp_sims.append(result.iterations[0].verification.avg_similarity)

        # Track VRAM
        vram = get_vram_usage_mb()
        vram_peak = max(vram_peak, vram)

        status = "SOLVED" if result.solved else f"{sim:.0%}"
        print(f"{status} ({elapsed:.1f}s)")

        if result.solved:
            bench.num_solved += 1

        if sim > bench.best_similarity:
            bench.best_similarity = sim
            bench.best_task_id = task_id

        bench.task_results.append({
            "task_id": task_id,
            "solved": result.solved,
            "similarity": round(sim, 4),
            "time_seconds": round(elapsed, 1),
            "iterations": result.num_iterations,
            "hypothesis": result.best_program.hypothesis[:100] if result.best_program else "",
        })

    bench.num_tasks = len(similarities)
    bench.avg_similarity = sum(similarities) / max(len(similarities), 1)
    bench.avg_time_per_task = sum(times) / max(len(times), 1)
    bench.total_time = sum(times)
    bench.total_llm_calls = bridge.call_count
    bench.avg_time_per_call = bench.total_time / max(bridge.call_count, 1)
    bench.vram_peak_mb = vram_peak
    bench.first_hyp_avg_sim = sum(first_hyp_sims) / max(len(first_hyp_sims), 1)

    return bench


def save_report(bench: ModelBenchmarkResult, output_dir: str) -> str:
    """Save a benchmark report as JSON and markdown."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    safe_name = bench.model.replace(":", "_").replace("/", "_")

    # JSON report
    json_path = out / f"{safe_name}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(asdict(bench), f, indent=2)

    # Markdown report
    md_path = out / f"{safe_name}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Model Benchmark: {bench.model}\n\n")
        f.write(f"| Metric | Value |\n|--------|-------|\n")
        f.write(f"| Tasks | {bench.num_tasks} |\n")
        f.write(f"| Solve rate | {bench.num_solved}/{bench.num_tasks} ({bench.solve_rate:.0%}) |\n")
        f.write(f"| Avg similarity | {bench.avg_similarity:.1%} |\n")
        f.write(f"| Best similarity | {bench.best_similarity:.1%} ({bench.best_task_id}) |\n")
        f.write(f"| Avg time/task | {bench.avg_time_per_task:.1f}s |\n")
        f.write(f"| Total time | {bench.total_time:.0f}s |\n")
        f.write(f"| LLM calls | {bench.total_llm_calls} |\n")
        f.write(f"| Avg time/call | {bench.avg_time_per_call:.1f}s |\n")
        f.write(f"| VRAM peak | {bench.vram_peak_mb}MB |\n")
        f.write(f"| 1st hypothesis avg sim | {bench.first_hyp_avg_sim:.1%} |\n")
        f.write(f"\n## Per-Task Results\n\n")
        f.write(f"| Task | Solved | Similarity | Time | Iterations |\n")
        f.write(f"|------|--------|-----------|------|------------|\n")
        for tr in bench.task_results:
            status = "yes" if tr["solved"] else "no"
            f.write(
                f"| {tr['task_id']} | {status} | {tr['similarity']:.1%} "
                f"| {tr['time_seconds']:.1f}s | {tr['iterations']} |\n"
            )

    print(f"  Reports saved: {json_path}, {md_path}")
    return str(md_path)


def compile_comparison(results: list[ModelBenchmarkResult], output_dir: str) -> None:
    """Compile a comparison report across all models."""
    out = Path(output_dir)
    md_path = out / "MODEL_BENCHMARK_REPORT.md"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# ARC-AGI Model Benchmark Report\n\n")
        f.write(f"**Models tested:** {len(results)}\n")
        f.write(f"**Tasks per model:** {results[0].num_tasks if results else 0}\n\n")

        # Comparison table
        f.write("## Comparison\n\n")
        f.write("| Model | Solve Rate | Avg Similarity | Avg Time/Task | VRAM |\n")
        f.write("|-------|-----------|---------------|--------------|------|\n")
        for r in sorted(results, key=lambda x: x.avg_similarity, reverse=True):
            f.write(
                f"| {r.model} | {r.solve_rate:.0%} | {r.avg_similarity:.1%} "
                f"| {r.avg_time_per_task:.1f}s | {r.vram_peak_mb}MB |\n"
            )

        # Recommendations
        f.write("\n## Recommendations\n\n")
        best_sim = max(results, key=lambda r: r.avg_similarity)
        fastest = min(results, key=lambda r: r.avg_time_per_task)
        f.write(f"- **Best accuracy:** {best_sim.model} ({best_sim.avg_similarity:.1%})\n")
        f.write(f"- **Fastest:** {fastest.model} ({fastest.avg_time_per_task:.1f}s/task)\n")

        f.write("\n---\n\n*Generated by benchmark_models.py*\n")

    print(f"\nComparison report: {md_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ARC-AGI Model Benchmark")
    parser.add_argument(
        "--models", type=str, default=None,
        help="Comma-separated model names (default: all installed)",
    )
    parser.add_argument("--tasks", type=int, default=20, help="Number of tasks")
    parser.add_argument("--max-hyp", type=int, default=3, help="Max hypotheses")
    parser.add_argument("--max-iter", type=int, default=3, help="Max iterations")
    parser.add_argument(
        "--output", type=str, default="chapter-22/ARC_MODEL_REPORTS",
        help="Output directory for reports",
    )
    parser.add_argument(
        "--two-model", action="store_true",
        help="Use qwen3:8b for reasoning + qwen2.5-coder:7b for code gen",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(message)s",
    )

    # Handle two-model mode
    two_model_config: ModelConfig | None = None
    if args.two_model:
        two_model_config = ModelConfig(
            default="qwen3:8b",
            perceiver="qwen3:8b",
            hypothesizer="qwen3:8b",
            synthesizer="qwen2.5-coder:7b",
            refiner="qwen2.5-coder:7b",
        )
        models = ["qwen3:8b+qwen2.5-coder:7b"]
        print(f"Two-model mode: {two_model_config.summary()}")
    # Determine models to benchmark
    elif args.models:
        models = [m.strip() for m in args.models.split(",")]
    else:
        models = [
            "qwen3:8b",
            "qwen2.5-coder:7b",
            "phi4-mini",
            "nemotron-mini",
            "llama3.2:latest",
        ]

    # Select task IDs
    task_ids = DEFAULT_BENCHMARK_TASKS[:args.tasks]

    print(f"ARC-AGI Model Benchmark")
    print(f"Models: {', '.join(models)}")
    print(f"Tasks: {len(task_ids)}")
    print(f"Config: max_hyp={args.max_hyp}, max_iter={args.max_iter}")
    print(f"Output: {args.output}")
    print()

    all_results: list[ModelBenchmarkResult] = []

    for model in models:
        print(f"\n{'=' * 60}")
        print(f"Benchmarking: {model}")
        print(f"{'=' * 60}")

        actual_model = "qwen3:8b" if two_model_config else model
        bench = benchmark_model(
            actual_model, task_ids, args.max_hyp, args.max_iter,
            model_config=two_model_config,
        )
        bench.model = model  # Use the display name
        print(f"\n{bench.summary()}")

        save_report(bench, args.output)
        all_results.append(bench)

    if len(all_results) > 1:
        compile_comparison(all_results, args.output)

    print(f"\nDone. {len(all_results)} models benchmarked.")


if __name__ == "__main__":
    main()
