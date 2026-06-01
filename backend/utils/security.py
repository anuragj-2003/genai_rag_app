"""
security.py — JWT creation/validation, password hashing, and prompt sanitization.
JWT_SECRET must be set via environment variable (never hardcoded).
Access tokens: 15-minute lifetime.
Refresh tokens: 7-day lifetime (stored hash in DB).
"""

import os
import re
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
import bcrypt
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ────────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET environment variable is not set! "
        "Run: python -c \"import secrets; print(secrets.token_hex(32))\" and add to .env"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> bytes:
    """Return bcrypt hash of password as bytes."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def verify_password(plain: str, hashed: bytes | str) -> bool:
    """Verify plain password against bcrypt hash."""
    if isinstance(hashed, str):
        hashed = hashed.encode("utf-8")
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed)
    except Exception:
        return False


# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token with jti claim for revocation support."""
    payload = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload.update({
        "exp": expire,
        "jti": str(uuid.uuid4()),  # unique token ID for revocation
        "type": "access",
    })
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """
    Create a signed refresh token.
    Returns (raw_token, token_hash) — store the hash in DB, send raw to client.
    """
    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    raw = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, token_hash


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT. Returns payload dict or None."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ── OTP bcrypt helpers ────────────────────────────────────────────────────────

def hash_otp(otp: str) -> bytes:
    return bcrypt.hashpw(otp.zfill(6).encode(), bcrypt.gensalt())


def verify_otp(plain_otp: str, hashed: bytes | str) -> bool:
    if isinstance(hashed, str):
        hashed = hashed.encode("utf-8")
    try:
        return bcrypt.checkpw(plain_otp.zfill(6).encode(), hashed)
    except Exception:
        return False


# ── Prompt sanitization ───────────────────────────────────────────────────────

# Characters that could be used for prompt injection / template injection
_INJECTION_PATTERN = re.compile(r"[{}\[\]<>\\]")


def sanitize_query(query: str, max_length: int = 2000) -> str:
    """
    Remove characters commonly used in prompt injection attacks.
    Truncate to max_length.
    Always use this before including user input in LLM messages.
    """
    cleaned = _INJECTION_PATTERN.sub("", query)
    return cleaned[:max_length].strip()
