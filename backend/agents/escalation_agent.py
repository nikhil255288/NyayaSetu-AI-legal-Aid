# backend/agents/escalation_agent.py
"""
Escalation Agent — scores query complexity.
If a query is too complex or sensitive for AI, it flags for human lawyer.

Scoring factors:
  - Multiple legal domains involved (criminal + civil + family)
  - Active/ongoing case language ("my case", "I was arrested today")
  - High-stakes keywords (death sentence, custody, minor, rape)
  - Query length and ambiguity

Score 0.0 → 1.0. Threshold 0.65 → escalate.
"""
import re
from dataclasses import dataclass


@dataclass
class EscalationResult:
    should_escalate: bool
    score: float              # 0.0 to 1.0
    reasons: list[str]        # human-readable reasons


# ── Keyword weight tables ─────────────────────────────────────────────────────

HIGH_STAKES = [
    "death sentence", "capital punishment", "execution",
    "minor", "child", "juvenile", "rape", "sexual assault",
    "custody", "kidnapping", "narcotics", "terrorism",
    "encounter", "fake encounter", "wrongful conviction",
]

ACTIVE_CASE = [
    "my case", "i was arrested", "i am in jail", "i am detained",
    "my husband", "my wife", "my father", "my son", "my daughter",
    "i was charged", "police came", "they arrested", "i got bail",
    "hearing tomorrow", "next hearing", "my lawyer",
]

MULTI_DOMAIN = [
    # Criminal + Family
    ("divorce", "fir"), ("custody", "criminal"),
    ("property", "arrested"), ("dowry", "murder"),
    # Criminal + Civil
    ("contract", "fir"), ("cheque bounce", "jail"),
]

AMBIGUOUS_PATTERNS = [
    r"\bor\b.{0,20}\bor\b",          # "X or Y or Z" — confused
    r"\?.*\?",                         # multiple questions
    r"what (if|happens if|should i)",  # hypotheticals needing advice
]


def score_query(question: str) -> EscalationResult:
    """
    Analyse a user question and return an escalation decision.
    """
    q = question.lower()
    score = 0.0
    reasons = []

    # ── High-stakes keywords ──────────────────────────────────────────────────
    hits = [kw for kw in HIGH_STAKES if kw in q]
    if hits:
        score += 0.35
        reasons.append(f"High-stakes topic: {', '.join(hits[:3])}")

    # ── Active case language ──────────────────────────────────────────────────
    active_hits = [kw for kw in ACTIVE_CASE if kw in q]
    if active_hits:
        score += 0.30
        reasons.append("Appears to be an active personal case")

    # ── Multi-domain complexity ───────────────────────────────────────────────
    for pair in MULTI_DOMAIN:
        if pair[0] in q and pair[1] in q:
            score += 0.20
            reasons.append(f"Multiple legal domains: {pair[0]} + {pair[1]}")
            break

    # ── Ambiguous or multi-part question ─────────────────────────────────────
    for pat in AMBIGUOUS_PATTERNS:
        if re.search(pat, q):
            score += 0.10
            reasons.append("Complex or multi-part question")
            break

    # ── Very short query (under 5 words) — likely too vague ──────────────────
    if len(q.split()) < 5:
        score += 0.10
        reasons.append("Very short query — may need clarification")

    score = min(score, 1.0)

    return EscalationResult(
        should_escalate=score >= 0.65,
        score=round(score, 2),
        reasons=reasons,
    )