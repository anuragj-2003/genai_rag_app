"""
llm_judge.py — LLM-as-judge quality gate for retrieved chunks.
Uses Groq (max_tokens=120) to score relevance and decide proceed/rerank/reject.
Prompt is fully parameterized — no user input in system role.
"""

import os
import json
import re
from groq import Groq
from utils.constants import JUDGE_PROMPT, JUDGE_MAX_TOKENS, GROQ_MODEL

_groq_client: Groq | None = None


def _get_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set in environment")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def judge_chunks(query: str, chunks: list[dict]) -> dict:
    """
    Evaluate retrieved chunks for relevance to the query.

    Returns:
        {
            "relevance_score": float (0.0–1.0),
            "completeness": "complete" | "partial" | "insufficient",
            "recommendation": "proceed" | "rerank" | "reject"
        }
    Default on failure: proceed with score 0.5.
    """
    _DEFAULT = {
        "relevance_score": 0.5,
        "completeness": "partial",
        "recommendation": "proceed",
    }

    if not chunks:
        return {
            "relevance_score": 0.0,
            "completeness": "insufficient",
            "recommendation": "reject",
        }

    chunks_text = "\n\n---\n\n".join(
        f"[Chunk {i+1}]:\n{c['text']}" for i, c in enumerate(chunks)
    )

    prompt = JUDGE_PROMPT.format(query=query, chunks=chunks_text)

    try:
        client = _get_client()
        model = os.getenv("GROQ_MODEL", GROQ_MODEL)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a retrieval quality evaluator. Return ONLY valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=JUDGE_MAX_TOKENS,
            temperature=0.0,
        )

        content = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if "```" in content:
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
            content = match.group(1) if match else content

        parsed = json.loads(content)
        return {
            "relevance_score": float(parsed.get("relevance_score", 0.5)),
            "completeness": str(parsed.get("completeness", "partial")),
            "recommendation": str(parsed.get("recommendation", "proceed")),
        }

    except Exception as e:
        print(f"[Judge] Error: {e} — defaulting to proceed")
        return _DEFAULT
