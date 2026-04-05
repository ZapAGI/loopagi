"""Tests for loopagi.ollama_utils module."""

from __future__ import annotations

from unittest.mock import patch

import loopagi.core.ollama_utils as utils
from loopagi.core.ollama_utils import MockAgent, create_agent


class TestMockAgent:
    """Tests for the MockAgent deterministic responses."""

    def test_coder_fibonacci(self) -> None:
        agent = MockAgent(name="coder", role="coding")
        resp = agent.invoke("Write a fibonacci function")
        assert "def fibonacci" in resp
        assert "```" in resp

    def test_coder_palindrome(self) -> None:
        agent = MockAgent(name="coder", role="coding")
        resp = agent.invoke("Check palindrome")
        assert "palindrome" in resp.lower()

    def test_coder_stack(self) -> None:
        agent = MockAgent(name="coder", role="coding")
        resp = agent.invoke("Implement a stack")
        assert "class Stack" in resp

    def test_coder_generic(self) -> None:
        agent = MockAgent(name="coder", role="coding")
        resp = agent.invoke("Something else entirely")
        assert "def " in resp

    def test_tester_fibonacci(self) -> None:
        agent = MockAgent(name="tester", role="testing")
        resp = agent.invoke("Write tests for fibonacci")
        assert "test_" in resp
        assert "assert" in resp

    def test_tester_stack(self) -> None:
        agent = MockAgent(name="tester", role="testing")
        resp = agent.invoke("Write tests for stack")
        assert "test_" in resp

    def test_reviewer_first_call_revision(self) -> None:
        agent = MockAgent(name="reviewer", role="review")
        resp = agent.invoke("Review this code")
        assert "REVISION NEEDED" in resp

    def test_reviewer_second_call_approved(self) -> None:
        agent = MockAgent(name="reviewer", role="review")
        agent.invoke("Review this code")
        resp = agent.invoke("Review revised code")
        assert "APPROVED" in resp

    def test_planner(self) -> None:
        agent = MockAgent(name="planner", role="planning")
        resp = agent.invoke("Plan this feature")
        assert "Plan" in resp or "plan" in resp

    def test_researcher(self) -> None:
        agent = MockAgent(name="researcher", role="research")
        resp = agent.invoke("Research best practices")
        assert "Research" in resp or "approach" in resp

    def test_generic_agent(self) -> None:
        agent = MockAgent(name="fileops", role="file management")
        resp = agent.invoke("Do something")
        assert "fileops" in resp

    def test_reset(self) -> None:
        agent = MockAgent(name="coder", role="coding")
        agent.invoke("test")
        agent.invoke("test")
        assert agent._call_count == 2
        agent.reset()
        assert agent._call_count == 0

    def test_repr(self) -> None:
        agent = MockAgent(name="test", role="testing")
        assert "MockAgent" in repr(agent)


class TestCreateAgent:
    """Tests for the create_agent factory."""

    @patch.object(utils, "_OLLAMA_AVAILABLE", False)
    def test_creates_mock_when_ollama_down(self) -> None:
        agent = create_agent(name="coder", role="coding")
        assert isinstance(agent, MockAgent)

    @patch.object(utils, "_OLLAMA_AVAILABLE", False)
    def test_mock_agent_responds(self) -> None:
        agent = create_agent(name="coder", role="coding")
        resp = agent.invoke("Write fibonacci")
        assert len(resp) > 0


class TestRequireOllama:
    """Tests for the require_ollama helper."""

    @patch.object(utils, "_OLLAMA_AVAILABLE", False)
    def test_prints_mock_mode(self, capsys) -> None:
        result = utils.require_ollama()
        assert result is False
        captured = capsys.readouterr()
        assert "MOCK MODE" in captured.out

    @patch.object(utils, "_OLLAMA_AVAILABLE", True)
    def test_returns_true_when_available(self) -> None:
        result = utils.require_ollama()
        assert result is True
