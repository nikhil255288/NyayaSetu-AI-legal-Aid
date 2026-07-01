# backend/rag/embedder.py
"""
Embeds StatuteChunks and stores them in ChromaDB.
Uses a local sentence-transformer model — no API cost for embeddings.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from config import get_settings
from rag.chunker import StatuteChunk

_settings = get_settings()


def _get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(
        path=_settings.chroma_persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _get_model() -> SentenceTransformer:
    # Downloads once, cached locally (~90 MB)
    return SentenceTransformer(_settings.embedding_model)


def make_unique_ids(chunks: list[StatuteChunk]) -> list[str]:
    """
    Ensure all chunk IDs are unique for ChromaDB.
    Example:
        BNS_S147
        BNS_S147_1
        BNS_S147_2
    """
    seen = {}
    unique_ids = []

    for chunk in chunks:
        base_id = chunk.chunk_id

        if base_id not in seen:
            seen[base_id] = 0
            unique_ids.append(base_id)
        else:
            seen[base_id] += 1
            unique_ids.append(f"{base_id}_{seen[base_id]}")

    return unique_ids


def embed_and_store(chunks: list[StatuteChunk]) -> int:
    """
    Embed a list of chunks and upsert into ChromaDB.
    Returns the number of chunks stored.
    Safe to call multiple times.
    """

    if not chunks:
        return 0

    client = _get_client()

    collection = client.get_or_create_collection(
        name=_settings.collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    model = _get_model()

    texts = [c.text for c in chunks]

    # FIXED: prevent duplicate IDs
    ids = make_unique_ids(chunks)

    metadatas = [
        {
            "act": c.act,
            "chapter": c.chapter,
            "section": c.section,
            "sub_clause": c.sub_clause,
            "title": c.title,
            **c.metadata,
        }
        for c in chunks
    ]

    # Embed in batches
    batch_size = 64
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        embeddings = model.encode(
            batch,
            show_progress_bar=False
        ).tolist()

        all_embeddings.extend(embeddings)

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=all_embeddings,
        metadatas=metadatas,
    )

    return len(chunks)


def collection_count() -> int:
    """
    Return total chunks stored in ChromaDB.
    """
    client = _get_client()

    try:
        collection = client.get_collection(_settings.collection_name)
        return collection.count()

    except Exception:
        return 0