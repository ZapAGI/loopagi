"""Tests for loopagi.router module."""

from __future__ import annotations

from unittest.mock import MagicMock

from loopagi.core.agent import Agent
from loopagi.core.router import ROUTING_PATTERNS, RouteDecision, Router


class TestRoutingPatterns:
    """Tests for keyword routing patterns."""

    def test_all_agent_types_have_patterns(self) -> None:
        expected = {"coder", "tester", "reviewer", "researcher", "planner", "fileops", "devops"}
        assert expected == set(ROUTING_PATTERNS.keys())

    def test_each_pattern_has_keywords(self) -> None:
        for agent, keywords in ROUTING_PATTERNS.items():
            assert len(keywords) > 0, f"{agent} has no keywords"

    def test_no_duplicate_keywords_within_agent(self) -> None:
        for agent, keywords in ROUTING_PATTERNS.items():
            assert len(keywords) == len(set(keywords)), f"{agent} has duplicate keywords"


class TestRouteDecision:
    """Tests for RouteDecision dataclass."""

    def test_creation(self) -> None:
        d = RouteDecision(agent_name="coder", confidence=0.8, method="keyword", reasoning="matched")
        assert d.agent_name == "coder"
        assert d.confidence == 0.8
        assert d.method == "keyword"

    def test_fields(self) -> None:
        d = RouteDecision(agent_name="x", confidence=0.5, method="llm", reasoning="r")
        assert hasattr(d, "agent_name")
        assert hasattr(d, "confidence")
        assert hasattr(d, "method")
        assert hasattr(d, "reasoning")


class TestRouter:
    """Tests for the Router class."""

    def _make_agents(self) -> list[Agent]:
        """Create mock-friendly agents (no Ollama needed)."""
        agents = []
        for name in ["coder", "researcher", "planner", "tester", "reviewer", "fileops", "devops"]:
            a = Agent.__new__(Agent)
            a.config = MagicMock()
            a.config.name = name
            a.config.role = f"You are a {name}."
            a.config.model = "test"
            a.config.temperature = 0.7
            a.config.max_history = 20
            a.history = []
            a.llm = MagicMock()
            agents.append(a)
        return agents

    def test_router_creation(self) -> None:
        agents = self._make_agents()
        router = Router(agents=agents)
        assert len(router.agents) == 7

    def test_keyword_route_coder(self) -> None:
        agents = self._make_agents()
        router = Router(agents=agents)
        decision = router._keyword_route("write a function to sort a list")
        assert decision is not None
        assert decision.agent_name == "coder"
        assert decision.method == "keyword"

    def test_keyword_route_researcher(self) -> None:
        agents = self._make_agents()
        router = Router(agents=agents)
        decision = router._keyword_route("explain how neural networks work")
        assert decision is not None
        assert decision.agent_name == "researcher"

    def test_keyword_route_tester(self) -> None:
        agents = self._make_agents()
        router = Router(agents=agents)
        decision = router._keyword_route("write pytest tests for the auth module")
        assert decision is not None
        assert decision.agent_name == "tester"

    def test_keyword_route_reviewer(self) -> None:
        agents = self._make_agents()
        router = Router(agents=agents)
        decision = router._keyword_route("review this code for quality")
        assert decision is not None
        assert decision.agent_name == "reviewer"

    def test_keyword_route_planner(self) -> None:
        agents = self._make_agents()
        router = Router(agents=agents)
        decision = router._keyword_route("design the architecture for this system")
        assert decision is not None
        assert decision.agent_name == "planner"

    def test_keyword_route_devops(self) -> None:
        agents = self._make_agents()
        router = Router(agents=agents)
        decision = router._keyword_route("deploy to docker container")
        assert decision is not None
        assert decision.agent_name == "devops"

    def test_keyword_route_fileops(self) -> None:
        agents = self._make_agents()
        router = Router(agents=agents)
        decision = router._keyword_route("organize the directory structure")
        assert decision is not None
        assert decision.agent_name == "fileops"

    def test_keyword_route_no_match(self) -> None:
        agents = self._make_agents()
        router = Router(agents=agents)
        decision = router._keyword_route("xyzzy foobar baz")
        assert decision is None

    def test_add_agent(self) -> None:
        agents = self._make_agents()[:3]
        router = Router(agents=agents)
        assert len(router.agents) == 3

        new_agent = self._make_agents()[3]
        router.add_agent(new_agent)
        assert len(router.agents) == 4

    def test_repr(self) -> None:
        agents = self._make_agents()[:2]
        router = Router(agents=agents)
        r = repr(router)
        assert "Router" in r
