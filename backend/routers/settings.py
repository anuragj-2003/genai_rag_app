from fastapi import APIRouter, Depends, HTTPException, status
from models.auth import User
from routers.auth import get_current_user, get_db_connection
from utils.security import get_password_hash, verify_password
from pydantic import BaseModel

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
)

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@router.put("/password")
async def change_password(data: PasswordChange, current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get current user with password
    c.execute("SELECT * FROM users WHERE email = ?", (current_user.email,))
    user_record = c.fetchone()
    
    if not user_record:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
        
    if not verify_password(data.current_password, user_record["password"]):
        conn.close()
        raise HTTPException(status_code=400, detail="Incorrect current password")
        
    new_hash = get_password_hash(data.new_password)
    c.execute("UPDATE users SET password = ? WHERE email = ?", (new_hash, current_user.email))
    conn.commit()
    conn.close()
    
    return {"message": "Password updated successfully"}

@router.delete("/account")
async def delete_account(current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # Delete user
        c.execute("DELETE FROM users WHERE email = ?", (current_user.email,))
        
        # Delete from interactions (We need to attach or access the interactions DB)
        # For simplicity in this structure, we assume separate DBs. 
        # We will connect to interactions.db explicitly here.
        import os
        import sqlite3
        INTERACTIONS_DB = os.path.join(os.path.dirname(__file__), "..", "data", "interactions.db")
        
        # We need to know which conversations belong to this user.
        # Ideally, we should have used the same DB or attached tables.
        # Let's clean up conversations by user ID (email)
        
        conn_int = sqlite3.connect(INTERACTIONS_DB)
        c_int = conn_int.cursor()
        
        # Get all conversation IDs for user
        c_int.execute("SELECT id FROM conversations WHERE user_id = ?", (current_user.email,))
        convs = c_int.fetchall()
        for conv in convs:
            c_int.execute("DELETE FROM interactions WHERE conversation_id = ?", (conv[0],))
        
        c_int.execute("DELETE FROM conversations WHERE user_id = ?", (current_user.email,))
        conn_int.commit()
        conn_int.close()
        
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    
    conn.close()
    return {"message": "Account deleted permanently"}

@router.delete("/memory")
async def clear_memory(current_user: User = Depends(get_current_user)):
    import sqlite3
    import os
    INTERACTIONS_DB = os.path.join(os.path.dirname(__file__), "..", "data", "interactions.db")
    
    try:
        conn = sqlite3.connect(INTERACTIONS_DB)
        c = conn.cursor()
        
        # Delete interactions for user's conversations
        c.execute("SELECT id FROM conversations WHERE user_id = ?", (current_user.email,))
        convs = c.fetchall()
        for conv in convs:
            c.execute("DELETE FROM interactions WHERE conversation_id = ?", (conv[0],))
        
        # Delete conversations themselves
        c.execute("DELETE FROM conversations WHERE user_id = ?", (current_user.email,))
        
        conn.commit()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear memory: {str(e)}")

    return {"message": "All conversations and memory cleared"}
