"""Tests for loopagi.arc.population -- population-based program evolution."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from loopagi.arc.population import (
    Organism,
    Population,
    crossover,
    format_crossover_prompt,
)


# ---------------------------------------------------------------------------
# Organism
# ---------------------------------------------------------------------------


class TestOrganism:
    """Tests for the Organism dataclass."""

    def test_creation(self):
        org = Organism(code="def transform(g): return g", fitness=0.5, generation=0)
        assert org.code == "def transform(g): return g"
        assert org.fitness == 0.5
        assert org.generation == 0
        assert org.parent_id is None

    def test_with_parent(self):
        org = Organism(code="x", fitness=0.8, generation=2, parent_id=5)
        assert org.parent_id == 5


# ---------------------------------------------------------------------------
# Population
# ---------------------------------------------------------------------------


class TestPopulation:
    """Tests for the Population class."""

    def test_empty_population(self):
        pop = Population(max_size=5)
        assert len(pop) == 0
        assert pop.best() is None
        assert pop.select_parent() is None

    def test_add_organism(self):
        pop = Population(max_size=5)
        pop.add(Organism(code="a", fitness=0.5, generation=0))
        assert len(pop) == 1

    def test_add_assigns_id(self):
        pop = Population(max_size=5)
        o1 = Organism(code="a", fitness=0.5, generation=0)
        o2 = Organism(code="b", fitness=0.6, generation=0)
        pop.add(o1)
        pop.add(o2)
        assert o1.id == 0
        assert o2.id == 1

    def test_best(self):
        pop = Population(max_size=5)
        pop.add(Organism(code="a", fitness=0.3, generation=0))
        pop.add(Organism(code="b", fitness=0.9, generation=0))
        pop.add(Organism(code="c", fitness=0.5, generation=0))
        best = pop.best()
        assert best is not None
        assert best.fitness == 0.9

    def test_capacity_replaces_weakest(self):
        pop = Population(max_size=2)
        pop.add(Organism(code="a", fitness=0.3, generation=0))
        pop.add(Organism(code="b", fitness=0.5, generation=0))
        # At capacity, adding better organism replaces weakest
        pop.add(Organism(code="c", fitness=0.8, generation=0))
        assert len(pop) == 2
        fitnesses = {o.fitness for o in pop.organisms}
        assert 0.3 not in fitnesses  # weakest replaced
        assert 0.8 in fitnesses

    def test_capacity_rejects_weaker(self):
        pop = Population(max_size=2)
        pop.add(Organism(code="a", fitness=0.5, generation=0))
        pop.add(Organism(code="b", fitness=0.8, generation=0))
        # Adding weaker organism does nothing
        pop.add(Organism(code="c", fitness=0.3, generation=0))
        assert len(pop) == 2
        fitnesses = {o.fitness for o in pop.organisms}
        assert 0.3 not in fitnesses

    def test_select_parent(self):
        pop = Population(max_size=5)
        pop.add(Organism(code="a", fitness=0.9, generation=0))
        pop.add(Organism(code="b", fitness=0.1, generation=0))
        # Should return one of the organisms
        parent = pop.select_parent()
        assert parent is not None
        assert parent.code in ("a", "b")

    def test_select_parents(self):
        pop = Population(max_size=5)
        pop.add(Organism(code="a", fitness=0.5, generation=0))
        pop.add(Organism(code="b", fitness=0.6, generation=0))
        pop.add(Organism(code="c", fitness=0.7, generation=0))
        parents = pop.select_parents(3)
        assert len(parents) == 3

    def test_select_parents_empty(self):
        pop = Population(max_size=5)
        assert pop.select_parents(3) == []

    def test_diversity_score_all_unique(self):
        pop = Population(max_size=5)
        pop.add(Organism(code="a", fitness=0.5, generation=0))
        pop.add(Organism(code="b", fitness=0.5, generation=0))
        pop.add(Organism(code="c", fitness=0.5, generation=0))
        assert pop.diversity_score() == 1.0

    def test_diversity_score_all_same(self):
        pop = Population(max_size=5)
        pop.add(Organism(code="x", fitness=0.5, generation=0))
        pop.add(Organism(code="x", fitness=0.6, generation=0))
        # 1 unique / 2 total = 0.5
        assert pop.diversity_score() == 0.5

    def test_diversity_score_single(self):
        pop = Population(max_size=5)
        pop.add(Organism(code="a", fitness=0.5, generation=0))
        assert pop.diversity_score() == 1.0

    def test_top_n(self):
        pop = Population(max_size=5)
        pop.add(Organism(code="a", fitness=0.3, generation=0))
        pop.add(Organism(code="b", fitness=0.9, generation=0))
        pop.add(Organism(code="c", fitness=0.6, generation=0))
        top = pop.top_n(2)
        assert len(top) == 2
        assert top[0].fitness == 0.9
        assert top[1].fitness == 0.6

    def test_summary_empty(self):
        pop = Population(max_size=5)
        assert "empty" in pop.summary()

    def test_summary_with_organisms(self):
        pop = Population(max_size=5)
        pop.add(Organism(code="a", fitness=0.8, generation=0))
        s = pop.summary()
        assert "1/5" in s
        assert "80" in s  # best=80%


# ---------------------------------------------------------------------------
# format_crossover_prompt
# ---------------------------------------------------------------------------


class TestFormatCrossoverPrompt:
    """Tests for crossover prompt formatting."""

    def test_includes_all_three(self):
        parents = [
            Organism(code="def transform(g): return g", fitness=0.5, generation=0),
            Organism(code="def transform(g): return [[0]]", fitness=0.6, generation=0),
            Organism(code="def transform(g): return [[1]]", fitness=0.7, generation=0),
        ]
        prompt = format_crossover_prompt(parents, "Pair 1: [[1]] -> [[2]]")
        assert "Approach 1" in prompt
        assert "Approach 2" in prompt
        assert "Approach 3" in prompt
        assert "50%" in prompt  # 0.5 fitness
        assert "Pair 1" in prompt

    def test_pads_if_fewer_than_three(self):
        parents = [
            Organism(code="def transform(g): return g", fitness=0.5, generation=0),
        ]
        prompt = format_crossover_prompt(parents, "examples")
        # Should not crash, pads with last parent
        assert "Approach 1" in prompt
        assert "Approach 3" in prompt


# ---------------------------------------------------------------------------
# crossover
# ---------------------------------------------------------------------------


class TestCrossover:
    """Tests for the crossover function."""

    def _make_bridge(self, response: str):
        bridge = MagicMock()
        bridge.call = MagicMock(return_value=response)
        return bridge

    def test_valid_crossover(self):
        code = "```python\ndef transform(grid):\n    return grid\n```"
        bridge = self._make_bridge(code)
        parents = [
            Organism(code="a", fitness=0.5, generation=0),
            Organism(code="b", fitness=0.6, generation=0),
            Organism(code="c", fitness=0.7, generation=0),
        ]
        result = crossover(bridge, parents, "examples", generation=1)
        assert result is not None
        assert "def transform" in result

    def test_garbage_response(self):
        bridge = self._make_bridge("I cannot do this")
        parents = [Organism(code="a", fitness=0.5, generation=0)] * 3
        result = crossover(bridge, parents, "examples", generation=1)
        assert result is None

    def test_syntax_error_response(self):
        code = "```python\ndef transform(grid:\n    return grid\n```"
        bridge = self._make_bridge(code)
        parents = [Organism(code="a", fitness=0.5, generation=0)] * 3
        result = crossover(bridge, parents, "examples", generation=1)
        assert result is None
