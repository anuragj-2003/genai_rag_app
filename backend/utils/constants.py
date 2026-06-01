"""
constants.py — App-wide constants, prompts, and configuration.
"""

from enum import Enum
import os

# ── Allowed file MIME types ────────────────────────────────────────────────
ALLOWED_MIME = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB hard cap

# ── LLM settings ───────────────────────────────────────────────────────────
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
ANSWER_MAX_TOKENS = 300
JUDGE_MAX_TOKENS = 120

# ── Semantic cache ──────────────────────────────────────────────────────────
CACHE_COSINE_THRESHOLD = 0.92
CACHE_TTL_DAYS = 90

# ── Hybrid search ───────────────────────────────────────────────────────────
HYBRID_TOP_K = 8        # candidates after RRF
RERANK_TOP_K = 3        # final chunks after cross-encoder

# ── ChromaDB ───────────────────────────────────────────────────────────────
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
CHROMA_COLLECTION = "rag_documents"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-12-v2"

# ── Retrieval strategy enum ─────────────────────────────────────────────────
class RetrievalStrategy(str, Enum):
    HYBRID = "hybrid"
    DIRECT_LLM = "direct_llm"
    CACHE_HIT = "cache_hit"


# ── System prompt (fixed — never embed user input here) ────────────────────
SYSTEM_PROMPT = (
    "You are a precise, helpful AI assistant. "
    "Answer ONLY from the provided document context. "
    "If the context does not contain enough information, say so clearly. "
    "Be concise — your answer must be under 300 tokens. "
    "Always cite which part of the context supports your answer."
)

# ── LLM-as-judge prompt ────────────────────────────────────────────────────
JUDGE_PROMPT = """You are a retrieval quality judge.

Query: {query}

Retrieved Chunks:
{chunks}

Evaluate whether the chunks contain sufficient information to answer the query.
Return ONLY valid JSON (no markdown, no explanation):
{{"relevance_score": 0.95, "completeness": "complete|partial|insufficient", "recommendation": "proceed|rerank|reject"}}

Rules:
- proceed   → score >= 0.85 AND completeness is complete or partial
- rerank    → score 0.70-0.84
- reject    → score < 0.70 or completeness is insufficient"""
