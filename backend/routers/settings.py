"""
routers/settings.py — User settings (/api/v1/settings/*)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from routers.auth import get_current_user, UserOut
from utils.security import hash_password, verify_password
from utils.app_db import get_db, get_user_by_id, delete_user_documents
from utils import chroma_manager

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None


@router.put("/password")
async def change_password(
    data: PasswordChange,
    current_user: UserOut = Depends(get_current_user)
):
    if current_user.is_guest:
        raise HTTPException(status_code=403, detail="Guests cannot change passwords.")

    user = get_user_by_id(current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    pw_hash = user["password_hash"]
    if isinstance(pw_hash, str):
        pw_hash = pw_hash.encode()

    if not verify_password(data.current_password, pw_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password.")

    new_hash = hash_password(data.new_password)
    conn = get_db()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, current_user.id))
    conn.commit()
    conn.close()

    return {"message": "Password updated successfully."}


@router.put("/profile")
async def update_profile(
    data: ProfileUpdate,
    current_user: UserOut = Depends(get_current_user)
):
    if current_user.is_guest:
        raise HTTPException(status_code=403, detail="Guests cannot update profiles.")

    if data.full_name is not None:
        conn = get_db()
        conn.execute("UPDATE users SET full_name=? WHERE id=?", (data.full_name, current_user.id))
        conn.commit()
        conn.close()

    return {"message": "Profile updated."}


@router.delete("/memory")
async def clear_conversations(current_user: UserOut = Depends(get_current_user)):
    """Delete all conversations and interactions for the current user."""
    conn = get_db()
    # Get conversation IDs
    rows = conn.execute(
        "SELECT id FROM conversations WHERE user_id=?", (current_user.id,)
    ).fetchall()
    for row in rows:
        conn.execute("DELETE FROM interactions WHERE conversation_id=?", (row["id"],))
    conn.execute("DELETE FROM conversations WHERE user_id=?", (current_user.id,))
    conn.commit()
    conn.close()
    return {"message": "All conversations cleared."}


@router.delete("/documents/all")
async def clear_all_documents(current_user: UserOut = Depends(get_current_user)):
    """Delete all uploaded documents and their vectors."""
    if current_user.is_guest:
        raise HTTPException(status_code=403, detail="Guests cannot delete documents.")

    chroma_manager.delete_user_vectors(current_user.id)
    delete_user_documents(current_user.id)
    return {"message": "All documents and vectors deleted."}
