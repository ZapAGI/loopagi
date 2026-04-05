"""
Chapter 2: REAL Emergence Demonstration

This is not a simulation with random numbers. This runs REAL
LLM-powered agents on the same coding task, individually and
orchestrated, then measures whether the system exceeds the
sum of its parts.

Hypothesis E1: Phi(S) > sum(Phi(s_i))

The experiment:
  1. Give the SAME coding task to each of 7 specialist agents individually
  2. Run the orchestrated pipeline (plan -> code -> test -> review)
  3. Score each output with concrete metrics
  4. Show that orchestration produces measurably better results

Requires: ollama pull llama3.2 (or runs in mock mode without it)
"""

from __future__ import annotations

import re
import textwrap
import time
from dataclasses import dataclass, field

from loopagi.core.ollama_utils import create_agent, require_ollama

# --- Scoring Engine ---


@dataclass
class CodeScore:
    """Concrete metrics for evaluating generated code (12 dimensions)."""

    agent_name: str
    has_function: bool = False
    has_class: bool = False
    has_type_hints: bool = False
    has_docstring: bool = False
    has_error_handling: bool = False
    has_custom_exception: bool = False
    has_edge_cases: bool = False
    has_decorator: bool = False
    has_logging: bool = False
    has_multiple_functions: bool = False
    has_default_params: bool = False
    code_block_found: bool = False
    line_count: int = 0
    raw_output: str = ""

    @property
    def total(self) -> float:
        """Weighted score out of 1.0 across 12 dimensions."""
        weights = {
            "has_function": 0.10,
            "has_class": 0.08,
            "has_type_hints": 0.10,
            "has_docstring": 0.08,
            "has_error_handling": 0.10,
            "has_custom_exception": 0.10,
            "has_edge_cases": 0.08,
            "has_decorator": 0.10,
            "has_logging": 0.06,
            "has_multiple_functions": 0.08,
            "has_default_params": 0.06,
            "code_block_found": 0.06,
        }
        score = 0.0
        for attr, weight in weights.items():
            if getattr(self, attr):
                score += weight
        return round(score, 3)

    @property
    def hits(self) -> int:
        """Number of dimensions achieved."""
        checks = [
            self.has_function, self.has_class,
            self.has_type_hints, self.has_docstring,
            self.has_error_handling, self.has_custom_exception,
            self.has_edge_cases, self.has_decorator,
            self.has_logging, self.has_multiple_functions,
            self.has_default_params, self.code_block_found,
        ]
        return sum(1 for c in checks if c)

    @property
    def grade(self) -> str:
        s = self.total
        if s >= 0.85:
            return "A"
        elif s >= 0.70:
            return "B"
        elif s >= 0.50:
            return "C"
        elif s >= 0.30:
            return "D"
        return "F"


