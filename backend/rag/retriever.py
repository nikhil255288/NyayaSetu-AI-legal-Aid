# backend/rag/retriever.py
"""
Hybrid retriever: BM25 (keyword) + Dense (semantic) search.
Merges results with Reciprocal Rank Fusion (RRF).
Also supports exact section lookup like:
    "BNS section 103"
    "IPC 302"
"""

from dataclasses import dataclass
import re

from rank_bm25 import BM25Okapi
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from config import get_settings

_settings = get_settings()


@dataclass
class RetrievedChunk:
    chunk_id: str
    act: str
    section: str
    title: str
    text: str
    score: float


def _rrf(dense_ids: list[str], bm25_ids: list[str], k: int = 60) -> list[str]:
    """
    Reciprocal Rank Fusion — merges two ranked lists into one.
    """

    scores: dict[str, float] = {}

    for rank, doc_id in enumerate(dense_ids):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)

    for rank, doc_id in enumerate(bm25_ids):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)

    return sorted(scores, key=lambda x: scores[x], reverse=True)


class HybridRetriever:
    def __init__(self):

        self._client = chromadb.PersistentClient(
            path=_settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        self._model = SentenceTransformer(_settings.embedding_model)

        self._collection = self._client.get_collection(
            _settings.collection_name
        )

        # Load everything for BM25
        all_data = self._collection.get(
            include=["documents", "metadatas"]
        )

        self._all_ids: list[str] = all_data["ids"]
        self._all_docs: list[str] = all_data["documents"]
        self._all_meta: list[dict] = all_data["metadatas"]

        tokenized = [
            doc.lower().split()
            for doc in self._all_docs
        ]

        self._bm25 = BM25Okapi(tokenized)

    # ───────────────────────────────────────────────────────────────
    # Exact section lookup
    # ───────────────────────────────────────────────────────────────

    def _exact_section_lookup(self, query: str) -> list[RetrievedChunk]:

        match = re.search(
            r"\b(IPC|BNS|BNSS|CRPC)\s*(section)?\s*(\d+[A-Z]?)\b",
            query,
            re.IGNORECASE,
        )

        if not match:
            return []

        act = match.group(1).upper()
        section = match.group(3).upper()

        chunk_id = f"{act}_S{section}"

        results = self._collection.get(
            ids=[chunk_id],
            include=["documents", "metadatas"]
        )

        if not results or not results.get("ids"):
            return []

        if len(results["ids"]) == 0:
            return []

        meta = results["metadatas"][0]
        doc = results["documents"][0]
        doc_id = results["ids"][0]

        return [
            RetrievedChunk(
                chunk_id=doc_id,
                act=meta.get("act", act),
                section=meta.get("section", section),
                title=meta.get("title", ""),
                text=doc,
                score=1.0,
            )
        ]

    # ───────────────────────────────────────────────────────────────
    # Main retrieval
    # ───────────────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:

        top_k = top_k or _settings.retrieval_top_k

        # ── Exact section lookup first ────────────────────────────
        exact = self._exact_section_lookup(query)

        if exact:
            return exact

        # ── Dense retrieval ───────────────────────────────────────
        query_embedding = self._model.encode(query).tolist()

        dense_results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,
            include=["documents", "metadatas", "distances"],
        )

        dense_ids = dense_results["ids"][0]

        # ── BM25 retrieval ────────────────────────────────────────
        tokenized_query = query.lower().split()

        bm25_scores = self._bm25.get_scores(tokenized_query)

        bm25_ranked_indices = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True,
        )[: top_k * 2]

        bm25_ids = [
            self._all_ids[i]
            for i in bm25_ranked_indices
        ]

        # ── Merge with RRF ────────────────────────────────────────
        merged_ids = _rrf(
            dense_ids,
            bm25_ids
        )[:top_k]

        # ── Build result objects ──────────────────────────────────
        id_to_index = {
            doc_id: i
            for i, doc_id in enumerate(self._all_ids)
        }

        results: list[RetrievedChunk] = []

        for rank, doc_id in enumerate(merged_ids):

            idx = id_to_index.get(doc_id)

            if idx is None:
                continue

            meta = self._all_meta[idx]

            results.append(
                RetrievedChunk(
                    chunk_id=doc_id,
                    act=meta.get("act", ""),
                    section=meta.get("section", ""),
                    title=meta.get("title", ""),
                    text=self._all_docs[idx],
                    score=1 / (60 + rank + 1),
                )
            )

        return results