# backend/agents/doc_parser_agent.py
"""
Document Parser Agent.
Accepts uploaded legal documents (FIR, bail order, summons, chargesheet).
Extracts structure, identifies key legal elements, and explains in plain language.
"""
import re
from dataclasses import dataclass
from openai import OpenAI
from config import get_settings

_settings = get_settings()
_client = OpenAI(
    api_key=_settings.openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
)


@dataclass
class ParsedDocument:
    doc_type: str           # "FIR" | "bail_order" | "summons" | "chargesheet" | "unknown"
    sections_cited: list[str]   # e.g. ["IPC 302", "CrPC 41"]
    key_facts: list[str]        # bullet points extracted
    plain_explanation: str      # what this document means for the person
    legal_response: str         # formal legal reading
    urgent_actions: list[str]   # what the person should do NOW


# ── Document type detection ───────────────────────────────────────────────────

DOC_TYPE_PATTERNS = {
    "FIR": [r"first information report", r"\bF\.I\.R\b", r"fir no", r"police station"],
    "bail_order": [r"bail", r"surety", r"personal bond", r"released on bail"],
    "summons": [r"summons", r"you are hereby required", r"appear before", r"court notice"],
    "chargesheet": [r"charge sheet", r"chargesheet", r"challan", r"accused", r"framing of charge"],
}

def detect_doc_type(text: str) -> str:
    text_lower = text.lower()
    for doc_type, patterns in DOC_TYPE_PATTERNS.items():
        if any(re.search(p, text_lower) for p in patterns):
            return doc_type
    return "unknown"


def extract_section_refs(text: str) -> list[str]:
    """Find all statute references in a document."""
    patterns = [
        r"[Ss]ection\s+\d+[A-Z]?(?:\(\d+\))?(?:\([a-z]\))?\s+(?:of\s+)?(?:the\s+)?(?:IPC|BNS|CrPC|BNSS|IEA)",
        r"(?:IPC|BNS|CrPC|BNSS)\s+[Ss]ection\s+\d+[A-Z]?",
        r"u/[Ss]\s+\d+[A-Z]?(?:\(\d+\))?",   # shorthand like u/s 302
        r"Section\s+\d+[A-Z]?/\d+[A-Z]?",     # compound like 302/34
    ]
    refs = []
    for pat in patterns:
        refs.extend(re.findall(pat, text))
    return list(set(refs))[:15]  # cap at 15


PARSE_SYSTEM = """You are NyayaSetu, an expert Indian legal document analyst.
You help ordinary citizens understand legal documents they have received.
Be accurate, compassionate, and clear."""

PARSE_PROMPT = """Analyze this Indian legal document and respond in EXACTLY this format:

===KEY_FACTS===
[5-8 bullet points of the most important facts in this document, one per line, starting with •]

===LEGAL===
[Formal legal reading: what this document legally means, what rights and obligations arise, 
what the law says about this situation. Cite relevant sections.]

===PLAIN===
[Plain language explanation for someone with no legal background. 
What this document is, what it means for them personally, what they must do.]

===URGENT===
[3-5 immediate action items the person should take, one per line, starting with ACTION:]

DOCUMENT TEXT:
{text}"""


def parse_document(text: str) -> ParsedDocument:
    """Parse a legal document and return structured explanation."""
    doc_type = detect_doc_type(text)
    sections_cited = extract_section_refs(text)

    # Truncate very long documents for the LLM (keep first 3000 chars)
    truncated = text[:3000] + ("\n[... document truncated ...]" if len(text) > 3000 else "")

    response = _client.chat.completions.create(
        model=_settings.llm_model,
        messages=[
            {"role": "system", "content": PARSE_SYSTEM},
            {"role": "user", "content": PARSE_PROMPT.format(text=truncated)},
        ],
        temperature=0.1,
    )

    raw = response.choices[0].message.content

    # Parse sections
    key_facts, legal, plain, urgent = [], "", "", []

    if "===KEY_FACTS===" in raw:
        facts_section = raw.split("===KEY_FACTS===")[1].split("===")[0]
        key_facts = [
            line.strip().lstrip("•").strip()
            for line in facts_section.strip().splitlines()
            if line.strip() and line.strip() != "•"
        ]

    if "===LEGAL===" in raw:
        legal = raw.split("===LEGAL===")[1].split("===")[0].strip()

    if "===PLAIN===" in raw:
        plain = raw.split("===PLAIN===")[1].split("===")[0].strip()

    if "===URGENT===" in raw:
        urgent_section = raw.split("===URGENT===")[1].strip()
        urgent = [
            line.strip().replace("ACTION:", "").strip()
            for line in urgent_section.splitlines()
            if "ACTION:" in line
        ]

    return ParsedDocument(
        doc_type=doc_type,
        sections_cited=sections_cited,
        key_facts=key_facts,
        plain_explanation=plain or raw,
        legal_response=legal or raw,
        urgent_actions=urgent,
    )