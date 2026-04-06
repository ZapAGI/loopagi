"""ARC-AGI Program Synthesizer Agent.

Converts a natural language hypothesis into executable Python code
that transforms an input grid to an output grid.

The Synthesizer is the third step in the refinement loop:
Perceive -> Hypothesize -> Synthesize -> Verify -> Refine
"""

from __future__ import annotations

import logging
import re
import signal
from dataclasses import dataclass

from loopagi.arc.hypothesizer import Hypothesis

logger = logging.getLogger(__name__)

# Template for generated transform functions
TRANSFORM_TEMPLATE = '''def transform(grid: list[list[int]]) -> list[list[int]]:
    """Transform an ARC grid according to the hypothesis.

    Hypothesis: {hypothesis}
    """
{body}
'''


@dataclass
class SynthesizedProgram:
    """A synthesized Python program for an ARC transformation."""

    hypothesis: str
    source_code: str
    is_valid: bool = True
    syntax_error: str = ""

    @property
    def code(self) -> str:
        """Alias for source_code (backwards compatibility)."""
        return self.source_code

    def summary(self) -> str:
        status = "valid" if self.is_valid else f"INVALID: {self.syntax_error}"
        return f"Program ({status}): {self.hypothesis[:80]}"


def validate_syntax(source_code: str) -> tuple[bool, str]:
    """Check if the generated Python code has valid syntax.

    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        compile(source_code, "<synthesized>", "exec")
        return True, ""
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"


def _try_fix_syntax(code: str) -> str:
    """Attempt basic syntax repairs on LLM-generated code.

    Fixes common issues: unclosed brackets, trailing junk,
    missing return statements.
    """
    lines = code.split("\n")

    # Remove trailing non-code lines (explanations after the function)
    cleaned: list[str] = []
    func_started = False
    func_ended = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("def "):
            func_started = True
        if func_started and not func_ended:
            cleaned.append(line)
            # Detect end of function: non-indented non-blank line after body
            if func_started and len(cleaned) > 1 and stripped and not line[0].isspace():
                if not stripped.startswith("def "):
                    cleaned.pop()
                    func_ended = True
        elif not func_started:
            cleaned.append(line)

    code = "\n".join(cleaned)

    # Balance brackets: close any unclosed (, [, {
    open_parens = code.count("(") - code.count(")")
    open_brackets = code.count("[") - code.count("]")
    open_braces = code.count("{") - code.count("}")
    suffix = ")" * max(0, open_parens)
    suffix += "]" * max(0, open_brackets)
    suffix += "}" * max(0, open_braces)
    if suffix:
        code = code.rstrip() + suffix + "\n"

    # Ensure return statement exists
    if "def transform" in code and "return" not in code:
        code = code.rstrip() + "\n    return grid\n"

    return code


def extract_code_from_response(llm_response: str) -> str:
    """Extract Python code from an LLM response.

    Handles fenced code blocks, bare function defs, and inline code.
    If no transform() function is found, wraps extracted code in one.
    Returns empty string if no usable code is found.
    """
    code = ""

    # Try to extract from fenced code block
    pattern = r"```(?:python)?\s*\n(.*?)```"
    matches = re.findall(pattern, llm_response, re.DOTALL)
    if matches:
        code = matches[0].strip()
    else:
        # Try to find any function definition
        lines = llm_response.split("\n")
        code_lines: list[str] = []
        in_code = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("def "):
                in_code = True
            if in_code:
                code_lines.append(line)
        if code_lines:
            code = "\n".join(code_lines)

    # Do NOT use raw LLM response as code (it's usually explanatory text)
    if not code:
        return ""

    # If code has a function but not named 'transform', rename it
    if "def " in code and "def transform" not in code:
        code = re.sub(r"def \w+\(", "def transform(", code, count=1)

    # If no function def at all, wrap the code body in transform()
    if "def transform" not in code and "def " not in code:
        # Only wrap if lines look like actual Python (contain =, return, for, if)
        code_indicators = ("=", "return", "for ", "if ", "while ", "import")
        if any(kw in code for kw in code_indicators):
            indented = "\n".join(
                "    " + line for line in code.split("\n") if line.strip()
            )
            if indented.strip():
                code = (
                    "def transform(grid: list[list[int]]) -> list[list[int]]:\n"
                    f"{indented}\n"
                )
                if "return" not in code:
                    code += "    return grid\n"
        else:
            return ""  # Not code, just text

    return code


def format_synthesis_prompt(
    hypothesis: Hypothesis,
    train_pairs: list[tuple[list[list[int]], list[list[int]]]] | None = None,
    grid_info: str = "",
    similar_context: str = "",
    max_examples: int = 2,
) -> str:
    """Format a concise prompt with training examples for the LLM.

    Including actual input/output examples dramatically improves code gen
    accuracy because the LLM can see the concrete transformation.

    Args:
        hypothesis: The hypothesis to synthesize code for.
        train_pairs: Optional training input/output pairs.
        grid_info: Optional extra grid info string.
        similar_context: Optional formatted context from similar tasks.
        max_examples: Maximum training examples to include.
    """
    from loopagi.arc.perceiver import grid_to_compact

    lines: list[str] = [
        f"Write a Python function. Rule: {hypothesis.rule}",
        "def transform(grid: list[list[int]]) -> list[list[int]]",
        "Input/output: 2D list of ints 0-9. Do not modify input.",
    ]

    if train_pairs:
        lines.append("")
        for i, (inp, out) in enumerate(train_pairs[:max_examples]):
            lines.append(f"Example {i + 1}:")
            lines.append(f"  In:  {inp}")
            lines.append(f"  Out: {out}")

    if similar_context:
        lines.append(similar_context)

    if grid_info:
        lines.append(f"Info: {grid_info}")

    # DSL reference: available grid primitives the LLM can use
    from loopagi.arc.grid_ops import get_dsl_reference
    lines.append("")
    lines.append(get_dsl_reference())

    lines.append("")
    lines.append("Reply with ONLY the function in a ```python block.")
    return "\n".join(lines)


def synthesize_from_code(hypothesis: str, code: str) -> SynthesizedProgram:
    """Create a SynthesizedProgram from raw code.

    Validates syntax and wraps in a SynthesizedProgram.
    """
    is_valid, error = validate_syntax(code)
    return SynthesizedProgram(
        hypothesis=hypothesis,
        source_code=code,
        is_valid=is_valid,
        syntax_error=error,
    )


def _has_transform_function(code: str, timeout: int = 10) -> bool:
    """Check if code defines a callable transform() function.

    Uses SIGALRM to prevent infinite loops during exec().
    """
    def _alarm_handler(signum: int, frame: object) -> None:
        raise TimeoutError("exec() timed out")

    old_handler = signal.getsignal(signal.SIGALRM)
    try:
        signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(timeout)
        ns: dict = {}
        exec(code, ns)
        return callable(ns.get("transform"))
    except Exception:
        return False
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def synthesize_from_llm(hypothesis: Hypothesis, llm_response: str) -> SynthesizedProgram:
    """Create a SynthesizedProgram from an LLM response.

    Extracts code, validates syntax, verifies transform() exists,
    attempts repair on failure, and falls back to identity if unusable.
    """
    code = extract_code_from_response(llm_response)

    if not code:
        logger.debug("No code extracted from LLM response, falling back to identity")
        return synthesize_identity()

    # Try original code
    is_valid, error = validate_syntax(code)
    if is_valid and _has_transform_function(code):
        return synthesize_from_code(hypothesis.rule, code)

    # Try syntax repair
    fixed = _try_fix_syntax(code)
    is_valid, error = validate_syntax(fixed)
    if is_valid and _has_transform_function(fixed):
        logger.debug("Syntax repair succeeded for: %s", hypothesis.rule[:60])
        return synthesize_from_code(hypothesis.rule, fixed)

    # Valid syntax but no transform() - fall back to identity
    if is_valid and not _has_transform_function(fixed):
        logger.debug("Code has no transform(), falling back to identity")
        return synthesize_identity()

    # Still broken syntax: fall back to identity (don't waste iterations on bad code)
    logger.debug("Syntax repair failed, falling back to identity")
    return synthesize_identity()


def synthesize_identity() -> SynthesizedProgram:
    """Synthesize the identity transform (baseline)."""
    code = (
        "def transform(grid: list[list[int]]) -> list[list[int]]:\n"
        "    return [row[:] for row in grid]\n"
    )
    return SynthesizedProgram(
        hypothesis="identity (return input unchanged)",
        source_code=code,
        is_valid=True,
    )


def synthesize_from_hypothesis(hypothesis: Hypothesis) -> SynthesizedProgram:
    """Attempt to synthesize a program from a hypothesis using pattern matching.

    This provides deterministic code generation for common transformations
    without requiring an LLM. Falls back to identity if no pattern matches.
    """
    rule_lower = hypothesis.rule.lower()
    code = _match_rule_to_code(rule_lower)

    if code:
        return synthesize_from_code(hypothesis.rule, code)

    logger.debug("No pattern match for hypothesis: %s", hypothesis.rule[:80])
    return synthesize_identity()


def _match_rule_to_code(rule: str) -> str | None:
    """Match a rule string to a known code template."""
    if "rotate" in rule and "90" in rule and "clockwise" in rule:
        return (
            "def transform(grid: list[list[int]]) -> list[list[int]]:\n"
            "    from loopagi.arc.grid_ops import rotate_cw\n"
            "    return rotate_cw(grid)\n"
        )

    if "rotate" in rule and "180" in rule:
        return (
            "def transform(grid: list[list[int]]) -> list[list[int]]:\n"
            "    from loopagi.arc.grid_ops import rotate_180\n"
            "    return rotate_180(grid)\n"
        )

    if "reflect" in rule and ("horizontal" in rule or "flip" in rule and "top" in rule):
        return (
            "def transform(grid: list[list[int]]) -> list[list[int]]:\n"
            "    from loopagi.arc.grid_ops import reflect_horizontal\n"
            "    return reflect_horizontal(grid)\n"
        )

    if "reflect" in rule and ("vertical" in rule or "mirror" in rule or "left" in rule):
        return (
            "def transform(grid: list[list[int]]) -> list[list[int]]:\n"
            "    from loopagi.arc.grid_ops import reflect_vertical\n"
            "    return reflect_vertical(grid)\n"
        )

    if "transpose" in rule or ("reflect" in rule and "diagonal" in rule):
        return (
            "def transform(grid: list[list[int]]) -> list[list[int]]:\n"
            "    from loopagi.arc.grid_ops import reflect_diagonal\n"
            "    return reflect_diagonal(grid)\n"
        )

    if "same dimensions" in rule or "modifies cell values in place" in rule:
        return None  # Too vague, need LLM

    if "preserves all colors" in rule:
        return None  # Constraint, not a transform

    return None
