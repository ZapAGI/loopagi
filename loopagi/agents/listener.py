"""
Listener agent: voice-to-text input via local STT.

Wraps the Listener voice module to provide an agent interface
for capturing and transcribing speech from the microphone.

Usage:
    from loopagi.agents.listener import ListenerAgent

    la = ListenerAgent()
    text = la.invoke("listen")  # Captures 5s of audio
"""

from __future__ import annotations

import logging

from loopagi.voice.listener import Listener, ListenerError

logger = logging.getLogger(__name__)

LISTENER_ROLE = (
    "You are a voice input specialist. You capture audio from the "
    "microphone and transcribe it to text using local speech-to-text. "
    "You do not use any cloud APIs. When activated, you listen for a "
    "specified duration and return the transcribed text."
)

LISTENER_KEYWORDS = [
    "listen", "voice input", "microphone", "speech to text",
    "transcribe", "hear", "record audio", "stt",
]


class ListenerAgent:
    """
    Agent that wraps the Listener for voice-to-text input.

    Not a standard LLM agent. Instead of invoking a model,
    it captures audio and returns transcribed text.
    """

    def __init__(
        self,
        model_size: str = "base.en",
        device: str = "cpu",
    ) -> None:
        self.listener = Listener(model_size=model_size, device=device)
        self._name = "listener"
        self._role = LISTENER_ROLE
        self.history: list = []
        logger.info("ListenerAgent initialized")

    @property
    def name(self) -> str:
        return self._name

    @property
    def role(self) -> str:
        return self._role

    def invoke(self, message: str) -> str:
        """
        Agent-compatible invoke interface.

        Parses the message for duration hints, then records and transcribes.
        """
        # Parse duration from message if provided
        duration = 5.0
        lower = message.lower().strip()
        for word in lower.split():
            try:
                val = float(word)
                if 1.0 <= val <= 30.0:
                    duration = val
                    break
            except ValueError:
                continue

        if not self.listener.available:
            return (
                "No microphone detected. Voice input requires a microphone "
                "and the sounddevice + faster-whisper packages."
            )

        try:
            text = self.listener.listen(duration=duration)
            if not text:
                return "(No speech detected. Try speaking louder or longer.)"
            return text
        except ListenerError as e:
            return f"Voice input error: {e}"

    def reset(self) -> None:
        """Clear agent history."""
        self.history.clear()

    def __repr__(self) -> str:
        return f"ListenerAgent(available={self.listener.available})"
