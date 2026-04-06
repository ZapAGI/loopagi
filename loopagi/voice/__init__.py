"""
LoopAGI voice I/O module.

Provides local speech-to-text (STT) via faster-whisper and
text-to-speech (TTS) via piper-tts. No cloud APIs required.

Both modules gracefully degrade if hardware (mic/speakers)
or dependencies are not available.
"""
