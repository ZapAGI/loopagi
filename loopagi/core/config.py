"""
TOML-based configuration system for LoopAGI.

Loads settings from loopagi.toml in the project directory,
with sensible defaults for everything. Per-agent model
configuration allows mixing different LLMs for different roles.

Usage:
    from loopagi.core.config import LoopAGIConfig

    config = LoopAGIConfig.load("loopagi.toml")
    print(config.model)
    print(config.agents["coder"].model)
"""

from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Per-agent configuration loaded from TOML."""

    name: str
    model: str | None = None  # None = use global default
    temperature: float | None = None  # None = use agent default
    enabled: bool = True


@dataclass
class RoutingConfig:
    """Routing configuration."""

    keyword_threshold: float = 0.3
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_threshold: float = 0.5
    enable_embedding: bool = True


@dataclass
class VoiceConfig:
    """Voice I/O configuration."""

    enabled: bool = False
    stt_model: str = "base.en"
    stt_device: str = "cpu"
    tts_voice: str = "en_US-lessac-medium"


@dataclass
class LoopAGIConfig:
    """
    Global configuration for the LoopAGI system.

    Loaded from loopagi.toml with defaults for everything.
    """

    model: str = "llama3.2"
    mode: str = "turbo"
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    routing: RoutingConfig = field(default_factory=RoutingConfig)
    agents: dict[str, AgentConfig] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path | None = None) -> LoopAGIConfig:
        """
        Load configuration from a TOML file.

        Falls back to defaults if file does not exist.
        """
        if path is None:
            path = Path.cwd() / "loopagi.toml"
        else:
            path = Path(path)

        if not path.exists():
            logger.info("No config file found at %s, using defaults", path)
            return cls()

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            logger.warning("Failed to parse %s: %s, using defaults", path, e)
            return cls()

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> LoopAGIConfig:
        """Parse a TOML dict into a LoopAGIConfig."""
        loopagi_section = data.get("loopagi", {})

        # Global settings
        model = loopagi_section.get("model", "llama3.2")
        mode = loopagi_section.get("mode", "turbo")

        # Voice config
        voice_data = data.get("voice", {})
        voice = VoiceConfig(
            enabled=voice_data.get("enabled", False),
            stt_model=voice_data.get("stt_model", "base.en"),
            stt_device=voice_data.get("stt_device", "cpu"),
            tts_voice=voice_data.get("tts_voice", "en_US-lessac-medium"),
        )

        # Routing config
        routing_data = data.get("routing", {})
        routing = RoutingConfig(
            keyword_threshold=routing_data.get("keyword_threshold", 0.3),
            embedding_model=routing_data.get("embedding_model", "BAAI/bge-small-en-v1.5"),
            embedding_threshold=routing_data.get("embedding_threshold", 0.5),
            enable_embedding=routing_data.get("enable_embedding", True),
        )

        # Per-agent configs
        agents: dict[str, AgentConfig] = {}
        agents_section = data.get("agents", {})
        for agent_name, agent_data in agents_section.items():
            if isinstance(agent_data, dict):
                agents[agent_name] = AgentConfig(
                    name=agent_name,
                    model=agent_data.get("model"),
                    temperature=agent_data.get("temperature"),
                    enabled=agent_data.get("enabled", True),
                )

        config = cls(
            model=model,
            mode=mode,
            voice=voice,
            routing=routing,
            agents=agents,
        )
        logger.info("Loaded config: model=%s, mode=%s, %d agent overrides", model, mode, len(agents))
        return config

    def get_agent_model(self, agent_name: str) -> str:
        """Get the model for a specific agent, falling back to global default."""
        agent_cfg = self.agents.get(agent_name)
        if agent_cfg and agent_cfg.model:
            return agent_cfg.model
        return self.model

    def get_agent_temperature(self, agent_name: str) -> float | None:
        """Get the temperature for a specific agent, or None for default."""
        agent_cfg = self.agents.get(agent_name)
        if agent_cfg and agent_cfg.temperature is not None:
            return agent_cfg.temperature
        return None

    def is_agent_enabled(self, agent_name: str) -> bool:
        """Check if an agent is enabled (default: True)."""
        agent_cfg = self.agents.get(agent_name)
        if agent_cfg:
            return agent_cfg.enabled
        return True
