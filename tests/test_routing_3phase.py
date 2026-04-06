"""Tests for 3-phase routing (keyword → embedding → LLM)."""

from unittest.mock import MagicMock

from loopagi.core.router import ROUTING_PATTERNS, RouteDecision, Router


def _make_mock_agent(name: str, role: str = "test role") -> MagicMock:
    """Create a mock agent with name and role attributes."""
    agent = MagicMock()
    agent.name = name
    agent.role = role
    agent.config = MagicMock()
    agent.config.role = role
    return agent


def test_routing_patterns_has_13_agents():
    """Router should have keyword patterns for all 13 agents."""
    expected = {
        "coder", "tester", "reviewer", "researcher", "planner",
        "fileops", "devops", "debugger", "documenter", "knowledge",
        "memory", "listener", "speaker",
    }
    assert set(ROUTING_PATTERNS.keys()) == expected


def test_keyword_routing_coder():
    """Keyword routing should route coding tasks to coder."""
    agents = [_make_mock_agent("coder"), _make_mock_agent("researcher")]
    router = Router(agents=agents, enable_embedding=False)
    decision = router._keyword_route("write a function to sort a list")
    assert decision is not None
    assert decision.agent_name == "coder"
    assert decision.method == "keyword"


def test_keyword_routing_debugger():
    """Keyword routing should route debug tasks to debugger."""
    agents = [_make_mock_agent("coder"), _make_mock_agent("debugger")]
    router = Router(agents=agents, enable_embedding=False)
    decision = router._keyword_route("debug this traceback error crash")
    assert decision is not None
    assert decision.agent_name == "debugger"


def test_keyword_routing_memory():
    """Keyword routing should route memory tasks to memory agent."""
    agents = [_make_mock_agent("coder"), _make_mock_agent("memory")]
    router = Router(agents=agents, enable_embedding=False)
    decision = router._keyword_route("remember that the user prefers FastAPI")
    assert decision is not None
    assert decision.agent_name == "memory"


def test_keyword_routing_listener():
    """Keyword routing should route voice input to listener."""
    agents = [_make_mock_agent("coder"), _make_mock_agent("listener")]
    router = Router(agents=agents, enable_embedding=False)
    decision = router._keyword_route("listen to my microphone for voice input")
    assert decision is not None
    assert decision.agent_name == "listener"


def test_keyword_routing_speaker():
    """Keyword routing should route TTS to speaker."""
    agents = [_make_mock_agent("coder"), _make_mock_agent("speaker")]
    router = Router(agents=agents, enable_embedding=False)
    decision = router._keyword_route("say hello, read aloud this text")
    assert decision is not None
    assert decision.agent_name == "speaker"


def test_keyword_routing_no_match():
    """Keyword routing should return None when no keywords match."""
    agents = [_make_mock_agent("coder")]
    router = Router(agents=agents, enable_embedding=False)
    decision = router._keyword_route("what is the meaning of life")
    assert decision is None


def test_route_decision_dataclass():
    """RouteDecision should store all fields."""
    rd = RouteDecision(
        agent_name="coder",
        confidence=0.8,
        method="embedding",
        reasoning="test",
    )
    assert rd.agent_name == "coder"
    assert rd.confidence == 0.8
    assert rd.method == "embedding"


def test_cosine_similarity():
    """Cosine similarity should compute correctly."""
    router = Router(agents=[_make_mock_agent("test")], enable_embedding=False)
    # Identical vectors → 1.0
    assert abs(router._cosine_similarity([1, 0, 0], [1, 0, 0]) - 1.0) < 0.001
    # Orthogonal vectors → 0.0
    assert abs(router._cosine_similarity([1, 0, 0], [0, 1, 0]) - 0.0) < 0.001
    # Zero vector → 0.0
    assert router._cosine_similarity([0, 0, 0], [1, 2, 3]) == 0.0


def test_router_init_with_thresholds():
    """Router should accept embedding configuration."""
    agents = [_make_mock_agent("coder")]
    router = Router(
        agents=agents,
        keyword_threshold=0.4,
        embedding_threshold=0.6,
        enable_embedding=False,
    )
    assert router.keyword_threshold == 0.4
    assert router.embedding_threshold == 0.6
    assert router.enable_embedding is False


def test_add_agent():
    """Adding an agent should register it in the router."""
    agents = [_make_mock_agent("coder")]
    router = Router(agents=agents, enable_embedding=False)
    assert len(router.agents) == 1
    router.add_agent(_make_mock_agent("tester"))
    assert len(router.agents) == 2
    assert "tester" in router.agents
