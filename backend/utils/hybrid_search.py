"""
hybrid_search.py — BM25 + dense retrieval merged with Reciprocal Rank Fusion (RRF).

BM25: rank_bm25 (in-memory, per-query corpus from user's ChromaDB results).
Dense: ChromaDB cosine search.
RRF: k=60 standard formula, returns top-N ranked doc IDs.
"""

from rank_bm25 import BM25Okapi
from utils import chroma_manager
from utils.constants import HYBRID_TOP_K


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercase tokenizer for BM25."""
    return text.lower().split()


def hybrid_search(query: str, user_id: str, top_k: int = HYBRID_TOP_K) -> list[dict]:
    """
    Run hybrid BM25 + dense search and merge with RRF.

    Returns top_k deduplicated chunks as:
    [{"id": str, "text": str, "score": float, "metadata": dict}]
    """
    # 1. Dense search — fetch 2x candidates to give BM25 something to rerank
    dense_hits = chroma_manager.dense_search(query, user_id, top_k=top_k * 2)

    if not dense_hits:
        return []

    # Build a corpus from the dense results for BM25
    corpus = [h["text"] for h in dense_hits]
    tokenized_corpus = [_tokenize(doc) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    # 2. BM25 scores on same corpus
    tokenized_query = _tokenize(query)
    bm25_scores = bm25.get_scores(tokenized_query)

    # Build ranked lists (index positions into dense_hits)
    bm25_ranked = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)
    dense_ranked = list(range(len(dense_hits)))  # already ranked by cosine distance

    # 3. RRF merge
    k = 60
    rrf_scores: dict[int, float] = {}
    for rank, idx in enumerate(bm25_ranked):
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (k + rank)
    for rank, idx in enumerate(dense_ranked):
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (k + rank)

    # 4. Sort by RRF score, take top_k
    merged_indices = sorted(rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True)[:top_k]

    results = []
    for idx in merged_indices:
        hit = dense_hits[idx]
        results.append({
            "id": hit["id"],
            "text": hit["text"],
            "score": rrf_scores[idx],
            "metadata": hit["metadata"],
        })

    return results
