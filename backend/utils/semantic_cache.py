"""
semantic_cache.py — SQLite-backed semantic similarity cache.
Cosine threshold: 0.92 (configurable via constants).
TTL: 90 days (configurable).
Embeddings stored as raw float32 bytes for fast numpy deserialization.
"""

import struct
import numpy as np
from utils.app_db import cache_get_all, cache_insert, cache_purge_expired
from utils import chroma_manager
from utils.constants import CACHE_COSINE_THRESHOLD, CACHE_TTL_DAYS


def _emb_to_bytes(emb: list[float]) -> bytes:
    """Serialize embedding list to packed float32 bytes."""
    return struct.pack(f"{len(emb)}f", *emb)


def _bytes_to_emb(b: bytes) -> np.ndarray:
    """Deserialize packed float32 bytes back to numpy array."""
    n = len(b) // 4
    return np.array(struct.unpack(f"{n}f", b), dtype=np.float32)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def cache_lookup(query: str) -> str | None:
    """
    Check if a semantically similar query exists in cache.
    Returns the cached response string if cosine similarity >= threshold, else None.
    """
    # Purge expired entries first (lightweight, happens on every lookup)
    cache_purge_expired()

    query_emb = np.array(chroma_manager.get_embedding(query), dtype=np.float32)
    entries = cache_get_all()

    best_score = 0.0
    best_response = None

    for entry in entries:
        stored_emb = _bytes_to_emb(entry["query_emb"])
        score = _cosine(query_emb, stored_emb)
        if score > best_score:
            best_score = score
            best_response = entry["response"]

    if best_score >= CACHE_COSINE_THRESHOLD:
        return best_response
    return None


def cache_store(query: str, response: str):
    """Store a query-response pair in the semantic cache."""
    emb = chroma_manager.get_embedding(query)
    emb_bytes = _emb_to_bytes(emb)
    cache_insert(
        query_text=query,
        query_emb=emb_bytes,
        response=response,
        ttl_days=CACHE_TTL_DAYS,
    )
