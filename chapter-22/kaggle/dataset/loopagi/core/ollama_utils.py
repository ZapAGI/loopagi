"""Minimal ollama_utils for Kaggle (Ollama not available)."""

def is_ollama_running(model: str = "") -> bool:
    """Always returns False on Kaggle — no Ollama available."""
    return False
