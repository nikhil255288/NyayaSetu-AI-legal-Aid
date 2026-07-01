# backend/api/voice.py
"""
Voice endpoint.
POST /api/voice
  - accepts: audio file (webm/wav/mp3) + optional language param
  - returns: JSON with transcription + legal/plain answers + base64 audio
"""
import base64
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from voice.stt import transcribe
from voice.tts import synthesize
from agents.router import AgentRouter
from rag.retriever import HybridRetriever

router = APIRouter()

_agent_router = None


def get_agent_router() -> AgentRouter:
    global _agent_router
    if _agent_router is None:
        _agent_router = AgentRouter(HybridRetriever())
    return _agent_router


class VoiceResponse(BaseModel):
    transcription: str          # what the user said
    detected_language: str      # language Whisper detected
    legal_response: str
    plain_response: str
    citations: list[str]
    escalated: bool
    escalation_reason: str
    audio_b64: str              # base64 MP3 of the plain_response spoken aloud


@router.post("/voice", response_model=VoiceResponse)
async def voice_query(
    audio: UploadFile = File(...),
    language: str = Form(default="en"),
):
    # ── Step 1: transcribe audio → text ──────────────────────────────────────
    audio_bytes = await audio.read()
    if len(audio_bytes) < 100:
        raise HTTPException(status_code=400, detail="Audio file is empty or too short")

    try:
        stt_result = transcribe(audio_bytes, filename=audio.filename or "audio.webm")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    question = stt_result["text"]
    detected_lang = stt_result.get("language", language)

    if not question:
        raise HTTPException(status_code=400, detail="Could not transcribe audio — please speak clearly")

    # ── Step 2: route through agent pipeline ─────────────────────────────────
    agent_router = get_agent_router()
    result = agent_router.route(question)

    # ── Step 3: synthesize plain_response → speech ───────────────────────────
    try:
        audio_bytes_out = synthesize(result.plain_response, language=detected_lang)
        audio_b64 = base64.b64encode(audio_bytes_out).decode("utf-8")
    except Exception:
        audio_b64 = ""  # TTS failure is non-fatal

    return VoiceResponse(
        transcription=question,
        detected_language=detected_lang,
        legal_response=result.legal_response,
        plain_response=result.plain_response,
        citations=result.citations,
        escalated=result.escalated,
        escalation_reason=result.escalation_reason,
        audio_b64=audio_b64,
    )