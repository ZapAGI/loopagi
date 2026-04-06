"""TPU / CPU LLM Bridge for Google Cloud TPU VMs.

Loads Qwen3-8B in full precision (bfloat16/float32) on CPU.
No bitsandbytes needed — TPU VMs have 112 CPUs + 188GB RAM.

Note: model.generate() is incompatible with XLA lazy evaluation,
so we use CPU inference on TPU VMs instead of the TPU hardware.

Usage:
    from loopagi.arc.tpu_bridge import create_tpu_bridge
    bridge = create_tpu_bridge(model="unsloth/Qwen3-8B")
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global model cache (load once, reuse across all calls)
# ---------------------------------------------------------------------------

_loaded_model = None
_loaded_tokenizer = None
_loaded_model_name: str = ""


def _is_model_cached(model_name: str) -> bool:
    """Check if a HuggingFace model is already cached locally."""
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    # HF hub stores models as models--{org}--{name}
    safe_name = "models--" + model_name.replace("/", "--")
    model_dir = cache_dir / safe_name / "snapshots"
    if model_dir.exists() and any(model_dir.iterdir()):
        return True
    # Also check if model_name is a local path
    if Path(model_name).exists():
        return True
    return False


def _detect_device():
    """Detect the best available device: CUDA > CPU.

    Note: TPU (XLA) is NOT used for model.generate() because HuggingFace
    generate() uses dynamic control flow incompatible with XLA's lazy
    evaluation. On TPU VMs we use CPU instead — the 112-core CPU with
    188GB RAM can hold the full 16GB model and run inference adequately.
    """
    import torch
    if torch.cuda.is_available():
        logger.info("TPU Bridge: using CUDA device")
        return torch.device("cuda:0"), "cuda"

    logger.info("TPU Bridge: using CPU device (112 cores, 188GB RAM)")
    return torch.device("cpu"), "cpu"


def _load_model(model_name: str) -> tuple:
    """Load and cache the HuggingFace model + tokenizer on TPU.

    Uses full precision bfloat16 (no quantization needed on TPU).

    Args:
        model_name: HuggingFace model identifier or local path.

    Returns:
        Tuple of (model, tokenizer, device).
    """
    global _loaded_model, _loaded_tokenizer, _loaded_model_name

    if _loaded_model is not None and _loaded_model_name == model_name:
        device, _ = _detect_device()
        return _loaded_model, _loaded_tokenizer, device

    logger.info("TPU Bridge: loading model '%s'...", model_name)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device, device_type = _detect_device()

    # Use float16 on CUDA, float32 on CPU
    if device_type == "cuda":
        dtype = torch.float16
    else:
        dtype = torch.float32

    # Check if model is already cached locally to avoid HF Hub requests
    local_only = _is_model_cached(model_name)
    if local_only:
        logger.info("TPU Bridge: using locally cached model")

    tokenizer = AutoTokenizer.from_pretrained(
        model_name, local_files_only=local_only,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        dtype=dtype,
        device_map=None,
        local_files_only=local_only,
    )

    # Move model to device
    if device_type == "cuda":
        model = model.to(device)
        logger.info("TPU Bridge: model moved to CUDA (float16)")
    else:
        logger.info("TPU Bridge: model on CPU (float32)")

    model.eval()
    logger.info("TPU Bridge: loaded '%s' (%s)", model_name, device_type)

    _loaded_model = model
    _loaded_tokenizer = tokenizer
    _loaded_model_name = model_name

    return model, tokenizer, device


def _create_tpu_call_fn(model_name: str) -> callable:
    """Create a call function using TPU inference.

    Matches the LLMCallFn signature: (prompt, temperature) -> str

    Args:
        model_name: HuggingFace model identifier.

    Returns:
        Call function compatible with LLMBridge.
    """
    import torch

    def call(prompt: str, temperature: float | None = None) -> str:
        temp = temperature if temperature is not None else 0.3
        model, tokenizer, device = _load_model(model_name)

        # Format as chat message (Qwen3 uses ChatML format)
        messages = [{"role": "user", "content": prompt}]

        try:
            input_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        except TypeError:
            input_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )

        # Qwen3 may insert <think>\n\n</think>\n\n even with
        # enable_thinking=False — strip it from the template
        input_text = input_text.replace("<think>\n\n</think>\n\n", "")

        inputs = tokenizer(input_text, return_tensors="pt").to(device)
        input_len = inputs["input_ids"].shape[1]

        # Generation parameters
        gen_kwargs = {
            "max_new_tokens": 1024,
            "do_sample": temp > 0,
            "pad_token_id": tokenizer.eos_token_id,
        }
        if temp > 0:
            gen_kwargs["temperature"] = temp
            gen_kwargs["top_p"] = 0.9
            gen_kwargs["top_k"] = 20

        try:
            with torch.no_grad():
                outputs = model.generate(**inputs, **gen_kwargs)
            # Decode only the new tokens
            content = tokenizer.decode(
                outputs[0][input_len:], skip_special_tokens=True
            )
        except Exception as e:
            logger.warning("TPU Bridge: generation error: %s", e)
            return ""

        # Strip any residual <think>...</think> tags from output
        if "<think>" in content:
            content = re.sub(
                r"<think>.*?</think>", "", content, flags=re.DOTALL
            ).strip()

        return content

    return call


def create_tpu_bridge(
    model: str = "unsloth/Qwen3-8B",
) -> "LLMBridge":
    """Create an LLM bridge using TPU inference.

    For use on Google Cloud TPU VMs. Falls back to CUDA or CPU
    if TPU is not available.

    Args:
        model: HuggingFace model identifier or local path.

    Returns:
        LLMBridge connected to the model via TPU/CUDA/CPU.
    """
    from loopagi.arc.llm_bridge import LLMBridge

    logger.info("TPU Bridge: creating bridge for '%s'", model)
    call_fn = _create_tpu_call_fn(model)

    return LLMBridge(
        model=model,
        call_fn=call_fn,
        is_mock=False,
        model_config=None,
        default_seed=None,
    )


def unload_model() -> None:
    """Unload the cached model to free memory."""
    global _loaded_model, _loaded_tokenizer, _loaded_model_name
    if _loaded_model is not None:
        import gc
        import torch

        del _loaded_model
        del _loaded_tokenizer
        _loaded_model = None
        _loaded_tokenizer = None
        _loaded_model_name = ""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("TPU Bridge: model unloaded, memory freed")
