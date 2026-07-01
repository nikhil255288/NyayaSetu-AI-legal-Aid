# backend/voice/stt.py
"""
Speech-to-Text using OpenAI Whisper (local, runs on CPU).
Converts uploaded audio → transcribed text.
Supports Hindi, Telugu, Tamil, English automatically.
"""
import tempfile
import os
from pathlib import Path

import whisper

_model = None  # loaded once on first call


def _get_model():
    global _model
    if _model is None:
        # "base" model: ~140MB, good accuracy, fast on CPU
        # swap to "small" for better Hindi accuracy (~460MB)
        _model = whisper.load_model("base")
    return _model


def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """
    Transcribe audio bytes to text.
    Returns: { text, language, confidence }
    """
    model = _get_model()

    # Write to a temp file (Whisper needs a file path)
    suffix = Path(filename).suffix or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = model.transcribe(
            tmp_path,
            task="transcribe",      # keep original language
            fp16=False,             # CPU-safe
        )
        return {
            "text": result["text"].strip(),
            "language": result.get("language", "en"),
            "confidence": "ok",
        }
    finally:
        os.unlink(tmp_path)         # clean up temp file