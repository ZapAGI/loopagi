"""Tests for loopagi.pool module."""

from __future__ import annotations

from unittest.mock import MagicMock

from loopagi.core.agent import Agent, AgentConfig
from loopagi.core.pool import AgentPool, PoolResult


class TestPoolResult:
    """Tests for PoolResult dataclass."""

    def test_success(self) -> None:
        r = PoolResult(
            agent_index=0, agent_name="coder:0", task="test",
            response="ok", success=True,
        )
        assert r.success
        assert r.error is None

    def test_failure(self) -> None:
        r = PoolResult(
            agent_index=0, agent_name="coder:0", task="test",
            response="", success=False, error="timeout",
        )
        assert not r.success
        assert r.error == "timeout"


class TestAgentPool:
    """Tests for the AgentPool class (mocked LLM)."""

    def _make_pool(self, size: int = 3) -> AgentPool:
        """Create a pool with mocked agents."""
        pool = AgentPool.__new__(AgentPool)
        pool.name = "coder"
        pool.size = size
        pool._next_agent = 0

        pool.agents = []
        for i in range(size):
            agent = Agent.__new__(Agent)
            agent.config = AgentConfig(name=f"coder:{i}", role="You code.")
            agent.llm = MagicMock()
            mock_resp = MagicMock()
            mock_resp.content = f"response from agent {i}"
            agent.llm.invoke.return_value = mock_resp
            agent.history = []
            pool.agents.append(agent)

        return pool

    def test_creation(self) -> None:
        pool = self._make_pool(3)
        assert pool.name == "coder"
        assert pool.size == 3
        assert len(pool.agents) == 3

    def test_round_robin_execute(self) -> None:
        pool = self._make_pool(3)
        # First call goes to agent 0
        result = pool.execute("task 1")
        assert "response from agent 0" in result

        # Second call goes to agent 1
        result = pool.execute("task 2")
        assert "response from agent 1" in result

        # Third call goes to agent 2
        result = pool.execute("task 3")
        assert "response from agent 2" in result

        # Fourth wraps around to agent 0
        result = pool.execute("task 4")
        assert "response from agent 0" in result

    def test_reset_all(self) -> None:
        pool = self._make_pool(2)
        mock_resp = MagicMock()
        mock_resp.content = "ok"
        for agent in pool.agents:
            agent.llm.invoke.return_value = mock_resp

        pool.execute("test")
        pool.reset_all()
        for agent in pool.agents:
            assert len(agent.history) == 0

    def test_repr(self) -> None:
        pool = self._make_pool(3)
        r = repr(pool)
        assert "AgentPool" in r
        assert "coder" in r
        assert "3" in r
