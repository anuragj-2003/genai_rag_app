"""
routers/auth.py — Authentication router (/api/v1/auth/*)

Security hardening applied:
- OTP: bcrypt-hashed, 10-min TTL, max 3 attempts, 60s cooldown per email
- Guest tokens: signed JWT (httpOnly cookie), SQLite usage tracking, not IP-based
- JWT: 15-min access + 7-day refresh tokens with jti revocation
- All SQL parameterized, no f-string queries
- Generic error messages in production
"""

import os
import uuid
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Response, Request, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated, Optional
from pydantic import BaseModel, EmailStr

from utils.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, hash_otp, verify_otp, sanitize_query
)
from utils.app_db import (
    get_user_by_email, get_user_by_id, create_user, delete_user as db_delete_user,
    upsert_pending_user, get_pending_user, delete_pending_user,
    upsert_otp, get_otp_record, increment_otp_attempts, delete_otp,
    revoke_token, is_token_revoked,
    get_guest_uses, increment_guest_uses,
    delete_user_documents
)
from utils.email_service import generate_otp, send_otp_email
from utils import chroma_manager
from utils.logging_utils import log_auth

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

GUEST_LIMIT = 5


# ── Pydantic models ───────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str = ""


class OTPVerify(BaseModel):
    email: str
    otp: str
    new_password: Optional[str] = None


class OTPRequest(BaseModel):
    email: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    is_verified: bool
    is_guest: bool = False
    usage_count: int = 0
    usage_limit: int = 0
    limit_exceeded: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None


# ── OTP rate limiting (in-memory per email, resets on restart) ────────────────
_otp_cooldowns: dict[str, datetime] = {}


def _check_otp_cooldown(email: str):
    """Raise 429 if OTP was issued for this email within the last 60 seconds."""
    if email in _otp_cooldowns:
        elapsed = (datetime.utcnow() - _otp_cooldowns[email]).total_seconds()
        if elapsed < 60:
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {int(60 - elapsed)}s before requesting another OTP."
            )
    _otp_cooldowns[email] = datetime.utcnow()


# ── Dependency: get current user ──────────────────────────────────────────────

