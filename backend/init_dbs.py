import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
USERS_DB = os.path.join(DB_DIR, "users.db")
INTERACTIONS_DB = os.path.join(DB_DIR, "interactions.db")

def init_dbs():
    os.makedirs(DB_DIR, exist_ok=True)
    
    # Init Users DB
    conn = sqlite3.connect(USERS_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT,
            google_id TEXT,
            full_name TEXT,
            is_verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add otp_codes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS otp_codes (
            email TEXT PRIMARY KEY,
            code TEXT,
            type TEXT, -- 'signup' or 'reset'
            expires_at DATETIME
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Initialized {USERS_DB}")
    
    # Init Pending Registration DB (for signup staging)
    conn = sqlite3.connect(USERS_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS pending_users (
            email TEXT PRIMARY KEY,
            password TEXT,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    # Init Interactions DB
    conn = sqlite3.connect(INTERACTIONS_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_prompt TEXT NOT NULL,
            web_context TEXT,
            llm_response TEXT,
            rating INTEGER DEFAULT 0,
            source TEXT,
            sources TEXT,
            conversation_id TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print(f"Initialized {INTERACTIONS_DB}")

if __name__ == "__main__":
    init_dbs()