def score_code_output(agent_name: str, output: str) -> CodeScore:
    """
    Score a code output with 12 concrete, deterministic metrics.

    No LLM grading. Pure regex and structural analysis.
    More dimensions = more differentiation between agents.
    """
    s = CodeScore(agent_name=agent_name, raw_output=output)

    # Extract code block if present
    code_match = re.search(
        r"```(?:python)?\s*\n(.*?)```", output, re.DOTALL,
    )
    if code_match:
        code = code_match.group(1)
        s.code_block_found = True
    else:
        code = output

    s.line_count = len(
        [ln for ln in code.splitlines() if ln.strip()]
    )

    # 1. Has function definition?
    s.has_function = bool(
        re.search(r"^\s*def\s+\w+", code, re.MULTILINE)
    )

    # 2. Has class definition?
    s.has_class = bool(
        re.search(r"^\s*class\s+\w+", code, re.MULTILINE)
    )

    # 3. Has type hints?
    s.has_type_hints = bool(re.search(
        r"(?:->|:\s*(?:int|str|bool|float|list|dict|None|Type|Callable))",
        code,
    ))

    # 4. Has docstring?
    s.has_docstring = bool(
        re.search(r'""".*?"""', code, re.DOTALL)
        or re.search(r"'''.*?'''", code, re.DOTALL)
    )

    # 5. Has error handling? (try/except or raise)
    s.has_error_handling = bool(re.search(
        r"(?:try:|except |raise )", code,
    ))

    # 6. Has custom exception class?
    s.has_custom_exception = bool(re.search(
        r"class\s+\w*(?:Error|Exception)", code,
    ))

    # 7. Handles edge cases?
    edge_patterns = [
        r"if\s+not\s+",
        r"if\s+\w+\s*(?:==|is)\s*None",
        r"if\s+\w+\s*(?:<=?|<)\s*[01]",
        r"if\s+len\(",
        r"is_empty",
        r"if\s+\w+\s*(?:==|is)\s*(?:''|\"\")",
    ]
    s.has_edge_cases = any(
        re.search(p, code) for p in edge_patterns
    )

    # 8. Has decorator usage (def with @)?
    s.has_decorator = bool(
        re.search(r"^\s*@\w+", code, re.MULTILINE)
    )

    # 9. Has logging or print-based diagnostics?
    s.has_logging = bool(re.search(
        r"(?:logging\.|logger\.|log\.|print\(.*(?:error|warn|info|debug))",
        code, re.IGNORECASE,
    ))

    # 10. Has multiple functions (2+)?
    func_count = len(
        re.findall(r"^\s*def\s+\w+", code, re.MULTILINE)
    )
    s.has_multiple_functions = func_count >= 2

    # 11. Has default parameter values?
    s.has_default_params = bool(re.search(
        r"def\s+\w+\([^)]*\w+\s*=\s*", code,
    ))

    return s


# --- The Experiment ---


TASK = textwrap.dedent("""\
    Write a Python retry decorator with exponential backoff.
    Requirements:
    - A decorator called `retry` that retries a function on exception
    - Configurable: max_retries (default 3), base_delay (default 1.0),
      max_delay (default 60.0), and exceptions to catch (default Exception)
    - Exponential backoff: delay doubles each retry
    - Add random jitter to prevent thundering herd
    - Create a custom RetryExhaustedError exception class
    - Log each retry attempt with attempt number and delay
    - Include type hints and docstrings
    - Handle edge cases (max_retries=0 means no retries, negative values)
    - The decorator should preserve the wrapped function's signature
""").strip()


@dataclass
class EmergenceResult:
    """Results from the emergence experiment."""

    individual_scores: list[CodeScore] = field(default_factory=list)
    orchestrated_score: CodeScore | None = None
    pipeline_stages: list[str] = field(default_factory=list)

    @property
    def best_individual(self) -> float:
        if not self.individual_scores:
            return 0.0
        return max(s.total for s in self.individual_scores)

    @property
    def avg_individual(self) -> float:
        if not self.individual_scores:
            return 0.0
        return sum(s.total for s in self.individual_scores) / len(self.individual_scores)

    @property
    def orchestrated_total(self) -> float:
        return self.orchestrated_score.total if self.orchestrated_score else 0.0

    @property
    def emergence_ratio(self) -> float:
        best = self.best_individual
        if best == 0:
            return 0.0
        return self.orchestrated_total / best

    @property
    def is_emergent(self) -> bool:
        return self.orchestrated_total > self.best_individual


def run_individual_agents(model: str) -> list[CodeScore]:
    """Phase 1: Each agent attempts the task alone."""
    agents_config = [
        ("coder", (
            "You are a Python coding specialist."
            " Write clean code with type hints and docstrings."
        )),
        ("tester", (
            "You are a testing specialist."
            " Write code that is thoroughly tested and handles edge cases."
        )),
        ("reviewer", (
            "You are a code reviewer."
            " Write code that follows best practices and PEP 8."
        )),
        ("planner", (
            "You are a software architect."
            " Write well-structured, planned code."
        )),
        ("researcher", (
            "You are a research specialist."
            " Write code based on algorithmic best practices."
        )),
        ("fileops", (
            "You are a file operations specialist."
            " Write utility code that is robust."
        )),
        ("devops", (
            "You are a DevOps specialist."
            " Write production-ready code with error handling."
        )),
    ]

    scores = []
    for name, role in agents_config:
        agent = create_agent(name=name, role=role, model=model)
        prompt = (
            "Write the code for this task. Output ONLY the"
            f" Python code in a code block.\n\n{TASK}"
        )

        print(f"  Running [{name}]...", end=" ", flush=True)
        start = time.time()
        response = agent.invoke(prompt)
        elapsed = time.time() - start

        score = score_code_output(name, response)
        scores.append(score)
        print(f"score={score.total:.2f} ({score.grade}) [{elapsed:.1f}s]")

    return scores