async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    guest_token: Optional[str] = Cookie(default=None),
) -> UserOut:
    """
    Resolve the current authenticated user.
    Tries Bearer token first, then guest_token cookie.
    Checks revocation table on every request.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # --- Try Bearer token ---
    if token:
        payload = decode_token(token)
        if payload:
            if payload.get("role") == "guest":
                sub = payload.get("sub", "")
                uses = get_guest_uses(sub)
                return UserOut(
                    id=sub,
                    email=sub,
                    full_name="Guest",
                    is_verified=False,
                    is_guest=True,
                    usage_count=uses,
                    usage_limit=GUEST_LIMIT,
                    limit_exceeded=uses >= GUEST_LIMIT,
                )
            elif payload.get("type") == "access":
                jti = payload.get("jti")
                if jti and is_token_revoked(jti):
                    pass # Fallthrough to raise
                else:
                    user_id = payload.get("sub")
                    if user_id:
                        user = get_user_by_id(user_id)
                        if user:
                            return UserOut(
                                id=user["id"],
                                email=user["email"],
                                full_name=user.get("full_name") or "",
                                is_verified=bool(user.get("is_verified", 0)),
                                is_guest=False,
                            )

    # --- Try guest cookie ---
    if guest_token:
        payload = decode_token(guest_token)
        if payload and payload.get("role") == "guest":
            sub = payload.get("sub", "")
            uses = get_guest_uses(sub)
            return UserOut(
                id=sub,
                email=sub,
                full_name="Guest",
                is_verified=False,
                is_guest=True,
                usage_count=uses,
                usage_limit=GUEST_LIMIT,
                limit_exceeded=uses >= GUEST_LIMIT,
            )

    raise credentials_exception


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/signup")
async def signup(user: UserCreate):
    # Check if already verified
    existing = get_user_by_email(user.email)
    if existing and existing.get("is_verified"):
        raise HTTPException(status_code=400, detail="Email already registered.")

    pw_hash = hash_password(user.password)
    upsert_pending_user(user.email, pw_hash, user.full_name)

    _check_otp_cooldown(user.email)
    otp = generate_otp()
    otp_hash = hash_otp(otp)
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    upsert_otp(user.email, otp_hash, "signup", expires_at)

    try:
        send_otp_email(user.email, otp, purpose="verification")
    except Exception:
        pass  # Don't leak SMTP errors

    log_auth("signup_initiated", user.email, success=True)
    return {"message": "OTP sent to your email. Please verify within 10 minutes."}


@router.post("/verify-otp")
async def verify_otp_endpoint(request: OTPVerify):
    record = get_otp_record(request.email)
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

    # Check expiry
    try:
        expires_at = datetime.fromisoformat(record["expires_at"])
        if datetime.utcnow() > expires_at:
            delete_otp(request.email)
            raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
    except (ValueError, TypeError):
        pass

    # Check max attempts
    if record["attempts"] >= 3:
        delete_otp(request.email)
        raise HTTPException(status_code=400, detail="Too many failed attempts. Please request a new OTP.")

    otp_hash = record["otp_hash"]
    if isinstance(otp_hash, str):
        otp_hash = otp_hash.encode()

    if not verify_otp(request.otp, otp_hash):
        increment_otp_attempts(request.email)
        raise HTTPException(status_code=400, detail="Invalid OTP.")

    otp_type = record.get("otp_type", "signup")

    if otp_type == "signup":
        pending = get_pending_user(request.email)
        if not pending:
            raise HTTPException(status_code=400, detail="No pending registration found.")

        user_id = str(uuid.uuid4())
        create_user(
            user_id=user_id,
            email=request.email,
            password_hash=pending["password_hash"] if isinstance(pending["password_hash"], bytes)
                          else pending["password_hash"].encode(),
            full_name=pending.get("full_name") or "",
        )
        delete_pending_user(request.email)
        msg = "Account verified successfully. You can now log in."

    elif otp_type == "reset":
        if not request.new_password:
            raise HTTPException(status_code=400, detail="New password required.")
        user = get_user_by_email(request.email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        pw_hash = hash_password(request.new_password)
        from utils.app_db import get_db
        conn = get_db()
        conn.execute("UPDATE users SET password_hash=? WHERE email=?", (pw_hash, request.email))
        conn.commit()
        conn.close()
        msg = "Password reset successfully."
    else:
        msg = "OTP verified."

    delete_otp(request.email)
    log_auth("otp_verified", request.email, success=True, detail=otp_type)
    return {"message": msg}


@router.post("/forgot-password")
async def forgot_password(request: OTPRequest):
    user = get_user_by_email(request.email)
    if not user:
        # Don't reveal if user exists
        return {"message": "If that email is registered, an OTP has been sent."}

    _check_otp_cooldown(request.email)
    otp = generate_otp()
    otp_hash = hash_otp(otp)
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    upsert_otp(request.email, otp_hash, "reset", expires_at)

    try:
        send_otp_email(request.email, otp, purpose="reset")
    except Exception:
        pass

    return {"message": "If that email is registered, an OTP has been sent."}


@router.post("/token", response_model=TokenResponse)
async def login(response: Response, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = get_user_by_email(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    pw_hash = user["password_hash"]
    if isinstance(pw_hash, str):
        pw_hash = pw_hash.encode()

    if not verify_password(form_data.password, pw_hash):
        log_auth("login_failed", form_data.username, success=False, detail="bad_password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user["id"]})
    raw_refresh, refresh_hash = create_refresh_token(user["id"])

    # Store refresh token hash in DB
    from utils.app_db import get_db
    from utils.security import REFRESH_TOKEN_EXPIRE_DAYS
    conn = get_db()
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    conn.execute(
        "INSERT OR REPLACE INTO refresh_tokens (token_hash,user_id,expires_at) VALUES (?,?,?)",
        (refresh_hash, user["id"], expires_at.isoformat())
    )
    conn.commit()
    conn.close()

    # Set refresh token as httpOnly cookie
    is_prod = os.getenv("APP_ENV", "development") == "production"
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,
        secure=is_prod,
        samesite="strict",
        max_age=60 * 60 * 24 * 7,  # 7 days in seconds
    )

    log_auth("login_success", form_data.username, success=True)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(refresh_token: Optional[str] = Cookie(default=None)):
    """Issue a new access token using the refresh token cookie."""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token provided.")

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

    import hashlib
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

    from utils.app_db import get_db
    conn = get_db()
    row = conn.execute(
        "SELECT user_id, expires_at FROM refresh_tokens WHERE token_hash=?", (token_hash,)
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Refresh token revoked or not found.")

    try:
        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.utcnow() > expires_at:
            raise HTTPException(status_code=401, detail="Refresh token expired.")
    except (ValueError, TypeError):
        pass

    new_access = create_access_token(data={"sub": row["user_id"]})
    return TokenResponse(access_token=new_access)


@router.post("/logout")
async def logout(
    response: Response,
    token: Optional[str] = Depends(oauth2_scheme),
    refresh_token: Optional[str] = Cookie(default=None),
):
    """Revoke access + refresh tokens."""
    if token:
        payload = decode_token(token)
        if payload and payload.get("jti"):
            revoke_token(payload["jti"])

    if refresh_token:
        import hashlib
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        from utils.app_db import get_db
        conn = get_db()
        conn.execute("DELETE FROM refresh_tokens WHERE token_hash=?", (token_hash,))
        conn.commit()
        conn.close()

    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserOut)
async def get_me(current_user: UserOut = Depends(get_current_user)):
    return current_user


@router.post("/guest")
async def create_guest_session(response: Response):
    """Issue a signed guest JWT as httpOnly cookie."""
    from utils.security import JWT_SECRET, ALGORITHM
    from jose import jwt as jose_jwt

    sub = f"guest:{uuid.uuid4()}"
    is_prod = os.getenv("APP_ENV", "development") == "production"

    payload = {
        "sub": sub,
        "role": "guest",
        "exp": datetime.utcnow() + timedelta(days=30),
    }
    token = jose_jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

    response.set_cookie(
        key="guest_token",
        value=token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return {"message": "Guest session created.", "sub": sub, "access_token": token}


@router.delete("/account")
async def delete_account(current_user: UserOut = Depends(get_current_user)):
    """Delete account + all user data (vectors, documents, conversations)."""
    if current_user.is_guest:
        raise HTTPException(status_code=403, detail="Guest accounts cannot be deleted this way.")

    user_id = current_user.id

    # Purge ChromaDB vectors
    chroma_manager.delete_user_vectors(user_id)

    # Purge DB data
    delete_user_documents(user_id)
    db_delete_user(user_id)

    log_auth("account_deleted", current_user.email, success=True)
    return {"message": "Account and all data deleted."}
