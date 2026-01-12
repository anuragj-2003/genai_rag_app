import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "interactions.db")

def migrate_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if is_pinned column exists
    c.execute("PRAGMA table_info(conversations)")
    columns = [column[1] for column in c.fetchall()]
    
    if "is_pinned" not in columns:
        print("Adding is_pinned column to conversations table...")
        c.execute("ALTER TABLE conversations ADD COLUMN is_pinned INTEGER DEFAULT 0")
        conn.commit()
    else:
        print("is_pinned column already exists.")
        
    conn.close()

if __name__ == "__main__":
    migrate_db()
