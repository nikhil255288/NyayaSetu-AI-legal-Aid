# backend/data/ingest.py
"""
One-time script: reads corpus text files, chunks them, embeds them.
Run this before starting the server.

Usage:
    cd backend
    python data/ingest.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.chunker import chunk_statute
from rag.embedder import embed_and_store, collection_count

CORPUS_DIR = Path(__file__).parent / "corpus"

# Map filename → act label used in chunk IDs
ACT_MAP = {
    "IPC.txt": "IPC",
    "BPS.txt": "BPS",
    "BNS.txt": "BNS",
    "BNSS.txt": "BNSS",
    "CrPC.txt": "CrPC",
    "MVA.txt": "MVA",
}


def ingest_all():
    total = 0

    for filename, act_name in ACT_MAP.items():
        filepath = CORPUS_DIR / filename

        if not filepath.exists():
            print(f"[SKIP] {filename} not found in corpus/")
            continue

        print(f"[READ] {filename} ...")
        raw_text = filepath.read_text(encoding="utf-8", errors="ignore")

        print(f"[CHUNK] Chunking {act_name} ...")
        chunks = chunk_statute(raw_text, act_name)
        print(f"  → {len(chunks)} chunks created")

        print(f"[EMBED] Embedding {act_name} ...")
        stored = embed_and_store(chunks)
        print(f"  → {stored} chunks stored in ChromaDB")

        total += stored

    print(f"\n✅ Done. Stored this run: {total}")
    print(f"✅ Total chunks in DB: {collection_count()}")


if __name__ == "__main__":
    ingest_all()