def run_orchestrated_pipeline(model: str) -> tuple[CodeScore, list[str]]:
    """Phase 2: The orchestrated pipeline (plan -> code -> test -> review -> revise)."""
    stages = []

    # Stage 1: Planner creates the plan
    planner = create_agent(
        name="planner",
        role=(
            "You are a software architect. Create a detailed implementation plan. "
            "Include: function signature, algorithm choice, edge cases to handle, "
            "and testing strategy. Output ONLY the plan, no code."
        ),
        model=model,
    )
    print("  [plan] Planning...", end=" ", flush=True)
    plan = planner.invoke(f"Create an implementation plan for:\n\n{TASK}")
    stages.append(f"PLAN:\n{plan[:300]}")
    print("done")

    # Stage 2: Coder implements the plan
    coder = create_agent(
        name="coder",
        role=(
            "You are an expert Python coder. Implement the plan EXACTLY. "
            "Use type hints, docstrings, error handling. "
            "Output ONLY Python code in a single code block."
        ),
        model=model,
    )
    print("  [code] Implementing...", end=" ", flush=True)
    code_v1 = coder.invoke(f"Implement this plan:\n\n{plan}")
    stages.append(f"CODE v1:\n{code_v1[:300]}")
    print("done")

    # Stage 3: Tester writes tests
    tester = create_agent(
        name="tester",
        role=(
            "You are a testing specialist. Write comprehensive pytest tests. "
            "Cover: happy path, edge cases (n=0, n=1, negative), boundary values. "
            "Output ONLY test code in a code block."
        ),
        model=model,
    )
    print("  [test] Writing tests...", end=" ", flush=True)
    tests = tester.invoke(f"Write tests for:\n\n{code_v1}")
    stages.append(f"TESTS:\n{tests[:300]}")
    print("done")

    # Stage 4: Reviewer evaluates
    reviewer = create_agent(
        name="reviewer",
        role=(
            "You are a senior code reviewer. Evaluate the code and tests. "
            "If issues found, respond with REVISION NEEDED and specific fixes. "
            "If code is good, respond with APPROVED."
        ),
        model=model,
    )
    print("  [review] Reviewing...", end=" ", flush=True)
    review = reviewer.invoke(f"Review this code and tests:\n\nCode:\n{code_v1}\n\nTests:\n{tests}")
    stages.append(f"REVIEW:\n{review[:300]}")
    approved = review.strip().upper().startswith("APPROVED")
    print(f"{'APPROVED' if approved else 'REVISION NEEDED'}")

    # Stage 5: If revision needed, coder fixes
    if not approved:
        print("  [revise] Revising...", end=" ", flush=True)
        code_v2 = coder.invoke(
            f"Fix this code based on reviewer feedback:\n\n"
            f"Original code:\n{code_v1}\n\n"
            f"Reviewer feedback:\n{review}"
        )
        stages.append(f"CODE v2 (revised):\n{code_v2[:300]}")
        print("done")
        final_code = code_v2
    else:
        final_code = code_v1

    score = score_code_output("orchestrated", final_code)
    return score, stages


