import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
USERS_DB = os.path.join(DB_DIR, "users.db")
INTERACTIONS_DB = os.path.join(DB_DIR, "interactions.db")

def migrate():
    # Users DB
    print(f"Migrating Users DB at {USERS_DB}")
    conn = sqlite3.connect(USERS_DB)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0")
        print("Added is_verified to users")
    except Exception as e:
        print(f"Skipping users update: {e}")
        
    try:
        c.execute("""
            CREATE TABLE IF NOT EXISTS pending_users (
                email TEXT PRIMARY KEY,
                password TEXT,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Created pending_users table")
    except Exception as e:
        print(f"Skipping pending_users creation: {e}")

    conn.commit()
    conn.close()
    
    # Interactions DB
    print(f"Migrating Interactions DB at {INTERACTIONS_DB}")
    conn = sqlite3.connect(INTERACTIONS_DB)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE interactions ADD COLUMN feedback TEXT")
        print("Added feedback to interactions")
    except Exception as e:
        print(f"Skipping interactions update: {e}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
