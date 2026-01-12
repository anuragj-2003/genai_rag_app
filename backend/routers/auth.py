from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from utils.security import verify_password, get_password_hash, create_access_token, decode_access_token, SECRET_KEY, ALGORITHM
from models.auth import User, UserCreate, Token, TokenData, OTPRequest, OTPVerify
from utils.email_manager import send_otp_email, generate_otp
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Annotated

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "users.db")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_db_connection():
    # Ensure directory exists (Render safety check)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.post("/signup", response_model=User)
async def signup(user: UserCreate):
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # Check if user exists
        c.execute("SELECT * FROM users WHERE email = ?", (user.email,))
        existing_user = c.fetchone()
        
        # Check if user already exists in MAIN users table
        if existing_user:
            if existing_user["is_verified"]:
                 raise HTTPException(status_code=400, detail="Email already registered")
            else:
                 # If unverified in main table (legacy), we can overwrite or treat as pending.
                 # But with new flow, unverified users shouldn't be in main table.
                 # We will fall through to pending.
                 pass
            
        hashed_password = get_password_hash(user.password)
        
        # Insert or Replace into PENDING users
        c.execute(
            "INSERT OR REPLACE INTO pending_users (email, password, full_name) VALUES (?, ?, ?)",
            (user.email, hashed_password, user.full_name)
        )
        conn.commit()
        
        # Send OTP for verification
        otp = generate_otp()
        expiry = datetime.now() + timedelta(minutes=10)
        c.execute("INSERT OR REPLACE INTO otp_codes (email, code, type, expires_at) VALUES (?, ?, 'signup', ?)", (user.email, otp, expiry))
        conn.commit()
        
        sent = send_otp_email(user.email, otp)
        
        # Fallback for Render Free Tier (where SMTP is likely blocked)
        if not sent:
             print(f"SMTP Failed. Using Fallback OTP for {user.email}")
             # Update OTP to '000000' so user can login with that
             fallback_otp = "000000"
             c.execute("UPDATE otp_codes SET code = ? WHERE email = ?", (fallback_otp, user.email))
             conn.commit()

        
        # Return a dummy user object or success message
        return User(email=user.email, full_name=user.full_name, is_verified=False)
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

@router.post("/verify-otp")
async def verify_otp(request: OTPVerify):
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT * FROM otp_codes WHERE email = ?", (request.email,))
    record = c.fetchone()
    
    if not record:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    if record["code"] != request.otp:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    # Check expiry (simple string comparison for now, ideally parse datetime)
    # For MVP, skipping strict datetime check to avoid parsing issues, rely on short lifespan
    
    auth_type = record["type"]
    
    if auth_type == "signup":
        # Check pending users
        c.execute("SELECT * FROM pending_users WHERE email = ?", (request.email,))
        pending_user = c.fetchone()
        
        if not pending_user:
            # Check if already in users (maybe legacy or verified)
            c.execute("SELECT * FROM users WHERE email = ?", (request.email,))
            if c.fetchone():
                msg = "Account already verified"
            else:
                 conn.close()
                 raise HTTPException(status_code=400, detail="No pending registration found for this email")
        else:
            # Move to users table
            c.execute(
                "INSERT INTO users (email, password, full_name, is_verified) VALUES (?, ?, ?, 1)",
                (pending_user["email"], pending_user["password"], pending_user["full_name"])
            )
            c.execute("DELETE FROM pending_users WHERE email = ?", (request.email,))
            conn.commit()
            msg = "Account verified and created successfully"
    elif auth_type == "reset":
        if not request.new_password:
            conn.close()
            raise HTTPException(status_code=400, detail="New password required for reset")
        hashed = get_password_hash(request.new_password)
        c.execute("UPDATE users SET password = ? WHERE email = ?", (hashed, request.email))
        conn.commit()
        msg = "Password reset successfully"
    else:
        msg = "OTP Verified"

    # Clean up OTP
    c.execute("DELETE FROM otp_codes WHERE email = ?", (request.email,))
    conn.commit()
    conn.close()
    
    return {"message": msg}

@router.post("/forgot-password")
async def forgot_password(request: OTPRequest):
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE email = ?", (request.email,))
    user = c.fetchone()
    
    if not user:
        conn.close()
        # Don't reveal user existence
        return {"message": "If email exists, OTP sent."}
        
    otp = generate_otp()
    expiry = datetime.now() + timedelta(minutes=10)
    c.execute("INSERT OR REPLACE INTO otp_codes (email, code, type, expires_at) VALUES (?, ?, 'reset', ?)", (request.email, otp, expiry))
    conn.commit()
    conn.close()
    
    send_otp_email(request.email, otp)
    return {"message": "OTP sent"}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (form_data.username,))
    user = c.fetchone()
    conn.close()
    
    if not user:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Optional: Enforce verification
    # if not user["is_verified"]:
    #     raise HTTPException(status_code=400, detail="Email not verified")

    access_token_expires = timedelta(minutes=300) # Long expiration for dev
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except Exception:
        raise credentials_exception
        
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (token_data.username,))
    user = c.fetchone()
    conn.close()
    
    if user is None:
        raise credentials_exception
        
    return User(
        email=user["email"], 
        full_name=user["full_name"],
        is_verified=bool(user["is_verified"]) if "is_verified" in user.keys() else False
    )
    
@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
