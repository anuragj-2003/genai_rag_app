"""
routers/chat.py — 7-Stage RAG Pipeline (/api/v1/chat/*)

Stage 1: Semantic cache check (cosine ≥ 0.92)
Stage 2: Hybrid BM25 + dense search → RRF top-8
Stage 3: Cross-encoder rerank → top-3
Stage 4: LLM-as-judge quality gate (proceed/rerank/reject)
Stage 5: Groq answer (max_tokens=300, system/user separated)
Stage 6: Log to SQLite, cache response

Rate limited: 20 requests/minute per IP via slowapi.
"""

import os
import time
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from groq import Groq

from routers.auth import get_current_user, UserOut
from utils.security import sanitize_query
from utils.semantic_cache import cache_lookup, cache_store
from utils.hybrid_search import hybrid_search
from utils.reranker import rerank
from utils.llm_judge import judge_chunks
from utils.app_db import (
    log_interaction, get_recent_chat_turns,
    create_conversation, get_conversations, get_conversation_messages,
    update_conversation, delete_conversation, get_conversation_owner,
    get_guest_uses, increment_guest_uses
)
from utils.logging_utils import log_query
from utils.constants import SYSTEM_PROMPT, GROQ_MODEL, ANSWER_MAX_TOKENS

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
limiter = Limiter(key_func=get_remote_address)

GUEST_LIMIT = 5
_groq_client: Groq | None = None


def _get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not configured")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


# ── Pydantic models ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    judge_score: float = 0.0
    cache_hit: bool = False
    source: str = "hybrid"
    chunks_used: int = 0


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None


# ── Main chat endpoint ────────────────────────────────────────────────────────

@router.post("/", response_model=ChatResponse)
@limiter.limit("20/minute")
def chat(
    request: Request,
    body: ChatRequest,
    current_user: UserOut = Depends(get_current_user)
):
    t0 = time.time()
    user_id = current_user.id

    # Guest limit check
    if current_user.is_guest:
        uses = get_guest_uses(user_id)
        if uses >= GUEST_LIMIT:
            raise HTTPException(status_code=403, detail="Demo limit reached. Please sign up.")
        increment_guest_uses(user_id)

    # Ensure conversation exists
    conv_id = body.conversation_id
    if not conv_id:
        conv_id = str(uuid.uuid4())
        title = body.message[:40].strip() + ("..." if len(body.message) > 40 else "")
        create_conversation(conv_id, user_id, title)

    # Sanitize user input (prompt injection prevention)
    clean_query = sanitize_query(body.message)

    # ── Stage 1: Semantic cache ──────────────────────────────────────────────
    cached = cache_lookup(clean_query)
    if cached:
        latency = round((time.time() - t0) * 1000)
        log_query(user_id, judge_score=1.0, cache_hit=True,
                  tokens_in=0, tokens_out=0, latency_ms=latency)
        log_interaction(
            user_id=user_id, conversation_id=conv_id, query=clean_query,
            response=cached, chunks=[], judge_score=1.0, recommendation="cache_hit",
            tokens_in=0, tokens_out=0, latency_ms=latency,
            cache_hit=True, source="semantic_cache"
        )
        return ChatResponse(
            response=cached,
            conversation_id=conv_id,
            judge_score=1.0,
            cache_hit=True,
            source="semantic_cache",
            chunks_used=0,
        )

    # ── Stage 2: Hybrid BM25 + dense → RRF ──────────────────────────────────
    hybrid_hits = hybrid_search(clean_query, user_id, top_k=8)

    # ── Stage 3: Cross-encoder rerank ────────────────────────────────────────
    if hybrid_hits:
        top_chunks = rerank(clean_query, hybrid_hits, top_k=3)
    else:
        top_chunks = []

    # ── Stage 4: LLM judge ───────────────────────────────────────────────────
    judge_result = {"relevance_score": 0.5, "recommendation": "proceed"}
    recommendation = "proceed"

    if top_chunks:
        judge_result = judge_chunks(clean_query, top_chunks)
        recommendation = judge_result.get("recommendation", "proceed")

        if recommendation == "reject":
            # No useful context — answer from general knowledge
            top_chunks = []

    # ── Stage 5: Groq answer ─────────────────────────────────────────────────
    model = body.model or os.getenv("GROQ_MODEL", GROQ_MODEL)
    groq = _get_groq()

    # Build context block (never embed in system prompt — always user role)
    context_block = ""
    if top_chunks:
        context_block = "\n\n".join(
            f"[Source {i+1}]:\n{c['text']}" for i, c in enumerate(top_chunks)
        )

    # Chat history (last 6 turns)
    history = get_recent_chat_turns(conv_id, limit=6)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    messages.extend(history)

    user_content = f"Query: {clean_query}"
    if context_block:
        user_content += f"\n\nRelevant Document Sections:\n{context_block}"

    messages.append({"role": "user", "content": user_content})

    try:
        completion = groq.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=ANSWER_MAX_TOKENS,
            temperature=0.3,
        )
        response_text = completion.choices[0].message.content.strip()
        tokens_in = completion.usage.prompt_tokens if completion.usage else 0
        tokens_out = completion.usage.completion_tokens if completion.usage else 0
    except Exception as e:
        raise HTTPException(status_code=503, detail="LLM service temporarily unavailable.")

    # ── Stage 6: Log + cache ─────────────────────────────────────────────────
    latency = round((time.time() - t0) * 1000)
    judge_score = judge_result.get("relevance_score", 0.5)

    log_interaction(
        user_id=user_id, conversation_id=conv_id, query=clean_query,
        response=response_text,
        chunks=[c["text"] for c in top_chunks],
        judge_score=judge_score,
        recommendation=recommendation,
        tokens_in=tokens_in, tokens_out=tokens_out,
        latency_ms=latency, cache_hit=False,
        source="hybrid" if top_chunks else "direct_llm",
    )

    # Cache if judge approved and we have good context
    if recommendation in ("proceed", "rerank") and judge_score >= 0.85:
        try:
            cache_store(clean_query, response_text)
        except Exception:
            pass  # Cache failure is non-fatal

    log_query(user_id, judge_score=judge_score, cache_hit=False,
              tokens_in=tokens_in, tokens_out=tokens_out, latency_ms=latency,
              recommendation=recommendation)

    return ChatResponse(
        response=response_text,
        conversation_id=conv_id,
        judge_score=judge_score,
        cache_hit=False,
        source="hybrid" if top_chunks else "direct_llm",
        chunks_used=len(top_chunks),
    )


# ── Conversation management endpoints ────────────────────────────────────────

@router.get("/history")
def list_conversations(current_user: UserOut = Depends(get_current_user)):
    return get_conversations(current_user.id)


@router.get("/history/{conversation_id}")
def get_conversation(conversation_id: str, current_user: UserOut = Depends(get_current_user)):
    owner = get_conversation_owner(conversation_id)
    if not owner or owner != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized.")
    return get_conversation_messages(conversation_id)


@router.put("/conversations/{conversation_id}")
def update_conv(
    conversation_id: str,
    body: ConversationUpdate,
    current_user: UserOut = Depends(get_current_user)
):
    owner = get_conversation_owner(conversation_id)
    if not owner or owner != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized.")
    update_conversation(conversation_id, current_user.id, body.title, body.is_pinned)
    return {"message": "Updated."}


@router.delete("/conversations/{conversation_id}")
def delete_conv(conversation_id: str, current_user: UserOut = Depends(get_current_user)):
    owner = get_conversation_owner(conversation_id)
    if not owner or owner != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized.")
    delete_conversation(conversation_id, current_user.id)
    return {"message": "Deleted."}
