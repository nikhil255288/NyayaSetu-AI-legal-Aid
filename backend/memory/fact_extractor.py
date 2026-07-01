# backend/memory/fact_extractor.py
"""
Extracts key legal facts from a conversation turn and stores them.
Used to build persistent case context (who, what, when, where).
"""
import json
from openai import OpenAI
from config import get_settings

_settings = get_settings()
_client = OpenAI(api_key=_settings.openrouter_api_key, base_url="https://openrouter.ai/api/v1")

EXTRACT_PROMPT = """Extract key legal facts from this message. 
Return ONLY valid JSON with these optional keys (omit keys not mentioned):
{
  "accused_name": "name if mentioned",
  "relation": "brother/father/self etc",
  "offence": "type of crime if mentioned",
  "police_station": "PS name if mentioned",
  "court": "court name if mentioned",
  "arrest_date": "date if mentioned",
  "hearing_date": "date if mentioned",
  "location": "city/district if mentioned",
  "case_number": "FIR/case number if mentioned"
}

Message: {message}"""


def extract_facts(message: str) -> dict:
    """Extract structured facts from a user message. Returns {} if nothing found."""
    try:
        response = _client.chat.completions.create(
            model=_settings.llm_model,
            messages=[{"role": "user", "content": EXTRACT_PROMPT.format(message=message)}],
            temperature=0,
            max_tokens=200,
        )
        text = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception:
        return {}