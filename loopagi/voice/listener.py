"""
Voice input: microphone capture and speech-to-text transcription.

Uses faster-whisper (CTranslate2) for local STT. No cloud APIs.
Gracefully degrades if microphone or dependencies are unavailable.

Usage:
    from loopagi.voice.listener import Listener

    listener = Listener(model_size="base.en")
    text = listener.listen(duration=5.0)
    print(f"You said: {text}")
"""

from __future__ import annotations

import io
import logging
import tempfile
import wave
from pathlib import Path

logger = logging.getLogger(__name__)

# Default Whisper model for STT (small and fast for real-time use)
DEFAULT_MODEL_SIZE = "base.en"
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1
DEFAULT_DTYPE = "int16"


def _detect_device() -> tuple[str, str]:
    """Auto-detect best device and compute type for faster-whisper."""
    try:
        import torch

        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            logger.info("GPU detected: %s", gpu_name)
            return "cuda", "float16"
    except ImportError:
        pass
    return "cpu", "int8"


class ListenerError(Exception):
    """Raised when voice input fails."""


class Listener:
    """
    Local speech-to-text using faster-whisper.

    Captures audio from the default microphone and transcribes
    it using a local Whisper model. No internet required.
    Auto-detects GPU (CUDA) for faster inference.
    """

    def __init__(
        self,
        model_size: str = DEFAULT_MODEL_SIZE,
        device: str = "auto",
        compute_type: str = "auto",
    ) -> None:
        if device == "auto" or compute_type == "auto":
            detected_device, detected_compute = _detect_device()
            device = detected_device if device == "auto" else device
            compute_type = detected_compute if compute_type == "auto" else compute_type
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
        self._sounddevice = None
        logger.info(
            "Listener configured (model=%s, device=%s)",
            model_size, device,
        )

    def _ensure_model(self):
        """Lazy-load the Whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as e:
                raise ListenerError(
                    "faster-whisper not installed. "
                    "Install with: uv pip install faster-whisper"
                ) from e

            logger.info("Loading Whisper model: %s", self.model_size)
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
            logger.info("Whisper model loaded")
        return self._model

    def _ensure_sounddevice(self):
        """Lazy-load sounddevice."""
        if self._sounddevice is None:
            try:
                import sounddevice as sd
            except ImportError as e:
                raise ListenerError(
                    "sounddevice not installed. "
                    "Install with: uv pip install sounddevice"
                ) from e
            self._sounddevice = sd
        return self._sounddevice

    def listen(self, duration: float = 5.0) -> str:
        """
        Record audio from microphone and transcribe.

        Args:
            duration: Recording duration in seconds.

        Returns:
            Transcribed text string.

        Raises:
            ListenerError: If recording or transcription fails.
        """
        sd = self._ensure_sounddevice()
        model = self._ensure_model()

        logger.info("Recording %.1f seconds of audio...", duration)
        try:
            audio = sd.rec(
                int(duration * DEFAULT_SAMPLE_RATE),
                samplerate=DEFAULT_SAMPLE_RATE,
                channels=DEFAULT_CHANNELS,
                dtype=DEFAULT_DTYPE,
            )
            sd.wait()
        except Exception as e:
            raise ListenerError(f"Microphone recording failed: {e}") from e

        # Write to a temporary WAV file for faster-whisper
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            with wave.open(tmp, "wb") as wf:
                wf.setnchannels(DEFAULT_CHANNELS)
                wf.setsampwidth(2)  # 16-bit = 2 bytes
                wf.setframerate(DEFAULT_SAMPLE_RATE)
                wf.writeframes(audio.tobytes())

        try:
            segments, info = model.transcribe(
                tmp_path,
                beam_size=5,
                vad_filter=True,
            )
            text = " ".join(seg.text for seg in segments).strip()
        except Exception as e:
            raise ListenerError(f"Transcription failed: {e}") from e
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        logger.info(
            "Transcribed: '%s' (lang=%s, prob=%.2f)",
            text[:80],
            info.language,
            info.language_probability,
        )
        return text

    def transcribe_file(self, audio_path: str | Path) -> str:
        """
        Transcribe an existing audio file.

        Args:
            audio_path: Path to WAV/MP3 file.

        Returns:
            Transcribed text string.
        """
        model = self._ensure_model()
        path = str(audio_path)

        segments, info = model.transcribe(
            path,
            beam_size=5,
            vad_filter=True,
        )
        text = " ".join(seg.text for seg in segments).strip()
        logger.info("Transcribed file '%s': '%s'", path, text[:80])
        return text

    @property
    def available(self) -> bool:
        """Check if voice input hardware and dependencies are available."""
        try:
            import sounddevice as sd

            devices = sd.query_devices()
            # Check for at least one input device
            return any(d.get("max_input_channels", 0) > 0 for d in devices)
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"Listener(model='{self.model_size}', available={self.available})"
