"""
Voice output: text-to-speech synthesis and audio playback.

Uses piper-tts for local TTS. No cloud APIs.
Gracefully degrades if speakers or dependencies are unavailable.

Usage:
    from loopagi.voice.speaker import Speaker

    speaker = Speaker()
    speaker.speak("Hello from LoopAGI")
"""

from __future__ import annotations

import logging
import tempfile
import wave
from pathlib import Path

logger = logging.getLogger(__name__)

# Default voice model (auto-downloaded by piper-tts)
DEFAULT_VOICE = "en_US-lessac-medium"
DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "loopagi" / "voices"


class SpeakerError(Exception):
    """Raised when voice output fails."""


class Speaker:
    """
    Local text-to-speech using piper-tts.

    Synthesizes speech from text and plays it through the default
    audio output device. No internet required after model download.
    """

    def __init__(
        self,
        voice: str = DEFAULT_VOICE,
        data_dir: Path | str | None = None,
    ) -> None:
        self.voice_name = voice
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._voice = None
        self._sounddevice = None
        logger.info("Speaker configured (voice=%s)", voice)

    def _ensure_voice(self):
        """Lazy-load the piper voice model."""
        if self._voice is None:
            try:
                from piper.voice import PiperVoice
            except ImportError as e:
                raise SpeakerError(
                    "piper-tts not installed. "
                    "Install with: uv pip install piper-tts"
                ) from e

            model_path = self._resolve_model()
            logger.info("Loading Piper voice: %s", model_path)
            self._voice = PiperVoice.load(str(model_path))
            logger.info("Piper voice loaded (sample_rate=%d)", self._voice.config.sample_rate)
        return self._voice

    def _ensure_sounddevice(self):
        """Lazy-load sounddevice."""
        if self._sounddevice is None:
            try:
                import sounddevice as sd
            except ImportError as e:
                raise SpeakerError(
                    "sounddevice not installed. "
                    "Install with: uv pip install sounddevice"
                ) from e
            self._sounddevice = sd
        return self._sounddevice

    def _resolve_model(self) -> Path:
        """
        Find or download the voice model.

        Checks data_dir for existing model files. If not found,
        downloads from Hugging Face using piper's built-in downloader.
        """
        # Check for existing .onnx file
        onnx_files = list(self.data_dir.glob(f"**/{self.voice_name}*.onnx"))
        if onnx_files:
            return onnx_files[0]

        # Try to download using piper's download utility
        try:
            from piper.download import ensure_voice_exists, find_voice, get_voices

            voices_info = get_voices(self.data_dir, update_voices=True)
            ensure_voice_exists(
                self.voice_name,
                data_dirs=[self.data_dir],
                download_dir=self.data_dir,
                voices_info=voices_info,
            )
            onnx_path, _ = find_voice(self.voice_name, [self.data_dir])
            return Path(onnx_path)
        except ImportError:
            raise SpeakerError(
                f"Voice model '{self.voice_name}' not found in {self.data_dir}. "
                "Download .onnx and .onnx.json files from "
                "https://huggingface.co/rhasspy/piper-voices/tree/main"
            )
        except Exception as e:
            raise SpeakerError(f"Failed to download voice '{self.voice_name}': {e}") from e

    def speak(self, text: str) -> None:
        """
        Synthesize text and play through speakers.

        Uses streaming synthesis for low latency.

        Args:
            text: Text to speak aloud.

        Raises:
            SpeakerError: If synthesis or playback fails.
        """
        import numpy as np

        sd = self._ensure_sounddevice()
        voice = self._ensure_voice()

        logger.info("Speaking: '%s'", text[:80])
        try:
            stream = sd.OutputStream(
                samplerate=voice.config.sample_rate,
                channels=1,
                dtype="int16",
            )
            stream.start()

            for audio_bytes in voice.synthesize_stream_raw(text):
                int_data = np.frombuffer(audio_bytes, dtype=np.int16)
                stream.write(int_data)

            stream.stop()
            stream.close()
        except Exception as e:
            raise SpeakerError(f"Playback failed: {e}") from e

        logger.info("Finished speaking")

    def synthesize_to_file(self, text: str, output_path: str | Path) -> Path:
        """
        Synthesize text to a WAV file.

        Args:
            text: Text to synthesize.
            output_path: Path for the output WAV file.

        Returns:
            Path to the created WAV file.
        """
        voice = self._ensure_voice()
        path = Path(output_path)

        with wave.open(str(path), "w") as wav_file:
            voice.synthesize(text, wav_file)

        logger.info("Synthesized to file: %s", path)
        return path

    @property
    def available(self) -> bool:
        """Check if voice output hardware and dependencies are available."""
        try:
            import sounddevice as sd

            devices = sd.query_devices()
            return any(d.get("max_output_channels", 0) > 0 for d in devices)
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"Speaker(voice='{self.voice_name}', available={self.available})"
