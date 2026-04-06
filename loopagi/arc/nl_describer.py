"""Natural language transformation describer for ARC tasks.

Imbue technique: before generating code, ask the LLM to describe the
transformation rule in plain English. This aligns the model's priors
with human visual reasoning and produces better synthesis code.

Usage:
    from loopagi.arc.nl_describer import describe_transformation
    description = describe_transformation(bridge, train_pairs)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.llm_bridge import LLMBridge

logger = logging.getLogger(__name__)

# Type alias
TrainPair = tuple[list[list[int]], list[list[int]]]


_DESCRIBE_PROMPT = """\
You are analyzing an ARC-AGI puzzle. Given input/output grid pairs, \
describe the transformation rule in plain English.

{examples}

Describe the EXACT rule that transforms each input into its output. \
Be specific about colors (integers 0-9), positions, shapes, and operations. \
Reply with ONE paragraph, no code."""


def _format_pairs(train_pairs: list[TrainPair], max_pairs: int = 3) -> str:
    """Format training pairs compactly for the describe prompt."""
    lines: list[str] = []
    for i, (inp, out) in enumerate(train_pairs[:max_pairs], 1):
        inp_str = "[" + ",".join(
            "[" + ",".join(str(v) for v in row) + "]" for row in inp
        ) + "]"
        out_str = "[" + ",".join(
            "[" + ",".join(str(v) for v in row) + "]" for row in out
        ) + "]"
        lines.append(f"Pair {i}:\n  Input:  {inp_str}\n  Output: {out_str}")
    return "\n".join(lines)


def describe_transformation(
    bridge: LLMBridge,
    train_pairs: list[TrainPair],
) -> str:
    """Ask the LLM to describe the transformation in natural language.

    Args:
        bridge: LLM bridge for inference.
        train_pairs: Training (input, output) pairs.

    Returns:
        Natural language description of the transformation rule.
        Returns empty string on error or if bridge is mock.
    """
    if bridge.is_mock or not train_pairs:
        return ""

    examples_text = _format_pairs(train_pairs)
    prompt = _DESCRIBE_PROMPT.format(examples=examples_text)

    try:
        description = bridge.call(prompt)
    except Exception:
        logger.warning("NL description failed, continuing without it")
        return ""

    # Truncate very long descriptions to avoid bloating synthesis prompts
    if len(description) > 500:
        description = description[:497] + "..."

    logger.info("NL description: %s", description[:120])
    return description.strip()


def format_nl_context(description: str) -> str:
    """Format a NL description for injection into a synthesis prompt.

    Args:
        description: The natural language transformation description.

    Returns:
        Formatted string to prepend to synthesis prompt, or empty string.
    """
    if not description:
        return ""
    return f"\nTransformation description: {description}\n"
