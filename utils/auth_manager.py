import sqlite3
import bcrypt
import os
import streamlit as st
from datetime import datetime

DB_PATH = "users.db"

def init_db():
    """Initialize the SQLite database for users."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT,
            google_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify a password against a hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def register_user(email, password=None, google_id=None):
    """Register a new user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Check if user exists
        c.execute("SELECT email FROM users WHERE email = ?", (email,))
        if c.fetchone():
            return False, "User already exists"
        
        hashed_pw = hash_password(password) if password else None
        
        c.execute(
            "INSERT INTO users (email, password, google_id) VALUES (?, ?, ?)",
            (email, hashed_pw, google_id)
        )
        conn.commit()
        return True, "User registered successfully"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def login_user(email, password):
    """Authenticate a user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT password FROM users WHERE email = ?", (email,))
    result = c.fetchone()
    conn.close()
    
    if result and result[0]:
        if verify_password(password, result[0]):
            return True
    return False

def has_password(email):
    """Checks if the user has a password set."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE email = ?", (email,))
    result = c.fetchone()
    conn.close()
    return result is not None and result[0] is not None

def user_exists(email):
    """Checks if a user already exists."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT email FROM users WHERE email = ?", (email,))
    result = c.fetchone()
    conn.close()
    return result is not None

def update_password(email, new_password):
    """Updates the user's password."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    hashed_pw = hash_password(new_password)
    try:
        c.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_pw, email))
        conn.commit()
        return True, "Password updated successfully"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def login_google_user(email, google_id):
    """Authenticate or register a Google user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT google_id FROM users WHERE email = ?", (email,))
    result = c.fetchone()
    
    if result:
        # User exists, update Google ID if missing
        if not result[0]:
            c.execute("UPDATE users SET google_id = ? WHERE email = ?", (google_id, email))
            conn.commit()
        conn.close()
        return True
    else:
        # Register new Google user
        conn.close()
        success, _ = register_user(email, google_id=google_id)
        return success

def delete_user(email):
    """Delete a user account."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE email = ?", (email,))
    conn.commit()
    conn.close()

def logout_user():
    """Clear session state for logout."""
    if "user_email" in st.session_state:
        del st.session_state["user_email"]
    if "authenticated" in st.session_state:
        del st.session_state["authenticated"]
    if "auth_mode" in st.session_state:
        del st.session_state["auth_mode"]
    st.rerun()
