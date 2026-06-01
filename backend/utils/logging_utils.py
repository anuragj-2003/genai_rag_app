"""
logging_utils.py — Structured JSON logging to stdout.
All events are emitted as single-line JSON for easy ingestion by log aggregators.
"""

import json
import logging
import sys
from datetime import datetime

# Configure root logger to output to stdout with minimal formatting
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter("%(message)s"))

logger = logging.getLogger("rag_app")
logger.setLevel(logging.INFO)
logger.addHandler(_handler)
logger.propagate = False


def _emit(level: str, event: str, **kwargs):
    record = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "event": event,
        **kwargs,
    }
    logger.info(json.dumps(record))


def log_query(user_id: str, judge_score: float, cache_hit: bool,
              tokens_in: int, tokens_out: int, latency_ms: int,
              recommendation: str = "proceed"):
    _emit(
        "INFO", "query_processed",
        user_id=user_id,
        judge_score=judge_score,
        cache_hit=cache_hit,
        recommendation=recommendation,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency_ms,
    )


def log_upload(user_id: str, filename: str, chunks: int, latency_ms: int):
    _emit(
        "INFO", "document_uploaded",
        user_id=user_id,
        filename=filename,
        chunks_indexed=chunks,
        latency_ms=latency_ms,
    )


def log_auth(event: str, email: str, success: bool, detail: str = ""):
    _emit(
        "INFO" if success else "WARN", event,
        email=email,
        success=success,
        detail=detail,
    )


def log_error(event: str, error: str, **kwargs):
    _emit("ERROR", event, error=error, **kwargs)
