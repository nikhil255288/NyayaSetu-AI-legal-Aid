# backend/language/detector.py
"""
Language detection and translation for 12 Indian languages.
Uses the LLM itself for translation — no extra API needed.
"""
from openai import OpenAI
from config import get_settings

_settings = get_settings()
_client = OpenAI(api_key=_settings.openrouter_api_key, base_url="https://openrouter.ai/api/v1")

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
    "ta": "Tamil",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
}

DETECT_PROMPT = """Detect the language of this text. Reply with ONLY the ISO 639-1 code.
Supported codes: en, hi, te, ta, kn, ml, bn, mr, gu, pa, or, as
If unsure, reply: en

Text: {text}"""

TRANSLATE_PROMPT = """Translate this text to {target_language}.
Keep legal terms like section numbers, court names, and act names in their original form.
Return ONLY the translation, nothing else.

Text: {text}"""


def detect_language(text: str) -> str:
    """Returns ISO 639-1 language code."""
    if not text or len(text.strip()) < 3:
        return "en"
    # Quick heuristic: if mostly ASCII, likely English
    ascii_ratio = sum(1 for c in text if ord(c) < 128) / len(text)
    if ascii_ratio > 0.9:
        return "en"
    try:
        response = _client.chat.completions.create(
            model=_settings.llm_model,
            messages=[{"role": "user", "content": DETECT_PROMPT.format(text=text[:200])}],
            temperature=0,
            max_tokens=5,
        )
        code = response.choices[0].message.content.strip().lower()[:2]
        return code if code in SUPPORTED_LANGUAGES else "en"
    except Exception:
        return "en"


def translate_to_english(text: str, source_lang: str) -> str:
    """Translate non-English input to English for RAG retrieval."""
    if source_lang == "en":
        return text
    try:
        response = _client.chat.completions.create(
            model=_settings.llm_model,
            messages=[{"role": "user", "content": TRANSLATE_PROMPT.format(
                target_language="English", text=text
            )}],
            temperature=0,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return text


def translate_from_english(text: str, target_lang: str) -> str:
    """Translate English answer to target language."""
    if target_lang == "en" or target_lang not in SUPPORTED_LANGUAGES:
        return text
    lang_name = SUPPORTED_LANGUAGES[target_lang]
    try:
        response = _client.chat.completions.create(
            model=_settings.llm_model,
            messages=[{"role": "user", "content": TRANSLATE_PROMPT.format(
                target_language=lang_name, text=text
            )}],
            temperature=0.1,
            max_tokens=1500,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return text