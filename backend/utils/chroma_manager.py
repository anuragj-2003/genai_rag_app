"""
chroma_manager.py — Local ChromaDB vector store, per-user scoped.
Embeddings: all-MiniLM-L6-v2 (44MB, cached locally, zero API cost).
"""

import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from utils.constants import CHROMA_PERSIST_DIR, CHROMA_COLLECTION, EMBEDDING_MODEL

# Lazy singletons
_client: chromadb.PersistentClient | None = None
_collection: chromadb.Collection | None = None
_encoder: SentenceTransformer | None = None


def _get_encoder() -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        print(f"[ChromaDB] Loading embedding model: {EMBEDDING_MODEL}")
        _encoder = SentenceTransformer(EMBEDDING_MODEL)
    return _encoder


def _get_collection() -> chromadb.Collection:
    global _client, _collection
    if _collection is None:
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        _collection = _client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"[ChromaDB] Collection '{CHROMA_COLLECTION}' ready at {CHROMA_PERSIST_DIR}")
    return _collection


def add_documents(chunks: list[str], user_id: str, doc_id: str, filename: str) -> int:
    """
    Embed and index chunks into ChromaDB.
    IDs are scoped as user_id:doc_id:chunk_index to prevent collisions.
    All metadata includes user_id for mandatory query filtering.
    """
    if not chunks:
        return 0

    encoder = _get_encoder()
    collection = _get_collection()

    embeddings = encoder.encode(chunks, show_progress_bar=False).tolist()
    ids = [f"{user_id}:{doc_id}:{i}" for i in range(len(chunks))]
    metadatas = [
        {"user_id": user_id, "doc_id": doc_id, "filename": filename}
        for _ in chunks
    ]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas,
    )
    return len(chunks)


def dense_search(query: str, user_id: str, top_k: int = 8) -> list[dict]:
    """
    Dense (embedding) search scoped strictly to user_id.
    Returns [{"id": str, "text": str, "score": float, "metadata": dict}]
    """
    encoder = _get_encoder()
    collection = _get_collection()

    query_emb = encoder.encode([query], show_progress_bar=False).tolist()

    results = collection.query(
        query_embeddings=query_emb,
        n_results=min(top_k, max(1, collection.count())),
        where={"user_id": {"$eq": user_id}},  # CRITICAL: always scoped
        include=["documents", "distances", "metadatas"],
    )

    hits = []
    if results and results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            hits.append({
                "id": doc_id,
                "text": results["documents"][0][i],
                "score": 1.0 - results["distances"][0][i],  # cosine: distance→similarity
                "metadata": results["metadatas"][0][i],
            })
    return hits


def get_embedding(text: str) -> list[float]:
    """Return embedding vector for a single text (used by semantic cache)."""
    encoder = _get_encoder()
    return encoder.encode([text], show_progress_bar=False)[0].tolist()


def delete_user_vectors(user_id: str):
    """
    Purge ALL vectors for a user (called on account deletion).
    CRITICAL for data isolation.
    """
    collection = _get_collection()
    try:
        collection.delete(where={"user_id": {"$eq": user_id}})
        print(f"[ChromaDB] Deleted all vectors for user {user_id}")
    except Exception as e:
        print(f"[ChromaDB] Error deleting vectors for {user_id}: {e}")


def delete_document_vectors(user_id: str, doc_id: str):
    """Delete vectors for a single document."""
    collection = _get_collection()
    try:
        collection.delete(where={
            "$and": [
                {"user_id": {"$eq": user_id}},
                {"doc_id": {"$eq": doc_id}},
            ]
        })
    except Exception as e:
        print(f"[ChromaDB] Error deleting doc {doc_id}: {e}")


def collection_count() -> int:
    try:
        return _get_collection().count()
    except Exception:
        return 0
