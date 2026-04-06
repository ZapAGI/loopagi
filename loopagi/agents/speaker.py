"""
Speaker agent: text-to-voice output via local TTS.

Wraps the Speaker voice module to provide an agent interface
for synthesizing and playing speech from text.

Usage:
    from loopagi.agents.speaker import SpeakerAgent

    sa = SpeakerAgent()
    sa.invoke("say Hello from LoopAGI")
"""

from __future__ import annotations

import logging

from loopagi.voice.speaker import Speaker, SpeakerError

logger = logging.getLogger(__name__)

SPEAKER_ROLE = (
    "You are a voice output specialist. You convert text to speech "
    "and play it through the speakers using local text-to-speech. "
    "You do not use any cloud APIs. When given text, you speak it aloud."
)

SPEAKER_KEYWORDS = [
    "say", "speak", "read aloud", "voice output", "text to speech",
    "tts", "pronounce", "narrate",
]


class SpeakerAgent:
    """
    Agent that wraps the Speaker for text-to-voice output.

    Not a standard LLM agent. Instead of invoking a model,
    it synthesizes and plays speech from text.
    """

    def __init__(
        self,
        voice: str = "en_US-lessac-medium",
    ) -> None:
        self.speaker = Speaker(voice=voice)
        self._name = "speaker"
        self._role = SPEAKER_ROLE
        self.history: list = []
        logger.info("SpeakerAgent initialized")

    @property
    def name(self) -> str:
        return self._name

    @property
    def role(self) -> str:
        return self._role

    def invoke(self, message: str) -> str:
        """
        Agent-compatible invoke interface.

        Strips command prefixes (say, speak, read) then speaks the rest.
        """
        # Strip command prefix
        text = message.strip()
        lower = text.lower()
        for prefix in ("say ", "speak ", "read aloud ", "narrate "):
            if lower.startswith(prefix):
                text = text[len(prefix):].strip()
                break

        if not text:
            return "Nothing to say. Provide text after the command."

        if not self.speaker.available:
            return (
                "No audio output device detected. Voice output requires "
                "speakers and the sounddevice + piper-tts packages."
            )

        try:
            self.speaker.speak(text)
            return f"(Spoken: {text[:100]}{'...' if len(text) > 100 else ''})"
        except SpeakerError as e:
            return f"Voice output error: {e}"

    def reset(self) -> None:
        """Clear agent history."""
        self.history.clear()

    def __repr__(self) -> str:
        return f"SpeakerAgent(available={self.speaker.available})"
