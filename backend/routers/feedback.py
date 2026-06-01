"""
routers/feedback.py — Interaction feedback (/api/v1/feedback/)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from routers.auth import get_current_user, UserOut
from utils.app_db import get_db

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    interaction_id: int
    rating: int  # 1 = thumbs up, -1 = thumbs down
    comment: Optional[str] = None


@router.post("/")
async def submit_feedback(
    data: FeedbackRequest,
    current_user: UserOut = Depends(get_current_user)
):
    if data.rating not in (1, -1):
        raise HTTPException(status_code=400, detail="Rating must be 1 or -1.")

    conn = get_db()
    # Verify the interaction belongs to this user
    row = conn.execute(
        "SELECT user_id FROM interactions WHERE id=?", (data.interaction_id,)
    ).fetchone()

    if not row or row["user_id"] != current_user.id:
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized.")

    conn.execute(
        "UPDATE interactions SET judge_score=? WHERE id=?",
        (1.0 if data.rating == 1 else 0.0, data.interaction_id)
    )
    conn.commit()
    conn.close()

    return {"message": "Feedback recorded."}
