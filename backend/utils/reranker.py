"""
reranker.py — Cross-encoder reranker to improve chunk relevance ranking.
Model: cross-encoder/ms-marco-MiniLM-L-12-v2 (~85MB, runs locally, ~80ms per batch).
Reranks 8 hybrid candidates → returns top 3.
"""

from sentence_transformers import CrossEncoder
from utils.constants import RERANKER_MODEL, RERANK_TOP_K

_reranker: CrossEncoder | None = None


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        print(f"[Reranker] Loading model: {RERANKER_MODEL}")
        _reranker = CrossEncoder(RERANKER_MODEL, max_length=512)
    return _reranker


def rerank(query: str, chunks: list[dict], top_k: int = RERANK_TOP_K) -> list[dict]:
    """
    Rerank candidate chunks using the cross-encoder.

    Args:
        query: User's search query.
        chunks: List of {"id", "text", "score", "metadata"} from hybrid search.
        top_k: Number of chunks to return after reranking (default: 3).

    Returns:
        Top-k chunks sorted by cross-encoder relevance score (descending).
    """
    if not chunks:
        return []

    reranker = _get_reranker()

    # Create (query, passage) pairs for cross-encoder
    pairs = [(query, chunk["text"]) for chunk in chunks]
    scores = reranker.predict(pairs)

    # Attach cross-encoder scores and sort
    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)

    reranked = sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)
    return reranked[:top_k]
