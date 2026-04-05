"""Tests for loopagi.agent module."""

from __future__ import annotations

from unittest.mock import MagicMock

from loopagi.core.agent import Agent, AgentConfig


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_defaults(self) -> None:
        config = AgentConfig(name="test", role="test role")
        assert config.model == "llama3.2"
        assert config.temperature == 0.7
        assert config.tools == []
        assert config.max_history == 20

    def test_custom(self) -> None:
        config = AgentConfig(name="x", role="y", model="qwen3:8b", temperature=0.3)
        assert config.model == "qwen3:8b"
        assert config.temperature == 0.3


class TestAgent:
    """Tests for the Agent class (mocked LLM, no Ollama needed)."""

    def _make_agent(self, name: str = "coder", role: str = "You code.") -> Agent:
        """Create an agent with a mocked LLM."""
        agent = Agent.__new__(Agent)
        agent.config = AgentConfig(name=name, role=role)
        agent.llm = MagicMock()
        agent.history = []
        return agent

    def test_name_property(self) -> None:
        agent = self._make_agent("coder", "You code.")
        assert agent.name == "coder"

    def test_role_property(self) -> None:
        agent = self._make_agent("coder", "You write Python.")
        assert agent.role == "You write Python."

    def test_invoke_adds_to_history(self) -> None:
        agent = self._make_agent()
        mock_response = MagicMock()
        mock_response.content = "def hello(): pass"
        agent.llm.invoke.return_value = mock_response

        result = agent.invoke("write a function")
        assert result == "def hello(): pass"
        assert len(agent.history) == 2  # human + ai

    def test_invoke_multiple_messages(self) -> None:
        agent = self._make_agent()
        mock_response = MagicMock()
        mock_response.content = "response"
        agent.llm.invoke.return_value = mock_response

        agent.invoke("msg 1")
        agent.invoke("msg 2")
        agent.invoke("msg 3")
        assert len(agent.history) == 6  # 3 pairs

    def test_reset_clears_history(self) -> None:
        agent = self._make_agent()
        mock_response = MagicMock()
        mock_response.content = "ok"
        agent.llm.invoke.return_value = mock_response

        agent.invoke("test")
        assert len(agent.history) > 0
        agent.reset()
        assert len(agent.history) == 0

    def test_history_trimming(self) -> None:
        agent = self._make_agent()
        agent.config.max_history = 2  # max 2 pairs = 4 messages
        mock_response = MagicMock()
        mock_response.content = "ok"
        agent.llm.invoke.return_value = mock_response

        for i in range(10):
            agent.invoke(f"msg {i}")

        assert len(agent.history) <= 4

    def test_build_messages_includes_system(self) -> None:
        agent = self._make_agent("coder", "You are a coder.")
        messages = agent._build_messages("hello")
        assert len(messages) >= 2
        assert messages[0].content == "You are a coder."
        assert messages[-1].content == "hello"

    def test_build_messages_includes_history(self) -> None:
        agent = self._make_agent()
        mock_response = MagicMock()
        mock_response.content = "prev answer"
        agent.llm.invoke.return_value = mock_response

        agent.invoke("previous question")
        messages = agent._build_messages("new question")
        # system + 2 history + new message = 4
        assert len(messages) == 4

    def test_repr(self) -> None:
        agent = self._make_agent("coder")
        r = repr(agent)
        assert "Agent" in r
        assert "coder" in r

    def test_invoke_handles_non_string_content(self) -> None:
        agent = self._make_agent()
        mock_response = MagicMock()
        mock_response.content = 42  # Non-string
        agent.llm.invoke.return_value = mock_response

        result = agent.invoke("test")
        assert result == "42"
