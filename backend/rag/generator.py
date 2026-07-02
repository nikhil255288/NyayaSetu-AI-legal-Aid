# backend/rag/generator.py

"""
Citation-aware generator with:
- Conversation memory
- Case context injection
- Multilingual-ready prompting
- Strict citation grounding
"""

import re
from dataclasses import dataclass

from openai import OpenAI

from config import get_settings
from rag.retriever import RetrievedChunk

_settings = get_settings()

client = OpenAI(
    api_key=_settings.openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
)


# ──────────────────────────────────────────────────────────────────────────────
# Output model
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class GeneratorOutput:
    legal_response: str
    plain_response: str
    citations: list[str]
    iterations: int
    context_chunks: list[str]


# ──────────────────────────────────────────────────────────────────────────────
# System Prompt
# ──────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are NyayaSetu, an AI legal assistant for Indian citizens.

You help ordinary citizens understand Indian law safely and clearly.

Rules:
- Use ONLY the provided CONTEXT.
- Never invent section numbers.
- Never cite statutes not present in CONTEXT.
- If a section is missing, clearly say:
  "I could not find the exact statute section in the retrieved context."
- Be accurate, compassionate, and simple.
- Use conversation history if the user refers to earlier facts.

IMPORTANT: When answering legal questions, ALWAYS include:
1. Applicable Law/Section (statute & section number)
2. What the law says (offense definition)
3. Penalty (imprisonment duration, fines)
4. Time period (if applicable)
5. Consequences (criminal record, etc.)

Return response EXACTLY in this format:

===LEGAL===
[Precise legal answer with valid section references from CONTEXT only]
Include: Applicable Section | What Happens | Penalty | Duration | Consequences

===PLAIN===
[Simple explanation anyone can understand in everyday language]
"""


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _build_context(chunks: list[RetrievedChunk]) -> str:
    """
    Convert retrieved chunks into prompt context.
    """
    return "\n\n".join(
        f"[{i+1}] {c.chunk_id}\n{c.text[:800]}"
        for i, c in enumerate(chunks)
    )


def _extract_citations(text: str) -> list[str]:
    """
    Extract citations like:
    IPC Section 302
    BNS Section 103
    CrPC Section 167
    """

    matches = re.findall(
        r"(IPC|BNS|CrPC|BNSS)\s+[Ss]ection\s+(\d+[A-Z]?(?:\(\d+\))?(?:\([a-z]\))?)",
        text,
    )

    citations = list(
        {
            f"{act} Section {section}"
            for act, section in matches
        }
    )

    return citations


def _parse_dual_output(raw: str) -> tuple[str, str]:
    """
    Parse ===LEGAL=== and ===PLAIN=== sections.
    """

    legal_response = raw.strip()
    plain_response = raw.strip()

    if "===PLAIN===" in raw and "===LEGAL===" in raw:
        parts = raw.split("===PLAIN===")

        legal_response = (
            parts[0]
            .replace("===LEGAL===", "")
            .strip()
        )

        plain_response = parts[1].strip()

    return legal_response, plain_response


def _inject_case_context(question: str, case_facts: dict) -> str:
    """
    Inject known case facts into question.
    """

    if not case_facts:
        return question

    facts_str = ", ".join(
        f"{k}: {v}"
        for k, v in case_facts.items()
        if v
    )

    return f"""
Known case facts:
{facts_str}

Question:
{question}
""".strip()


# ──────────────────────────────────────────────────────────────────────────────
# Main generation pipeline
# ──────────────────────────────────────────────────────────────────────────────

def generate(
    question: str,
    initial_chunks: list[RetrievedChunk],
    retriever=None,
    history: list[dict] | None = None,
    case_facts: dict | None = None,
) -> GeneratorOutput:

    history = history or []
    case_facts = case_facts or {}

    enriched_question = _inject_case_context(
        question,
        case_facts,
    )

    context = _build_context(initial_chunks)

    # ── Build messages ──────────────────────────────────────────────────────

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    # Add previous conversation memory
    messages.extend(history[-12:])

    # Current question
    messages.append(
        {
            "role": "user",
            "content": f"""
CONTEXT:
{context}

QUESTION:
{enriched_question}
""",
        }
    )

    # ── Generate ────────────────────────────────────────────────────────────

    response = client.chat.completions.create(
        model=_settings.llm_model,
        messages=messages,
        temperature=0.2,
    )

    raw = response.choices[0].message.content

    # ── Parse outputs ───────────────────────────────────────────────────────

    legal_response, plain_response = _parse_dual_output(raw)

    citations = _extract_citations(legal_response)

    # Fallback → retrieved chunk IDs
    if not citations:
        citations = [c.chunk_id for c in initial_chunks]

    return GeneratorOutput(
        legal_response=legal_response,
        plain_response=plain_response,
        citations=citations,
        iterations=1,
        context_chunks=[c.chunk_id for c in initial_chunks],
    )