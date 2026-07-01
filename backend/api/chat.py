# backend/api/chat.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from rag.retriever import HybridRetriever
from rag.generator import generate

from agents.router import AgentRouter
from agents.escalation_agent import score_query
from agents.router import ESCALATION_MESSAGE_LEGAL, ESCALATION_MESSAGE_PLAIN

from memory.session import get_session_memory
from memory.fact_extractor import extract_facts

from language.detector import (
    detect_language,
    translate_to_english,
    translate_from_english,
)

router = APIRouter()

_agent_router: AgentRouter | None = None


def get_router() -> AgentRouter:
    global _agent_router

    if _agent_router is None:
        retriever = HybridRetriever()
        _agent_router = AgentRouter(retriever)

    return _agent_router


class QueryRequest(BaseModel):
    question: str
    language: str = "auto"
    thread_id: str | None = None


class CitationOut(BaseModel):
    ref: str


class QueryResponse(BaseModel):
    legal_response: str
    plain_response: str
    citations: list[CitationOut]
    iterations: int
    sources: list[str]
    escalated: bool = False
    escalation_reason: str = ""
    thread_id: str = ""
    detected_language: str = "en"


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    memory = get_session_memory()
    thread = memory.get_or_create(req.thread_id)

    # Language detection
    detected_lang = req.language

    if req.language == "auto":
        detected_lang = detect_language(req.question)

    if detected_lang == "auto":
        detected_lang = "en"

    english_question = translate_to_english(req.question, detected_lang)

    # Extract and store facts
    facts = extract_facts(req.question)

    if facts:
        memory.update_facts(thread.thread_id, facts)

    memory.add_message(thread.thread_id, "user", req.question)

    # Escalation check
    escalation = score_query(english_question)

    if escalation.should_escalate:
        legal_r = translate_from_english(
            ESCALATION_MESSAGE_LEGAL,
            detected_lang,
        )

        plain_r = translate_from_english(
            ESCALATION_MESSAGE_PLAIN,
            detected_lang,
        )

        memory.add_message(thread.thread_id, "assistant", plain_r)

        return QueryResponse(
            legal_response=legal_r,
            plain_response=plain_r,
            citations=[],
            iterations=0,
            sources=[],
            escalated=True,
            escalation_reason=" | ".join(escalation.reasons),
            thread_id=thread.thread_id,
            detected_language=detected_lang,
        )

    # RAG pipeline
    agent_router = get_router()

    # Uses retriever inside AgentRouter
    retriever = agent_router._rag_agent._retriever

    chunks = retriever.retrieve(english_question)

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No relevant statute sections found.",
        )

    history = memory.get_history_for_llm(thread.thread_id)
    case_facts = thread.extracted_facts

    output = generate(
        question=english_question,
        initial_chunks=chunks,
        retriever=retriever,
        history=history,
        case_facts=case_facts,
    )

    legal_r = translate_from_english(
        output.legal_response,
        detected_lang,
    )

    plain_r = translate_from_english(
        output.plain_response,
        detected_lang,
    )

    memory.add_message(thread.thread_id, "assistant", plain_r)

    return QueryResponse(
        legal_response=legal_r,
        plain_response=plain_r,
        citations=[CitationOut(ref=c) for c in output.citations],
        iterations=output.iterations,
        sources=output.context_chunks,
        escalated=False,
        escalation_reason="",
        thread_id=thread.thread_id,
        detected_language=detected_lang,
    )


@router.get("/threads")
def list_threads():
    memory = get_session_memory()
    return {"threads": memory.list_threads()}