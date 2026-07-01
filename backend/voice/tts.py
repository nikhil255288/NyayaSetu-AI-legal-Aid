# backend/voice/tts.py
"""
Text-to-Speech using gTTS (Google TTS, free, no API key needed).
Converts answer text → MP3 bytes.
"""
import io
from gtts import gTTS

# Language codes gTTS supports for Indian languages
LANG_MAP = {
    "en": "en",
    "hi": "hi",
    "te": "te",
    "ta": "ta",
    "kn": "kn",
    "ml": "ml",
    "bn": "bn",
    "mr": "mr",
}


def synthesize(text: str, language: str = "en") -> bytes:
    """
    Convert text to MP3 audio bytes.
    language: ISO 639-1 code ("en", "hi", "te", etc.)
    """
    lang_code = LANG_MAP.get(language, "en")

    # Truncate very long texts (TTS works best under ~500 words)
    words = text.split()
    if len(words) > 500:
        text = " ".join(words[:500]) + "..."

    tts = gTTS(text=text, lang=lang_code, slow=False)

    buffer = io.BytesIO()
    tts.write_to_fp(buffer)
    buffer.seek(0)
    return buffer.read()