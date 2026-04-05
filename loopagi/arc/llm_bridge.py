"""ARC-AGI LLM Bridge.

Connects the multi-agent solver to real LLM inference via Ollama,
with automatic mock fallback when Ollama is unavailable.

The bridge provides a unified interface for all 5 specialist agents:
- Perceiver: describe transformations
- Hypothesizer: generate candidate rules
- Synthesizer: write Python transform functions
- Refiner: analyze failures and suggest improvements

Usage:
    bridge = create_llm_bridge(model="qwen3:8b")
    result = solve_task_with_llm(task, bridge)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Type alias for the LLM call function
# Signature: (prompt, temperature) -> response
LLMCallFn = Callable[[str, float | None], str]

# Agent roles for model routing
ROLE_PERCEIVER = "perceiver"
ROLE_HYPOTHESIZER = "hypothesizer"
ROLE_SYNTHESIZER = "synthesizer"
ROLE_REFINER = "refiner"
ROLE_DEFAULT = "default"


@dataclass
class ModelConfig:
    """Maps agent roles to specific Ollama model names.

    Enables the two-model approach where reasoning agents
    use one model and code generation agents use another.
    """

    default: str = "qwen3:8b"
    perceiver: str = ""
    hypothesizer: str = ""
    synthesizer: str = ""
    refiner: str = ""

    def model_for_role(self, role: str) -> str:
        """Get the model name for a given agent role."""
        override = getattr(self, role, "")
        return override if override else self.default

    def unique_models(self) -> set[str]:
        """Return the set of unique model names used."""
        models = {self.default}
        for role in ("perceiver", "hypothesizer", "synthesizer", "refiner"):
            m = getattr(self, role, "")
            if m:
                models.add(m)
        return models

    def summary(self) -> str:
        lines = [f"ModelConfig (default={self.default})"]
        for role in ("perceiver", "hypothesizer", "synthesizer", "refiner"):
            m = self.model_for_role(role)
            marker = " *" if m != self.default else ""
            lines.append(f"  {role}: {m}{marker}")
        return "\n".join(lines)


@dataclass
class LLMBridge:
    """Bridge between ARC solver agents and an LLM backend."""

    model: str
    call_fn: LLMCallFn
    is_mock: bool = False
    call_count: int = 0
    total_prompt_chars: int = 0
    total_response_chars: int = 0
    model_config: ModelConfig | None = None
    default_seed: int | None = None
    _role_call_fns: dict[str, LLMCallFn] = field(default_factory=dict)

    def call(self, prompt: str, temperature: float | None = None) -> str:
        """Call the LLM with a prompt and return the response.

        Args:
            prompt: The text prompt to send.
            temperature: Optional temperature override for this call.
                If None, uses the model default (0.3).
        """
        self.call_count += 1
        self.total_prompt_chars += len(prompt)
        response = self.call_fn(prompt, temperature)
        self.total_response_chars += len(response)
        logger.debug(
            "LLM call #%d: %d chars in, %d chars out",
            self.call_count, len(prompt), len(response),
        )
        return response

    def call_as(self, role: str, prompt: str) -> str:
        """Call the LLM using the model configured for a specific role.

        Falls back to the default call_fn if no role-specific model is set.
        """
        if self.is_mock or not self.model_config:
            return self.call(prompt)

        target_model = self.model_config.model_for_role(role)
        if target_model == self.model:
            return self.call(prompt)

        # Use cached role-specific call function
        if role not in self._role_call_fns:
            self._role_call_fns[role] = _create_ollama_call_fn(
                target_model, seed=self.default_seed)

        self.call_count += 1
        self.total_prompt_chars += len(prompt)
        response = self._role_call_fns[role](prompt, None)
        self.total_response_chars += len(response)
        logger.debug(
            "LLM call #%d (role=%s, model=%s): %d chars in, %d chars out",
            self.call_count, role, target_model, len(prompt), len(response),
        )
        return response

    def with_seed(self, seed: int | None) -> LLMBridge:
        """Return a new bridge using a different random seed.

        Useful for retrying stochastic phases (e.g. D4 voting) with
        different randomness while keeping stats and config.
        """
        if self.is_mock:
            return self
        new_call_fn = _create_ollama_call_fn(self.model, seed=seed)
        return LLMBridge(
            model=self.model,
            call_fn=new_call_fn,
            is_mock=False,
            call_count=self.call_count,
            total_prompt_chars=self.total_prompt_chars,
            total_response_chars=self.total_response_chars,
            model_config=self.model_config,
            default_seed=seed,
        )

    def stats(self) -> str:
        mode = "MOCK" if self.is_mock else self.model
        return (
            f"LLM Bridge ({mode}): "
            f"{self.call_count} calls, "
            f"{self.total_prompt_chars} chars sent, "
            f"{self.total_response_chars} chars received"
        )


def _create_ollama_call_fn(model: str, seed: int | None = None) -> LLMCallFn:
    """Create a call function using Ollama's REST API directly.

    Uses httpx instead of LangChain to avoid compatibility issues
    with think=False on qwen3/deepseek-r1 models.

    Args:
        model: Ollama model name.
        seed: Random seed for reproducibility. None = non-deterministic.
    """
    import re

    import httpx

    def call(prompt: str, temperature: float | None = None) -> str:
        temp = temperature if temperature is not None else 0.3
        options: dict = {"num_predict": 4096, "temperature": temp}
        if seed is not None:
            options["seed"] = seed
        payload: dict = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": options,
        }

        try:
            resp = httpx.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=120.0,
            )
            resp.raise_for_status()
            content = resp.json().get("response", "")
        except httpx.TimeoutException:
            logger.warning("LLM call timed out for model %s", model)
            return ""
        except httpx.HTTPError as e:
            logger.warning("LLM call failed for model %s: %s", model, e)
            return ""

        # Strip any residual <think>...</think> tags
        if "<think>" in content:
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        return content

    return call


def _create_mock_call_fn() -> LLMCallFn:
    """Create a deterministic mock call function for testing."""

    def call(prompt: str, temperature: float | None = None) -> str:
        prompt_lower = prompt.lower()

        if "analyze" in prompt_lower and "arc-agi" in prompt_lower:
            return (
                "The transformation appears to modify objects in the grid. "
                "Colors are preserved. Objects may be moved or reflected."
            )

        if "generate" in prompt_lower and "hypothesis" in prompt_lower:
            return (
                "RULE: Reflect the grid horizontally (flip top to bottom)\n"
                "CONFIDENCE: 0.7\n"
                "EVIDENCE: Training pairs show vertical mirroring\n"
                "\n"
                "RULE: Swap the positions of colored objects\n"
                "CONFIDENCE: 0.5\n"
                "EVIDENCE: Objects change location between input and output\n"
            )

        if "write" in prompt_lower and "python" in prompt_lower:
            return (
                "```python\n"
                "def transform(grid: list[list[int]]) -> list[list[int]]:\n"
                "    return [row[:] for row in reversed(grid)]\n"
                "```"
            )

        if "refine" in prompt_lower or "improve" in prompt_lower:
            return (
                "RULE: Apply a color mapping where each non-background "
                "color is replaced by a specific target color\n"
                "CONFIDENCE: 0.6\n"
                "FIX: Check the color mapping for each training pair\n"
            )

        return f"[Mock LLM] Acknowledged prompt ({len(prompt)} chars)"

    return call


def create_llm_bridge(
    model: str = "qwen3:8b",
    model_config: ModelConfig | None = None,
) -> LLMBridge:
    """Create an LLM bridge with automatic mock fallback.

    Args:
        model: Default Ollama model name to use.
        model_config: Optional per-agent model configuration.
            If provided, different agents can use different models.

    Returns:
        LLMBridge connected to Ollama or mock.
    """
    from loopagi.core.ollama_utils import is_ollama_running
    if is_ollama_running(model):
        logger.info("LLM Bridge: using Ollama model '%s'", model)
        if model_config:
            logger.info("Model config:\n%s", model_config.summary())
        return LLMBridge(
            model=model,
            call_fn=_create_ollama_call_fn(model),
            is_mock=False,
            model_config=model_config,
            default_seed=None,
        )

    logger.info("LLM Bridge: Ollama not available, using mock mode")
    return LLMBridge(
        model="mock",
        call_fn=_create_mock_call_fn(),
        is_mock=True,
    )


# Re-export for backward compatibility (function moved to llm_solver.py)
from loopagi.arc.llm_solver import solve_task_with_llm  # noqa: F401