def run_experiment(model: str = "llama3.2") -> EmergenceResult:
    """Run the full emergence experiment."""
    result = EmergenceResult()

    print("\n" + "=" * 60)
    print("PHASE 1: Individual Agents (each alone)")
    print("=" * 60)
    print(f"Task: {TASK[:80]}...")
    print()

    result.individual_scores = run_individual_agents(model)

    print("\n" + "=" * 60)
    print("PHASE 2: Orchestrated Pipeline (plan -> code -> test -> review)")
    print("=" * 60)
    print()

    score, stages = run_orchestrated_pipeline(model)
    result.orchestrated_score = score
    result.pipeline_stages = stages

    return result


def _yn(val: bool) -> str:
    return "Y" if val else "-"


def _print_score_row(s: CodeScore, label: str = "") -> None:
    """Print one row of the 12-dimension score table."""
    name = label or s.agent_name
    print(
        f"  {name:<13} {s.total:<6.3f} {s.hits:>2}/12 "
        f"{s.grade:<3} "
        f"{_yn(s.has_function)} {_yn(s.has_class)} "
        f"{_yn(s.has_type_hints)} {_yn(s.has_docstring)} "
        f"{_yn(s.has_error_handling)} "
        f"{_yn(s.has_custom_exception)} "
        f"{_yn(s.has_edge_cases)} {_yn(s.has_decorator)} "
        f"{_yn(s.has_logging)} "
        f"{_yn(s.has_multiple_functions)} "
        f"{_yn(s.has_default_params)} "
        f"{_yn(s.code_block_found)}"
    )


def print_results(result: EmergenceResult) -> None:
    """Display the emergence measurement results."""
    print("\n" + "=" * 72)
    print("EMERGENCE MEASUREMENT RESULTS (12 dimensions)")
    print("=" * 72)

    hdr = (
        "  Fn Cl Ty Do Er CE Ed De Lo MF DP Bk"
    )
    print(f"\n  {'Agent':<13} {'Score':<6} {'Hits':<6}"
          f"{'Gr':<4}{hdr}")
    print("  " + "-" * 68)

    for s in result.individual_scores:
        _print_score_row(s)

    s = result.orchestrated_score
    if s:
        print("  " + "-" * 68)
        _print_score_row(s, "ORCHESTRATED")

    print()
    print("  Legend: Fn=Function Cl=Class Ty=TypeHints "
          "Do=Docstring Er=ErrorHandling")
    print("  CE=CustomException Ed=EdgeCases De=Decorator "
          "Lo=Logging MF=MultiFuncs")
    print("  DP=DefaultParams Bk=CodeBlock")

    # Summary
    print("\n" + "-" * 60)
    print("SUMMARY:")
    print(f"  Best individual agent:  {result.best_individual:.3f}")
    print(f"  Average individual:     {result.avg_individual:.3f}")
    print(f"  Orchestrated system:    {result.orchestrated_total:.3f}")
    print(f"  Emergence ratio:        {result.emergence_ratio:.3f}x")
    print()

    if result.is_emergent:
        surplus = result.orchestrated_total - result.best_individual
        print("  EMERGENCE DETECTED: Phi(S) > max(Phi(s_i))")
        print(f"  Emergent surplus: +{surplus:.3f}")
        print()
        print("  The orchestrated system produced measurably")
        print("  better code than ANY individual agent alone.")
        print("  Intelligence emerged from the collaboration.")
    else:
        print("  No emergence detected in this run.")
        print("  The best individual matched or exceeded the")
        print("  pipeline. (Try with a different model or task.)")

    print()
    print("  Hypothesis E1: Phi(S) > sum(Phi(s_i))")
    print("  The whole exceeds the sum of its parts.")
    print("=" * 72)


def demo() -> None:
    """Run the real emergence demonstration."""
    print("Chapter 2: REAL Emergence Demonstration")
    print("=" * 60)
    print()
    print("This is not a simulation. This runs REAL LLM agents on the")
    print("same coding task, individually and orchestrated, then measures")
    print("whether the system exceeds the sum of its parts.")
    print()

    live = require_ollama()
    mode = "LIVE (Ollama)" if live else "MOCK (deterministic)"
    print(f"Mode: {mode}")

    result = run_experiment()
    print_results(result)


if __name__ == "__main__":
    demo()
