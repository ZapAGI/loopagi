"""
Shared Ollama utilities for chapter examples.

Provides graceful fallback when Ollama is not running,
so readers can see the flow of every demo even without
a local LLM. When Ollama IS available, examples use real
inference. When it is not, they use deterministic mock
responses that illustrate the same patterns.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_OLLAMA_AVAILABLE: bool | None = None


def is_ollama_running(model: str = "llama3.2") -> bool:
    """
    Check if Ollama is reachable and the model is pulled.

    Result is cached after the first call.
    """
    global _OLLAMA_AVAILABLE
    if _OLLAMA_AVAILABLE is not None:
        return _OLLAMA_AVAILABLE

    try:
        import httpx

        resp = httpx.get("http://localhost:11434/api/tags", timeout=3)
        if resp.status_code != 200:
            _OLLAMA_AVAILABLE = False
            return False
        models = [m["name"] for m in resp.json().get("models", [])]
        base_names = [m.split(":")[0] for m in models]
        model_base = model.split(":")[0]
        _OLLAMA_AVAILABLE = model_base in base_names or model in models
        return _OLLAMA_AVAILABLE
    except Exception:
        _OLLAMA_AVAILABLE = False
        return False


def require_ollama(model: str = "llama3.2") -> bool:
    """
    Print a friendly message if Ollama is not available.

    Returns True if Ollama is ready, False otherwise.
    """
    if is_ollama_running(model):
        return True

    print(f"\n  [MOCK MODE] Ollama not detected (model: {model}).")
    print("  Install: https://ollama.ai  |  Then: ollama pull llama3.2")
    print("  Running with deterministic mock responses.\n")
    return False


class MockAgent:
    """
    Deterministic mock agent for demos when Ollama is unavailable.

    Produces canned responses keyed by agent role, so readers
    can see the full flow of every demo without a GPU.
    """

    def __init__(self, name: str, role: str, **kwargs: Any) -> None:
        self.name = name
        self.role = role
        self._call_count = 0

    def invoke(self, message: str) -> str:
        self._call_count += 1
        return self._generate_mock(message)

    async def ainvoke(self, message: str) -> str:
        self._call_count += 1
        return self._generate_mock(message)

    def reset(self) -> None:
        self._call_count = 0

    def _generate_mock(self, message: str) -> str:
        """Generate a deterministic mock response based on agent name."""
        msg_lower = message.lower()

        if self.name == "coder" or "code" in self.role.lower():
            return self._mock_coder(msg_lower)
        elif self.name == "tester" or "test" in self.role.lower():
            return self._mock_tester(msg_lower)
        elif self.name == "reviewer" or "review" in self.role.lower():
            return self._mock_reviewer(msg_lower)
        elif self.name == "planner" or "plan" in self.role.lower():
            return self._mock_planner(msg_lower)
        elif self.name == "researcher" or "research" in self.role.lower():
            return self._mock_researcher(msg_lower)
        else:
            return f"[{self.name}] Acknowledged: {message[:80]}"

    def _mock_coder(self, msg: str) -> str:
        if "fibonacci" in msg or "fib" in msg:
            return (
                "```python\n"
                "def fibonacci(n: int) -> int:\n"
                '    """Return the nth Fibonacci number."""\n'
                "    if n < 0:\n"
                '        raise ValueError("n must be non-negative")\n'
                "    if n <= 1:\n"
                "        return n\n"
                "    a, b = 0, 1\n"
                "    for _ in range(2, n + 1):\n"
                "        a, b = b, a + b\n"
                "    return b\n"
                "```"
            )
        if "palindrome" in msg:
            return (
                "```python\n"
                "def is_palindrome(s: str) -> bool:\n"
                '    """Check if a string is a palindrome."""\n'
                "    if not isinstance(s, str):\n"
                '        raise TypeError("Input must be a string")\n'
                "    cleaned = s.lower().replace(' ', '')\n"
                "    return cleaned == cleaned[::-1]\n"
                "```"
            )
        if "stack" in msg:
            return (
                "```python\n"
                "class Stack:\n"
                '    """A simple stack data structure."""\n'
                "    def __init__(self) -> None:\n"
                "        self._items: list = []\n\n"
                "    def push(self, item) -> None:\n"
                "        self._items.append(item)\n\n"
                "    def pop(self):\n"
                "        if self.is_empty():\n"
                '            raise IndexError("pop from empty stack")\n'
                "        return self._items.pop()\n\n"
                "    def peek(self):\n"
                "        if self.is_empty():\n"
                '            raise IndexError("peek at empty stack")\n'
                "        return self._items[-1]\n\n"
                "    def is_empty(self) -> bool:\n"
                "        return len(self._items) == 0\n\n"
                "    def size(self) -> int:\n"
                "        return len(self._items)\n"
                "```"
            )
        return (
            "```python\n"
            "def solve(input_data):\n"
            '    """Solution implementation."""\n'
            "    # Implementation based on requirements\n"
            "    return process(input_data)\n"
            "```"
        )

    def _mock_tester(self, msg: str) -> str:
        if "fibonacci" in msg or "fib" in msg:
            return (
                "```python\n"
                "import pytest\n"
                "from solution import fibonacci\n\n"
                "def test_base_cases():\n"
                "    assert fibonacci(0) == 0\n"
                "    assert fibonacci(1) == 1\n\n"
                "def test_sequence():\n"
                "    assert fibonacci(10) == 55\n"
                "    assert fibonacci(20) == 6765\n\n"
                "def test_negative_raises():\n"
                "    with pytest.raises(ValueError):\n"
                "        fibonacci(-1)\n"
                "```"
            )
        if "stack" in msg:
            return (
                "```python\n"
                "import pytest\n"
                "from solution import Stack\n\n"
                "def test_push_pop():\n"
                "    s = Stack()\n"
                "    s.push(1)\n"
                "    assert s.pop() == 1\n\n"
                "def test_empty_pop_raises():\n"
                "    s = Stack()\n"
                "    with pytest.raises(IndexError):\n"
                "        s.pop()\n\n"
                "def test_size():\n"
                "    s = Stack()\n"
                "    assert s.size() == 0\n"
                "    s.push(42)\n"
                "    assert s.size() == 1\n"
                "```"
            )
        return (
            "```python\n"
            "import pytest\n\n"
            "def test_happy_path():\n"
            "    assert solve('input') is not None\n\n"
            "def test_edge_case():\n"
            "    assert solve('') == default\n"
            "```"
        )

    def _mock_reviewer(self, msg: str) -> str:
        if self._call_count <= 1:
            return (
                "REVISION NEEDED\n\n"
                "1. Missing input validation for edge cases\n"
                "2. No docstring on helper functions\n"
                "3. Consider using iterative approach for performance\n"
                "4. Add type hints to all parameters"
            )
        return (
            "APPROVED\n\n"
            "Code quality: 8/10\n"
            "- Clean implementation with proper type hints\n"
            "- Good error handling\n"
            "- Tests cover happy path and edge cases\n"
            "- Well-documented with docstrings"
        )

    def _mock_planner(self, msg: str) -> str:
        return (
            "Implementation Plan:\n"
            "1. Define the function signature with type hints\n"
            "2. Handle edge cases (empty input, invalid types)\n"
            "3. Implement core algorithm\n"
            "4. Add comprehensive docstring\n"
            "5. Write unit tests for all paths\n"
            "6. Review for performance and style"
        )

    def _mock_researcher(self, msg: str) -> str:
        return (
            "Research Summary:\n"
            "- Multiple approaches exist in the literature\n"
            "- The iterative approach is O(n) time, O(1) space\n"
            "- The recursive approach is O(2^n) without memoization\n"
            "- Best practice: iterative with clear variable names\n"
            "- Reference: CLRS Chapter 15, Dynamic Programming"
        )

    def __repr__(self) -> str:
        return f"MockAgent(name='{self.name}')"


def create_agent(
    name: str,
    role: str,
    model: str = "llama3.2",
    **kwargs: Any,
):
    """
    Create an Agent or MockAgent depending on Ollama availability.

    This is the recommended way to create agents in chapter demos.
    """
    if is_ollama_running(model):
        from loopagi.core.agent import Agent
        return Agent(name=name, role=role, model=model, **kwargs)
    else:
        return MockAgent(name=name, role=role, **kwargs)
