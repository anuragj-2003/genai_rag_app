"""
app_db.py — Single unified SQLite database (app.db) connection factory and CRUD helpers.
All 10 tables defined in Layer 5 are created here on first run.
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "app.db"))


def get_db() -> sqlite3.Connection:
    """Return a thread-local SQLite connection with row_factory."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist. Safe to call on every startup."""
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash BLOB,
            full_name TEXT,
            google_id TEXT,
            is_verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS pending_users (
            email TEXT PRIMARY KEY,
            password_hash BLOB,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sessions (
            jti TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            expires_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS revoked_tokens (
            jti TEXT PRIMARY KEY,
            revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS refresh_tokens (
            token_hash TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            expires_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS guest_usage (
            sub TEXT PRIMARY KEY,
            uses INTEGER DEFAULT 0,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS otp_store (
            email TEXT PRIMARY KEY,
            otp_hash BLOB NOT NULL,
            otp_type TEXT DEFAULT 'signup',
            attempts INTEGER DEFAULT 0,
            expires_at TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            markdown_content TEXT,
            chunks_indexed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            is_pinned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            conversation_id TEXT,
            query TEXT NOT NULL,
            response TEXT,
            chunks TEXT,
            judge_score REAL,
            recommendation TEXT,
            tokens_in INTEGER,
            tokens_out INTEGER,
            latency_ms INTEGER,
            cache_hit INTEGER DEFAULT 0,
            source TEXT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS semantic_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text TEXT NOT NULL,
            query_emb BLOB NOT NULL,
            response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS rate_limits (
            key TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0,
            window_reset_at TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
    print(f"[DB] Initialized {DB_PATH}")


# ── User helpers ────────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(user_id: str, email: str, password_hash: bytes, full_name: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO users (id,email,password_hash,full_name,is_verified) VALUES (?,?,?,?,1)",
        (user_id, email, password_hash, full_name)
    )
    conn.commit()
    conn.close()


def delete_user(user_id: str):
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


# ── Pending users ───────────────────────────────────────────────────────────

def upsert_pending_user(email: str, password_hash: bytes, full_name: str):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO pending_users (email,password_hash,full_name) VALUES (?,?,?)",
        (email, password_hash, full_name)
    )
    conn.commit()
    conn.close()


def get_pending_user(email: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM pending_users WHERE email=?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_pending_user(email: str):
    conn = get_db()
    conn.execute("DELETE FROM pending_users WHERE email=?", (email,))
    conn.commit()
    conn.close()


# ── OTP helpers ─────────────────────────────────────────────────────────────

def upsert_otp(email: str, otp_hash: bytes, otp_type: str, expires_at: datetime):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO otp_store (email,otp_hash,otp_type,attempts,expires_at) VALUES (?,?,?,0,?)",
        (email, otp_hash, otp_type, expires_at.isoformat())
    )
    conn.commit()
    conn.close()


def get_otp_record(email: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM otp_store WHERE email=?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def increment_otp_attempts(email: str):
    conn = get_db()
    conn.execute("UPDATE otp_store SET attempts=attempts+1 WHERE email=?", (email,))
    conn.commit()
    conn.close()


def delete_otp(email: str):
    conn = get_db()
    conn.execute("DELETE FROM otp_store WHERE email=?", (email,))
    conn.commit()
    conn.close()


# ── Token revocation ────────────────────────────────────────────────────────

def revoke_token(jti: str):
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO revoked_tokens (jti) VALUES (?)", (jti,))
    conn.commit()
    conn.close()


def is_token_revoked(jti: str) -> bool:
    conn = get_db()
    row = conn.execute("SELECT 1 FROM revoked_tokens WHERE jti=?", (jti,)).fetchone()
    conn.close()
    return row is not None


# ── Guest usage ─────────────────────────────────────────────────────────────

def get_guest_uses(sub: str) -> int:
    conn = get_db()
    row = conn.execute("SELECT uses FROM guest_usage WHERE sub=?", (sub,)).fetchone()
    conn.close()
    return row["uses"] if row else 0


def increment_guest_uses(sub: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO guest_usage (sub,uses,last_seen) VALUES (?,1,datetime('now')) "
        "ON CONFLICT(sub) DO UPDATE SET uses=uses+1, last_seen=datetime('now')",
        (sub,)
    )
    conn.commit()
    conn.close()


# ── Documents ───────────────────────────────────────────────────────────────

def insert_document(doc_id: str, user_id: str, filename: str, markdown_content: str, chunks_indexed: int):
    conn = get_db()
    conn.execute(
        "INSERT INTO documents (id,user_id,filename,markdown_content,chunks_indexed) VALUES (?,?,?,?,?)",
        (doc_id, user_id, filename, markdown_content, chunks_indexed)
    )
    conn.commit()
    conn.close()


def get_user_documents(user_id: str) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT id,filename,chunks_indexed,created_at FROM documents WHERE user_id=? AND deleted_at IS NULL ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def soft_delete_document(doc_id: str, user_id: str):
    conn = get_db()
    conn.execute(
        "UPDATE documents SET deleted_at=datetime('now') WHERE id=? AND user_id=?",
        (doc_id, user_id)
    )
    conn.commit()
    conn.close()


def delete_user_documents(user_id: str):
    conn = get_db()
    conn.execute("DELETE FROM documents WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


# ── Conversations ───────────────────────────────────────────────────────────

def create_conversation(conv_id: str, user_id: str, title: str) -> str:
    conn = get_db()
    conn.execute(
        "INSERT INTO conversations (id,user_id,title) VALUES (?,?,?)",
        (conv_id, user_id, title)
    )
    conn.commit()
    conn.close()
    return conv_id


def get_conversations(user_id: str) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM conversations WHERE user_id=? ORDER BY is_pinned DESC, created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_conversation(conv_id: str, user_id: str, title: str = None, is_pinned: bool = None):
    conn = get_db()
    if title is not None:
        conn.execute("UPDATE conversations SET title=? WHERE id=? AND user_id=?", (title, conv_id, user_id))
    if is_pinned is not None:
        conn.execute("UPDATE conversations SET is_pinned=? WHERE id=? AND user_id=?", (int(is_pinned), conv_id, user_id))
    conn.commit()
    conn.close()


def delete_conversation(conv_id: str, user_id: str):
    conn = get_db()
    conn.execute("DELETE FROM interactions WHERE conversation_id=?", (conv_id,))
    conn.execute("DELETE FROM conversations WHERE id=? AND user_id=?", (conv_id, user_id))
    conn.commit()
    conn.close()


def get_conversation_owner(conv_id: str) -> str | None:
    conn = get_db()
    row = conn.execute("SELECT user_id FROM conversations WHERE id=?", (conv_id,)).fetchone()
    conn.close()
    return row["user_id"] if row else None


# ── Interactions ────────────────────────────────────────────────────────────

def log_interaction(user_id: str, conversation_id: str, query: str, response: str,
                    chunks: list, judge_score: float, recommendation: str,
                    tokens_in: int, tokens_out: int, latency_ms: int,
                    cache_hit: bool, source: str):
    conn = get_db()
    conn.execute(
        """INSERT INTO interactions
           (user_id,conversation_id,query,response,chunks,judge_score,recommendation,
            tokens_in,tokens_out,latency_ms,cache_hit,source)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (user_id, conversation_id, query, response,
         json.dumps(chunks), judge_score, recommendation,
         tokens_in, tokens_out, latency_ms, int(cache_hit), source)
    )
    conn.commit()
    conn.close()


def get_conversation_messages(conv_id: str) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM interactions WHERE conversation_id=? ORDER BY ts ASC",
        (conv_id,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({"role": "user", "content": r["query"]})
        result.append({
            "role": "assistant",
            "content": r["response"],
            "judge_score": r["judge_score"],
            "cache_hit": bool(r["cache_hit"]),
            "source": r["source"],
        })
    return result


def get_recent_chat_turns(conv_id: str, limit: int = 6) -> list[dict]:
    """Return last N turns as [{role, content}] for LLM context window."""
    conn = get_db()
    rows = conn.execute(
        "SELECT query, response FROM interactions WHERE conversation_id=? ORDER BY ts DESC LIMIT ?",
        (conv_id, limit)
    ).fetchall()
    conn.close()
    messages = []
    for r in reversed(rows):
        messages.append({"role": "user", "content": r["query"]})
        messages.append({"role": "assistant", "content": r["response"]})
    return messages


# ── Semantic cache ──────────────────────────────────────────────────────────

def cache_get_all() -> list[dict]:
    """Return all non-expired cache entries (id, query_emb, response)."""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, query_emb, response FROM semantic_cache WHERE expires_at > datetime('now')"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def cache_insert(query_text: str, query_emb: bytes, response: str, ttl_days: int = 90):
    conn = get_db()
    conn.execute(
        "INSERT INTO semantic_cache (query_text,query_emb,response,expires_at) "
        "VALUES (?,?,?,datetime('now',?))",
        (query_text, query_emb, response, f"+{ttl_days} days")
    )
    conn.commit()
    conn.close()


def cache_purge_expired():
    conn = get_db()
    conn.execute("DELETE FROM semantic_cache WHERE expires_at <= datetime('now')")
    conn.commit()
    conn.close()


# ── Retention ───────────────────────────────────────────────────────────────

def purge_old_interactions(days: int = 90):
    conn = get_db()
    conn.execute("DELETE FROM interactions WHERE ts < date('now',?)", (f"-{days} days",))
    conn.commit()
    conn.close()
