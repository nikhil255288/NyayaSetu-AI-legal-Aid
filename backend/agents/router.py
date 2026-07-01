# backend/agents/router.py
"""
Agent Router — the orchestration brain.

Decision tree:
  1. Score the query for complexity/escalation need
  2. If score >= 0.65 AND active case → escalate immediately
  3. Otherwise → RAG agent handles it
  4. If RAG returns empty → escalate as fallback

This is the agentic layer that makes NyayaSetu more than plain RAG.
"""
from dataclasses import dataclass

from agents.rag_agent import RAGAgent, AgentResult
from agents.escalation_agent import score_query, EscalationResult
from rag.retriever import HybridRetriever


ESCALATION_MESSAGE_LEGAL = """This query involves a complex or active legal situation 
that requires personalised legal advice beyond what an AI system can safely provide.

Relevant legal aid resources in India:
- District Legal Services Authority (DLSA) — free legal aid
- National Legal Services Authority (NALSA) — 15100 helpline
- High Court Legal Services Committee in your state"""

ESCALATION_MESSAGE_PLAIN = """Your question involves a serious or complicated legal 
situation. For your safety, we recommend speaking directly with a lawyer.

You can get FREE legal help by calling: 15100 (NALSA helpline)
This service is available to anyone who cannot afford a lawyer."""


class AgentRouter:
    def __init__(self, retriever: HybridRetriever):
        self._rag_agent = RAGAgent(retriever)

    def route(self, question: str) -> AgentResult:
        # Step 1: score the query
        escalation: EscalationResult = score_query(question)

        # Step 2: hard escalate for active high-stakes cases
        if escalation.should_escalate:
            return AgentResult(
                agent="escalation",
                legal_response=ESCALATION_MESSAGE_LEGAL,
                plain_response=ESCALATION_MESSAGE_PLAIN,
                citations=[],
                iterations=0,
                sources=[],
                escalated=True,
                escalation_reason=" | ".join(escalation.reasons),
            )

        # Step 3: try RAG
        result = self._rag_agent.run(question)

        # Step 4: if RAG found nothing, soft escalate
        if not result.sources:
            result.escalated = True
            result.escalation_reason = "No relevant statutes found"
            result.plain_response = (
                "We couldn't find relevant statute sections for your question. "
                "For personalised help, call NALSA at 15100 (free legal aid)."
            )

        return result