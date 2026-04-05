"""Tests for ModelConfig and role-based LLM routing."""

from __future__ import annotations

import pytest

from loopagi.arc.llm_bridge import (
    LLMBridge,
    ModelConfig,
    ROLE_PERCEIVER,
    ROLE_HYPOTHESIZER,
    ROLE_SYNTHESIZER,
    ROLE_REFINER,
    ROLE_DEFAULT,
)


class TestModelConfig:
    def test_default_model(self) -> None:
        config = ModelConfig(default="qwen3:8b")
        assert config.model_for_role("perceiver") == "qwen3:8b"
        assert config.model_for_role("synthesizer") == "qwen3:8b"

    def test_role_override(self) -> None:
        config = ModelConfig(
            default="qwen3:8b",
            synthesizer="qwen2.5-coder:14b",
        )
        assert config.model_for_role("perceiver") == "qwen3:8b"
        assert config.model_for_role("synthesizer") == "qwen2.5-coder:14b"

    def test_unique_models(self) -> None:
        config = ModelConfig(
            default="qwen3:8b",
            synthesizer="qwen2.5-coder:14b",
            refiner="qwen2.5-coder:14b",
        )
        unique = config.unique_models()
        assert unique == {"qwen3:8b", "qwen2.5-coder:14b"}

    def test_unique_models_single(self) -> None:
        config = ModelConfig(default="qwen3:8b")
        assert config.unique_models() == {"qwen3:8b"}

    def test_summary(self) -> None:
        config = ModelConfig(
            default="qwen3:8b",
            synthesizer="qwen2.5-coder:14b",
        )
        s = config.summary()
        assert "qwen3:8b" in s
        assert "qwen2.5-coder:14b" in s
        assert "*" in s  # override marker

    def test_unknown_role_fallback(self) -> None:
        config = ModelConfig(default="qwen3:8b")
        assert config.model_for_role("unknown_role") == "qwen3:8b"


class TestLLMBridgeCallAs:
    def test_call_as_mock_falls_back(self) -> None:
        calls: list[str] = []

        def mock_fn(prompt: str, temperature: float | None = None) -> str:
            calls.append(prompt)
            return "mock response"

        bridge = LLMBridge(
            model="mock",
            call_fn=mock_fn,
            is_mock=True,
            model_config=ModelConfig(default="qwen3:8b"),
        )
        result = bridge.call_as(ROLE_PERCEIVER, "test prompt")
        assert result == "mock response"
        assert len(calls) == 1

    def test_call_as_no_config_falls_back(self) -> None:
        calls: list[str] = []

        def mock_fn(prompt: str, temperature: float | None = None) -> str:
            calls.append(prompt)
            return "response"

        bridge = LLMBridge(
            model="test",
            call_fn=mock_fn,
            is_mock=False,
            model_config=None,
        )
        result = bridge.call_as(ROLE_SYNTHESIZER, "test")
        assert result == "response"
        assert bridge.call_count == 1

    def test_call_as_same_model_uses_default(self) -> None:
        calls: list[str] = []

        def mock_fn(prompt: str, temperature: float | None = None) -> str:
            calls.append(prompt)
            return "default response"

        config = ModelConfig(default="qwen3:8b")
        bridge = LLMBridge(
            model="qwen3:8b",
            call_fn=mock_fn,
            is_mock=False,
            model_config=config,
        )
        result = bridge.call_as(ROLE_PERCEIVER, "test")
        assert result == "default response"
        assert bridge.call_count == 1

    def test_stats_tracked_across_roles(self) -> None:
        def mock_fn(prompt: str, temperature: float | None = None) -> str:
            return "x" * 10

        bridge = LLMBridge(
            model="mock",
            call_fn=mock_fn,
            is_mock=True,
        )
        bridge.call_as(ROLE_PERCEIVER, "prompt1")
        bridge.call_as(ROLE_SYNTHESIZER, "prompt2")
        assert bridge.call_count == 2
        assert bridge.total_response_chars == 20

    def test_role_constants(self) -> None:
        assert ROLE_PERCEIVER == "perceiver"
        assert ROLE_HYPOTHESIZER == "hypothesizer"
        assert ROLE_SYNTHESIZER == "synthesizer"
        assert ROLE_REFINER == "refiner"
        assert ROLE_DEFAULT == "default"


# ---------------------------------------------------------------------------
# Phase O: Temperature forwarding
# ---------------------------------------------------------------------------


class TestBridgeTemperature:
    """Tests for temperature parameter in LLMBridge.call()."""

    def test_call_forwards_temperature(self) -> None:
        """O.3: Temperature is forwarded to the call function."""
        received_temps: list[float | None] = []

        def mock_fn(prompt: str, temperature: float | None = None) -> str:
            received_temps.append(temperature)
            return "ok"

        bridge = LLMBridge(model="mock", call_fn=mock_fn, is_mock=True)
        bridge.call("test", temperature=0.7)
        assert received_temps == [0.7]

    def test_call_default_temperature_none(self) -> None:
        """O.3: Default temperature is None (call function decides)."""
        received_temps: list[float | None] = []

        def mock_fn(prompt: str, temperature: float | None = None) -> str:
            received_temps.append(temperature)
            return "ok"

        bridge = LLMBridge(model="mock", call_fn=mock_fn, is_mock=True)
        bridge.call("test")
        assert received_temps == [None]

    def test_call_zero_temperature(self) -> None:
        """O.3: Explicit 0.0 temperature is forwarded (not confused with None)."""
        received_temps: list[float | None] = []

        def mock_fn(prompt: str, temperature: float | None = None) -> str:
            received_temps.append(temperature)
            return "ok"

        bridge = LLMBridge(model="mock", call_fn=mock_fn, is_mock=True)
        bridge.call("test", temperature=0.0)
        assert received_temps == [0.0]
