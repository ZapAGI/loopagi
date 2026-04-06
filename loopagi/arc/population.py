"""Population-based program evolution for ARC tasks.

Maintains a diverse pool of candidate programs with fitness-weighted
selection, LLM-guided mutation, and crossover. Inspired by Imbue's
Darwinian Evolver approach.

Usage:
    from loopagi.arc.population import Population, Organism
    pop = Population(max_size=10)
    pop.add(Organism(code="def transform(g): return g", fitness=0.5))
    parent = pop.select_parent()
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Organism:
    """A single candidate program in the population."""

    code: str
    fitness: float  # correctness (90%) + simplicity bonus (10%)
    generation: int
    parent_id: int | None = None
    id: int = field(default=0)


# ---------------------------------------------------------------------------
# Population management
# ---------------------------------------------------------------------------


class Population:
    """Manages a diverse pool of candidate programs.

    Supports fitness-weighted selection, insertion with diversity
    maintenance, and best-organism tracking.
    """

    def __init__(self, max_size: int = 10) -> None:
        self.max_size = max_size
        self.organisms: list[Organism] = []
        self._next_id = 0

    def __len__(self) -> int:
        return len(self.organisms)

    def add(self, organism: Organism) -> None:
        """Add an organism to the population.

        If at capacity, replaces the weakest organism only if the new
        one has higher fitness. Assigns a unique ID.
        """
        organism.id = self._next_id
        self._next_id += 1

        if len(self.organisms) < self.max_size:
            self.organisms.append(organism)
        else:
            weakest_idx = min(
                range(len(self.organisms)),
                key=lambda i: self.organisms[i].fitness,
            )
            if organism.fitness > self.organisms[weakest_idx].fitness:
                self.organisms[weakest_idx] = organism

    def best(self) -> Organism | None:
        """Return the organism with the highest fitness."""
        if not self.organisms:
            return None
        return max(self.organisms, key=lambda o: o.fitness)

    def select_parent(self) -> Organism | None:
        """Select a parent using fitness-weighted probability.

        Higher-fitness organisms are more likely to be selected.
        Returns None if the population is empty.
        """
        if not self.organisms:
            return None

        fitnesses = [max(o.fitness, 0.01) for o in self.organisms]
        total = sum(fitnesses)
        weights = [f / total for f in fitnesses]

        return random.choices(self.organisms, weights=weights, k=1)[0]

    def select_parents(self, n: int) -> list[Organism]:
        """Select n parents using fitness-weighted probability.

        May return duplicates if population is small.
        Returns fewer than n if population is smaller.
        """
        if not self.organisms:
            return []

        n = min(n, max(len(self.organisms), 1))
        fitnesses = [max(o.fitness, 0.01) for o in self.organisms]
        total = sum(fitnesses)
        weights = [f / total for f in fitnesses]

        return random.choices(self.organisms, weights=weights, k=n)

    def diversity_score(self) -> float:
        """Compute a diversity score based on code uniqueness.

        Returns a value between 0.0 (all identical) and 1.0 (all unique).
        """
        if len(self.organisms) <= 1:
            return 1.0

        unique_codes = {o.code for o in self.organisms}
        return len(unique_codes) / len(self.organisms)

    def top_n(self, n: int) -> list[Organism]:
        """Return the top n organisms by fitness."""
        return sorted(self.organisms, key=lambda o: o.fitness, reverse=True)[:n]

    def summary(self) -> str:
        """Return a compact summary of the population."""
        if not self.organisms:
            return "Population: empty"
        best = self.best()
        return (
            f"Population: {len(self.organisms)}/{self.max_size}, "
            f"best={best.fitness:.1%}, "
            f"diversity={self.diversity_score():.1%}"
        )


# ---------------------------------------------------------------------------
# Crossover prompt
# ---------------------------------------------------------------------------

_CROSSOVER_PROMPT = """\
Three different approaches to solving this ARC puzzle:

Approach 1 ({sim1:.0%} accuracy):
```python
{code1}
```

Approach 2 ({sim2:.0%} accuracy):
```python
{code2}
```

Approach 3 ({sim3:.0%} accuracy):
```python
{code3}
```

Training examples:
{examples}

Combine the best ideas from all three approaches into a single
correct solution. Write a single transform() function.
Reply with ONLY the function in a ```python block."""


def format_crossover_prompt(
    parents: list[Organism],
    train_pairs_text: str,
) -> str:
    """Format a crossover prompt combining multiple parent approaches.

    Args:
        parents: List of 3 parent organisms to combine.
        train_pairs_text: Pre-formatted training pairs text.

    Returns:
        Formatted crossover prompt string.
    """
    if len(parents) < 3:
        parents = parents + [parents[-1]] * (3 - len(parents))

    return _CROSSOVER_PROMPT.format(
        sim1=parents[0].fitness,
        code1=parents[0].code,
        sim2=parents[1].fitness,
        code2=parents[1].code,
        sim3=parents[2].fitness,
        code3=parents[2].code,
        examples=train_pairs_text,
    )


def crossover(
    bridge: object,
    parents: list[Organism],
    train_pairs_text: str,
    generation: int,
) -> str | None:
    """Generate a crossover child from multiple parent organisms.

    Args:
        bridge: LLM bridge for inference (uses .call()).
        parents: Parent organisms to combine (ideally 3).
        train_pairs_text: Pre-formatted training pairs text.
        generation: Current generation number.

    Returns:
        Crossover code string, or None if LLM returns no valid code.
    """
    from loopagi.arc.synthesizer import extract_code_from_response

    prompt = format_crossover_prompt(parents, train_pairs_text)
    response = bridge.call(prompt)  # type: ignore[attr-defined]
    code = extract_code_from_response(response)

    if not code or "def transform" not in code:
        return None

    try:
        compile(code, "<crossover>", "exec")
    except SyntaxError:
        return None

    return code
