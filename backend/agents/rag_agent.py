# backend/agents/rag_agent.py
"""
RAG Agent — wraps the retriever + generator into a single callable unit.
The router calls this when the query is answerable from statutes.
"""
from dataclasses import dataclass
from rag.retriever import HybridRetriever
from rag.generator import generate, GeneratorOutput


@dataclass
class AgentResult:
    agent: str                  # which agent handled it
    legal_response: str
    plain_response: str
    citations: list[str]
    iterations: int
    sources: list[str]
    escalated: bool = False
    escalation_reason: str = ""


class RAGAgent:
    def __init__(self, retriever: HybridRetriever):
        self._retriever = retriever

    def run(self, question: str) -> AgentResult:
        chunks = self._retriever.retrieve(question)

        if not chunks:
            return AgentResult(
                agent="rag",
                legal_response="",
                plain_response="No relevant statute sections found for this question.",
                citations=[],
                iterations=0,
                sources=[],
            )

        output: GeneratorOutput = generate(
            question=question,
            initial_chunks=chunks,
            retriever=self._retriever,
        )

        return AgentResult(
            agent="rag",
            legal_response=output.legal_response,
            plain_response=output.plain_response,
            citations=output.citations,
            iterations=output.iterations,
            sources=output.context_chunks,
        )