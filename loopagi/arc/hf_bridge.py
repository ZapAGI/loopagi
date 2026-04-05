"""HuggingFace LLM Bridge for Kaggle submissions.

Replaces the Ollama-based LLM bridge with direct HuggingFace/Unsloth
inference for use in Kaggle notebooks where no internet is available.

Loads Qwen3-8B (4-bit quantized via Unsloth) directly on the GPU and
provides the same LLMCallFn interface used by the rest of the pipeline.

Usage:
    from loopagi.arc.hf_bridge import create_hf_bridge
    bridge = create_hf_bridge(model="unsloth/Qwen3-8B-unsloth-bnb-4bit")
    # Use bridge exactly like the Ollama bridge
"""

from __future__ import annotations

import gc
import logging
import os
import re
from typing import TYPE_CHECKING

# v14: Force CUDA memory config (must be set before torch import)
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Global model cache (load once, reuse across all calls)
# ---------------------------------------------------------------------------

_loaded_model = None
_loaded_tokenizer = None
_loaded_model_name: str = ""


def _detect_device() -> str:
    """Detect the best available device for model inference.

    Strategy:
    1. If CUDA available AND ops work (sm_70+) -> use GPU with BnB 4-bit
    2. If CUDA reports available but ops fail (P100 + PyTorch 2.10+cu128) -> CPU
    3. No CUDA -> CPU

    Returns:
        One of: 'cuda_bnb', 'cuda_fp16', 'cpu'
    """
    import torch
    if not torch.cuda.is_available():
        logger.info("HF Bridge: No CUDA available, using CPU")
        return "cpu"

    gpu_name = torch.cuda.get_device_name(0)
    major, minor = torch.cuda.get_device_capability(0)
    cc = major * 10 + minor
    logger.info("HF Bridge: GPU=%s, compute capability=%d.%d (sm_%d)", gpu_name, major, minor, cc)

    # Test if CUDA actually works (PyTorch 2.10+cu128 dropped sm_60)
    try:
        x = torch.randn(2, 2, device="cuda:0")
        _ = x @ x.T
        del x
        torch.cuda.empty_cache()
    except RuntimeError as e:
        logger.warning(
            "HF Bridge: CUDA ops FAILED on %s (sm_%d): %s. Using CPU.",
            gpu_name, cc, str(e)[:100],
        )
        return "cpu"

    if cc >= 70:
        logger.info("HF Bridge: CUDA works, sm_%d >= 70, BnB 4-bit supported", cc)
        return "cuda_bnb"
    else:
        logger.info("HF Bridge: CUDA works but sm_%d < 70, using float16", cc)
        return "cuda_fp16"


def _load_model(model_name: str) -> tuple:
    """Load and cache the HuggingFace model + tokenizer.

    Loading strategy based on detected device:
    - cuda_bnb: BitsAndBytes 4-bit on GPU (T4/V100+, ~5GB VRAM)
    - cuda_fp16: float16 on GPU (older CUDA-capable GPUs, ~16GB VRAM)
    - cpu: float32 on CPU (~30GB RAM, slow but always works)

    Args:
        model_name: HuggingFace model identifier.

    Returns:
        Tuple of (model, tokenizer).
    """
    global _loaded_model, _loaded_tokenizer, _loaded_model_name

    if _loaded_model is not None and _loaded_model_name == model_name:
        return _loaded_model, _loaded_tokenizer

    logger.info("HF Bridge: loading model '%s'...", model_name)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    device_mode = _detect_device()

    if device_mode == "cuda_bnb":
        from transformers import BitsAndBytesConfig
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map={"": 0},
            attn_implementation="sdpa",
        )
        logger.info("HF Bridge: loaded on GPU with BitsAndBytes 4-bit")
    elif device_mode == "cuda_fp16":
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map={"": 0},
            attn_implementation="sdpa",
        )
        logger.info("HF Bridge: loaded on GPU in float16")
    else:
        # CPU fallback - use float32 for stability, no device_map needed
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            device_map="cpu",
        )
        logger.info("HF Bridge: loaded on CPU in float32 (~30GB RAM)")

    _loaded_model = model
    _loaded_tokenizer = tokenizer
    _loaded_model_name = model_name

    return model, tokenizer


def _create_hf_call_fn(model_name: str) -> callable:
    """Create a call function using direct HuggingFace inference.

    Matches the LLMCallFn signature: (prompt, temperature) -> str

    Args:
        model_name: HuggingFace model identifier.

    Returns:
        Call function compatible with LLMBridge.
    """
    import torch

    def call(prompt: str, temperature: float | None = None) -> str:
        temp = temperature if temperature is not None else 0.3
        model, tokenizer = _load_model(model_name)

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

        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
        input_len = inputs["input_ids"].shape[1]

        # Generation parameters — v15: reduced from 512 to 256 (most ARC grids fit)
        gen_kwargs = {
            "max_new_tokens": 256,
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
            # v13: aggressively free tensors to prevent OOM accumulation
            del inputs, outputs
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception as e:
            logger.warning("HF Bridge: generation error: %s", e)
            # v13: aggressive OOM recovery
            try:
                del inputs
            except Exception:
                pass
            gc.collect()
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass
            return ""

        # Strip any residual <think>...</think> tags from output
        if "<think>" in content:
            content = re.sub(
                r"<think>.*?</think>", "", content, flags=re.DOTALL
            ).strip()

        return content

    return call


def create_hf_bridge(
    model: str = "unsloth/Qwen3-8B-unsloth-bnb-4bit",
) -> "LLMBridge":
    """Create an LLM bridge using direct HuggingFace inference.

    For use in Kaggle notebooks where Ollama is not available.

    Args:
        model: HuggingFace model identifier (must be pre-downloaded
               or available as a Kaggle dataset).

    Returns:
        LLMBridge connected to HuggingFace model.
    """
    from loopagi.arc.llm_bridge import LLMBridge

    logger.info("HF Bridge: creating bridge for '%s'", model)
    call_fn = _create_hf_call_fn(model)

    return LLMBridge(
        model=model,
        call_fn=call_fn,
        is_mock=False,
        model_config=None,
        default_seed=None,
    )


def unload_model() -> None:
    """Unload the cached model to free GPU memory."""
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
        logger.info("HF Bridge: model unloaded, GPU memory freed")
