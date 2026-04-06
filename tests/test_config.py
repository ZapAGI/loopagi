"""Tests for the TOML configuration system."""

import tempfile
from pathlib import Path

from loopagi.core.config import (
    AgentConfig,
    LoopAGIConfig,
    RoutingConfig,
    VoiceConfig,
)


def test_default_config():
    """Default config should have sensible values."""
    config = LoopAGIConfig()
    assert config.model == "llama3.2"
    assert config.mode == "turbo"
    assert isinstance(config.voice, VoiceConfig)
    assert isinstance(config.routing, RoutingConfig)
    assert config.agents == {}


def test_voice_config_defaults():
    """Voice config defaults should be sane."""
    vc = VoiceConfig()
    assert vc.enabled is False
    assert vc.stt_model == "base.en"
    assert vc.stt_device == "cpu"
    assert vc.tts_voice == "en_US-lessac-medium"


def test_routing_config_defaults():
    """Routing config defaults should be sane."""
    rc = RoutingConfig()
    assert rc.keyword_threshold == 0.3
    assert rc.embedding_threshold == 0.5
    assert rc.enable_embedding is True


def test_load_missing_file():
    """Loading a non-existent file should return defaults."""
    config = LoopAGIConfig.load("/tmp/nonexistent_loopagi.toml")
    assert config.model == "llama3.2"


def test_load_valid_toml():
    """Loading a valid TOML should override defaults."""
    toml_content = b"""
[loopagi]
model = "qwen3:14b"
mode = "careful"

[voice]
enabled = true
stt_model = "small.en"

[routing]
keyword_threshold = 0.5
enable_embedding = false

[agents.coder]
model = "qwen2.5-coder:14b"
temperature = 0.2

[agents.reviewer]
enabled = false
"""
    with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()
        config = LoopAGIConfig.load(f.name)

    assert config.model == "qwen3:14b"
    assert config.mode == "careful"
    assert config.voice.enabled is True
    assert config.voice.stt_model == "small.en"
    assert config.routing.keyword_threshold == 0.5
    assert config.routing.enable_embedding is False
    assert "coder" in config.agents
    assert config.agents["coder"].model == "qwen2.5-coder:14b"
    assert config.agents["coder"].temperature == 0.2
    assert "reviewer" in config.agents
    assert config.agents["reviewer"].enabled is False

    Path(f.name).unlink()


def test_get_agent_model_with_override():
    """get_agent_model should return per-agent model when set."""
    config = LoopAGIConfig(
        model="llama3.2",
        agents={"coder": AgentConfig(name="coder", model="qwen2.5-coder:14b")},
    )
    assert config.get_agent_model("coder") == "qwen2.5-coder:14b"
    assert config.get_agent_model("planner") == "llama3.2"


def test_get_agent_model_fallback():
    """get_agent_model should fall back to global model."""
    config = LoopAGIConfig(model="qwen3:8b")
    assert config.get_agent_model("anything") == "qwen3:8b"


def test_is_agent_enabled():
    """is_agent_enabled should respect config."""
    config = LoopAGIConfig(
        agents={
            "coder": AgentConfig(name="coder", enabled=True),
            "reviewer": AgentConfig(name="reviewer", enabled=False),
        },
    )
    assert config.is_agent_enabled("coder") is True
    assert config.is_agent_enabled("reviewer") is False
    assert config.is_agent_enabled("unknown") is True  # default


def test_get_agent_temperature():
    """get_agent_temperature should return per-agent value or None."""
    config = LoopAGIConfig(
        agents={"coder": AgentConfig(name="coder", temperature=0.3)},
    )
    assert config.get_agent_temperature("coder") == 0.3
    assert config.get_agent_temperature("planner") is None


def test_invalid_toml_returns_defaults():
    """Invalid TOML content should return defaults gracefully."""
    with tempfile.NamedTemporaryFile(suffix=".toml", delete=False, mode="wb") as f:
        f.write(b"this is not valid toml {{{}}")
        f.flush()
        config = LoopAGIConfig.load(f.name)

    assert config.model == "llama3.2"
    Path(f.name).unlink()
