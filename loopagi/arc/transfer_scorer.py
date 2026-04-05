"""Transfer score for ARC program evolution (Phase Z).

Evaluates whether a candidate program will generalize from training
examples to unseen challenge inputs. Inspired by Imbue's Darwinian
Evolver transfer score (7% of total fitness).

The LLM inspects the code and challenge inputs to detect overfitting
signals: hard-coded colors, fixed dimensions, training-specific logic.

Usage:
    from loopagi.arc.transfer_scorer import compute_transfer_score
    score = compute_transfer_score(bridge, code, task)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import ArcTask
    from loopagi.arc.llm_bridge import LLMBridge

logger = logging.getLogger(__name__)

# Type aliases
Grid = list[list[int]]

_TRANSFER_PROMPT = """\
You are evaluating whether a Python function will generalize to new inputs.

The function solves an ARC-AGI puzzle. It was written based on these training examples:
{train_summary}

Here is the function:
```python
{code}
```

Here are the UNSEEN challenge inputs (outputs unknown):
{challenge_inputs}

Rate how likely the function is to work correctly on the challenge inputs.
Consider:
1. Does the code use hard-coded color values (0-9) that may not appear in challenges?
2. Does the code assume specific grid dimensions?
3. Does the code handle edge cases (empty regions, different sizes)?
4. Is the logic general enough to work on new inputs?

Reply with ONLY a single number from 0 to 10:
0 = definitely will fail (completely overfit to training)
5 = uncertain (some generalization issues)
10 = very likely to work (fully general logic)"""


def compute_transfer_score(
    bridge: LLMBridge,
    code: str,
    task: ArcTask,
) -> float:
    """Compute transfer score via LLM evaluation.

    Args:
        bridge: LLM bridge for inference.
        code: Python source code to evaluate.
        task: ARC task with training pairs and challenge inputs.

    Returns:
        Score from 0.0 (overfit) to 1.0 (generalizes well).
    """
    if bridge.is_mock or not code:
        return 0.5

    train_summary = _format_train_summary(task)
    challenge_text = _format_challenge_inputs(task)

    prompt = _TRANSFER_PROMPT.format(
        train_summary=train_summary,
        code=code,
        challenge_inputs=challenge_text,
    )

    try:
        response = bridge.call(prompt)
    except Exception:
        return 0.5

    return _parse_score(response)


def _format_train_summary(task: ArcTask) -> str:
    """Compact summary of training pairs."""
    lines: list[str] = []
    for i, pair in enumerate(task.train, 1):
        inp = pair.input
        out = pair.output
        lines.append(
            f"Pair {i}: {len(inp)}x{len(inp[0]) if inp else 0} -> "
            f"{len(out)}x{len(out[0]) if out else 0}"
        )
    return "\n".join(lines)


def _format_challenge_inputs(task: ArcTask) -> str:
    """Format challenge/test inputs compactly."""
    import json
    lines: list[str] = []
    for i, test in enumerate(task.test, 1):
        grid_str = json.dumps(test.input, separators=(",", ":"))
        lines.append(f"Challenge {i}: {grid_str}")
    return "\n".join(lines)


def _parse_score(response: str) -> float:
    """Parse a 0-10 score from LLM response, return 0.0-1.0."""
    import re
    # Find first number in response
    match = re.search(r"\b(\d+(?:\.\d+)?)\b", response.strip())
    if not match:
        return 0.5
    try:
        raw = float(match.group(1))
        return min(max(raw / 10.0, 0.0), 1.0)
    except ValueError:
        return 0.5
