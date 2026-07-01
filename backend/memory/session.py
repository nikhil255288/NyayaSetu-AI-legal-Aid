# backend/memory/session.py
"""
Two-tier memory system:
  1. Session memory  — message history within one conversation (sent to LLM every call)
  2. Persistent memory — key facts extracted and stored in ChromaDB across sessions
"""
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from config import get_settings

_settings = get_settings()


@dataclass
class Message:
    role: str           # "user" | "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    doc_type: str = ""  # set if message was triggered by doc upload


@dataclass
class CaseThread:
    thread_id: str
    title: str          # auto-generated from first message
    created_at: str
    messages: list[Message] = field(default_factory=list)
    extracted_facts: dict = field(default_factory=dict)  # persisted case facts


class SessionMemory:
    """
    In-memory session store. Lives for the duration of one browser session.
    Key: thread_id → CaseThread
    """
    def __init__(self):
        self._threads: dict[str, CaseThread] = {}

    def create_thread(self, title: str = "") -> CaseThread:
        thread_id = str(uuid.uuid4())[:8]
        thread = CaseThread(
            thread_id=thread_id,
            title=title or f"Case {thread_id}",
            created_at=datetime.utcnow().isoformat(),
        )
        self._threads[thread_id] = thread
        return thread

    def get_thread(self, thread_id: str) -> CaseThread | None:
        return self._threads.get(thread_id)

    def get_or_create(self, thread_id: str | None) -> CaseThread:
        if thread_id and thread_id in self._threads:
            return self._threads[thread_id]
        return self.create_thread()

    def add_message(self, thread_id: str, role: str, content: str, doc_type: str = ""):
        thread = self._threads.get(thread_id)
        if not thread:
            return
        thread.messages.append(Message(role=role, content=content, doc_type=doc_type))
        # Auto-title from first user message
        if role == "user" and thread.title.startswith("Case ") and len(thread.messages) == 1:
            thread.title = content[:50] + ("…" if len(content) > 50 else "")

    def get_history_for_llm(self, thread_id: str, max_turns: int = 8) -> list[dict]:
        """Return last N turns formatted for LLM messages array."""
        thread = self._threads.get(thread_id)
        if not thread:
            return []
        recent = thread.messages[-(max_turns * 2):]
        return [{"role": m.role, "content": m.content} for m in recent]

    def update_facts(self, thread_id: str, facts: dict):
        """Store extracted case facts for this thread."""
        thread = self._threads.get(thread_id)
        if thread:
            thread.extracted_facts.update(facts)

    def list_threads(self) -> list[dict]:
        return [
            {"thread_id": t.thread_id, "title": t.title, "created_at": t.created_at,
             "message_count": len(t.messages)}
            for t in self._threads.values()
        ]


# Global singleton — shared across all requests in one server process
_session_memory = SessionMemory()

def get_session_memory() -> SessionMemory:
    return _session_memory