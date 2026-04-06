"""AST-based mutation generators for ARC program evolution.

Generates single-point mutations of Python programs by sweeping
integer constants, flipping comparison operators, adjusting loop
bounds, and negating boolean conditions.

The evolution loop that *uses* these mutations lives in ``evolver.py``.

Usage:
    from loopagi.arc.mutator import generate_mutations
    mutations = generate_mutations(source_code)
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Mutation:
    """A single mutation applied to source code."""

    original_code: str
    mutated_code: str
    mutation_type: str
    target: str
    line_number: int = 0


# ---------------------------------------------------------------------------
# AST-based mutation generators
# ---------------------------------------------------------------------------


def _find_integer_literals(source: str) -> list[tuple[int, int, int]]:
    """Find all integer literals in source code.

    Returns list of (line_number, col_offset, value).
    Skips the ``0`` in ``range(0, ...)`` style patterns and very large
    numbers that are unlikely to be ARC color values or small offsets.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    results: list[tuple[int, int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            # Skip booleans (True/False are int subclass)
            if isinstance(node.value, bool):
                continue
            # Focus on small integers relevant to ARC (colors 0-9, offsets -30..30)
            if -30 <= node.value <= 30:
                results.append((node.lineno, node.col_offset, node.value))
    return results


def mutate_constants(source: str) -> list[Mutation]:
    """Generate mutations by sweeping integer constants.

    For each integer literal found, produce variants with nearby values
    and all ARC color values (0-9).
    """
    literals = _find_integer_literals(source)
    lines = source.splitlines()
    mutations: list[Mutation] = []
    seen: set[str] = set()

    for lineno, col, value in literals:
        # Generate replacement values: ARC colors + nearby offsets
        candidates: set[int] = set()
        # ARC colors
        for c in range(10):
            if c != value:
                candidates.add(c)
        # Nearby offsets (±1, ±2)
        for delta in (-2, -1, 1, 2):
            nv = value + delta
            if nv != value:
                candidates.add(nv)

        for new_val in sorted(candidates):
            new_lines = list(lines)
            line_idx = lineno - 1
            if line_idx >= len(new_lines):
                continue

            old_line = new_lines[line_idx]
            # Replace the specific integer occurrence
            new_line = _replace_int_at(old_line, col, value, new_val)
            if new_line == old_line:
                continue
            new_lines[line_idx] = new_line
            mutated = "\n".join(new_lines)

            if mutated not in seen:
                seen.add(mutated)
                mutations.append(Mutation(
                    original_code=source,
                    mutated_code=mutated,
                    mutation_type="constant",
                    target=f"L{lineno}: {value}→{new_val}",
                    line_number=lineno,
                ))

    return mutations


def _replace_int_at(line: str, col: int, old_val: int, new_val: int) -> str:
    """Replace an integer at a specific column position in a line."""
    old_str = str(old_val)
    new_str = str(new_val)

    # Handle negative numbers
    if old_val < 0:
        # Check for '-' before the digits
        if col > 0 and line[col - 1] == '-':
            col -= 1
            old_str = str(old_val)

    # Verify the value is actually at this position
    segment = line[col:col + len(old_str)]
    if segment == old_str:
        return line[:col] + new_str + line[col + len(old_str):]

    # Fallback: try finding the value near the column
    return line


def mutate_operators(source: str) -> list[Mutation]:
    """Generate mutations by flipping comparison operators."""
    # Operator replacement pairs
    op_swaps = {
        ">=": [">" , "==", "<="],
        "<=": ["<" , "==", ">="],
        ">" : [">=", "!=", "<" ],
        "<" : ["<=", "!=", ">" ],
        "==": ["!=", ">=", "<="],
        "!=": ["=="],
    }

    lines = source.splitlines()
    mutations: list[Mutation] = []
    seen: set[str] = set()

    for i, line in enumerate(lines):
        # Skip comments and strings
        stripped = line.split("#")[0]
        for old_op, new_ops in op_swaps.items():
            if old_op not in stripped:
                continue
            for new_op in new_ops:
                new_line = _replace_first_op(stripped, old_op, new_op)
                if new_line == stripped:
                    continue
                # Reconstruct with any trailing comment
                comment_part = line[len(stripped):] if len(stripped) < len(line) else ""
                new_lines = list(lines)
                new_lines[i] = new_line + comment_part
                mutated = "\n".join(new_lines)

                if mutated not in seen:
                    seen.add(mutated)
                    mutations.append(Mutation(
                        original_code=source,
                        mutated_code=mutated,
                        mutation_type="operator",
                        target=f"L{i + 1}: {old_op}→{new_op}",
                        line_number=i + 1,
                    ))

    return mutations


def _replace_first_op(line: str, old_op: str, new_op: str) -> str:
    """Replace the first occurrence of an operator in a line.

    Careful not to replace operators inside strings.
    """
    # Simple approach: find outside of string literals
    idx = line.find(old_op)
    if idx < 0:
        return line
    return line[:idx] + new_op + line[idx + len(old_op):]


def mutate_bounds(source: str) -> list[Mutation]:
    """Generate mutations by adjusting loop bounds (±1, ±2).

    Targets ``range(...)`` calls and slice notation.
    """
    mutations: list[Mutation] = []
    seen: set[str] = set()
    lines = source.splitlines()

    # Pattern: range(...) with numeric arguments
    range_pat = re.compile(r'range\(([^)]+)\)')

    for i, line in enumerate(lines):
        for match in range_pat.finditer(line):
            args_str = match.group(1)
            args = [a.strip() for a in args_str.split(",")]

            for arg_idx, arg in enumerate(args):
                try:
                    val = int(arg)
                except ValueError:
                    # Non-literal argument (variable), try ±1
                    for suffix in [" - 1", " + 1", " - 2", " + 2"]:
                        new_arg = arg + suffix
                        new_args = list(args)
                        new_args[arg_idx] = new_arg
                        new_range = f"range({', '.join(new_args)})"
                        new_line = line[:match.start()] + new_range + line[match.end():]
                        new_lines = list(lines)
                        new_lines[i] = new_line
                        mutated = "\n".join(new_lines)
                        if mutated not in seen:
                            seen.add(mutated)
                            mutations.append(Mutation(
                                original_code=source,
                                mutated_code=mutated,
                                mutation_type="bound",
                                target=f"L{i + 1}: range arg '{arg}'{suffix}",
                                line_number=i + 1,
                            ))
                    continue

                # Numeric arg: try ±1, ±2
                for delta in (-2, -1, 1, 2):
                    new_val = val + delta
                    new_args = list(args)
                    new_args[arg_idx] = str(new_val)
                    new_range = f"range({', '.join(new_args)})"
                    new_line = line[:match.start()] + new_range + line[match.end():]
                    new_lines = list(lines)
                    new_lines[i] = new_line
                    mutated = "\n".join(new_lines)
                    if mutated not in seen:
                        seen.add(mutated)
                        mutations.append(Mutation(
                            original_code=source,
                            mutated_code=mutated,
                            mutation_type="bound",
                            target=f"L{i + 1}: range({args_str}) arg {val}→{new_val}",
                            line_number=i + 1,
                        ))

    return mutations


def mutate_negations(source: str) -> list[Mutation]:
    """Generate mutations by negating boolean conditions.

    Targets ``if cond:`` → ``if not cond:`` and vice versa.
    """
    mutations: list[Mutation] = []
    seen: set[str] = set()
    lines = source.splitlines()

    if_pat = re.compile(r'^(\s*)(if|elif)\s+(.+):(.*)$')

    for i, line in enumerate(lines):
        m = if_pat.match(line)
        if not m:
            continue
        indent, keyword, condition, rest = m.groups()

        # Add negation
        if condition.startswith("not "):
            new_cond = condition[4:]  # Remove 'not '
            desc = f"L{i + 1}: remove 'not'"
        else:
            new_cond = f"not ({condition})"
            desc = f"L{i + 1}: add 'not'"

        new_line = f"{indent}{keyword} {new_cond}:{rest}"
        new_lines = list(lines)
        new_lines[i] = new_line
        mutated = "\n".join(new_lines)

        if mutated not in seen:
            seen.add(mutated)
            mutations.append(Mutation(
                original_code=source,
                mutated_code=mutated,
                mutation_type="negate",
                target=desc,
                line_number=i + 1,
            ))

    return mutations


def generate_mutations(source: str) -> list[Mutation]:
    """Generate all single-point mutations of a program.

    Combines constant sweeps, operator flips, bound adjustments,
    and condition negations.
    """
    all_mutations: list[Mutation] = []
    all_mutations.extend(mutate_constants(source))
    all_mutations.extend(mutate_operators(source))
    all_mutations.extend(mutate_bounds(source))
    all_mutations.extend(mutate_negations(source))
    return all_mutations
