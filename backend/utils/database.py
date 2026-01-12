import sqlite3
import json
import os
import uuid
from datetime import datetime

DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "interactions.db"))

def setup_database():
    """Create the database and tables, with all necessary columns for persistence."""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Interactions Table
    cursor.execute("""
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
    
    # Conversations Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Check if conversation_id column exists in interactions (migration for existing DB)
    cursor.execute("PRAGMA table_info(interactions)")
    columns = [info[1] for info in cursor.fetchall()]
    if "conversation_id" not in columns:
        cursor.execute("ALTER TABLE interactions ADD COLUMN conversation_id TEXT")
        
    # Check if user_id column exists in conversations (migration for existing DB)
    cursor.execute("PRAGMA table_info(conversations)")
    columns = [info[1] for info in cursor.fetchall()]
    if "user_id" not in columns:
        cursor.execute("ALTER TABLE conversations ADD COLUMN user_id TEXT")
        
    conn.commit()
    conn.close()

def create_conversation(title: str, user_id: str):
    """Creates a new conversation and returns its ID."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    conv_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO conversations (id, title, user_id) VALUES (?, ?, ?)",
        (conv_id, title, user_id)
    )
    conn.commit()
    conn.close()
    return conv_id

def get_conversations(user_id: str, limit: int = 50):
    """Retrieves recent conversations for a specific user."""
    if not os.path.exists(DB_FILE): return []
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_conversation(conversation_id: str):
    """Deletes a conversation and its interactions."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    cursor.execute("DELETE FROM interactions WHERE conversation_id = ?", (conversation_id,))
    conn.commit()
    conn.close()

def delete_all_user_conversations(user_id: str):
    """Deletes ALL conversations for a specific user."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Get all conversation IDs for this user first (to delete interactions)
    cursor.execute("SELECT id FROM conversations WHERE user_id = ?", (user_id,))
    conv_ids = [row[0] for row in cursor.fetchall()]
    
    if conv_ids:
        # Delete conversations
        cursor.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
        # Delete interactions (batch delete)
        placeholders = ','.join(['?'] * len(conv_ids))
        cursor.execute(f"DELETE FROM interactions WHERE conversation_id IN ({placeholders})", conv_ids)
        
    conn.commit()
    conn.close()

def get_dashboard_stats(user_id: str):
    """Aggregates dashboard statistics for a specific user."""
    if not os.path.exists(DB_FILE): return {}
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    stats = {
        "total_conversations": 0,
        "total_interactions": 0,
        "activity_by_date": [],
        "source_distribution": []
    }
    
    # 1. Total Conversations
    cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?", (user_id,))
    stats["total_conversations"] = cursor.fetchone()[0]
    
    # 2. Total Interactions (Joined)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM interactions i
        JOIN conversations c ON i.conversation_id = c.id
        WHERE c.user_id = ?
    """, (user_id,))
    stats["total_interactions"] = cursor.fetchone()[0]
    
    # 3. Activity by Date (Last 7 days)
    cursor.execute("""
        SELECT DATE(i.timestamp) as day, COUNT(*) as count
        FROM interactions i
        JOIN conversations c ON i.conversation_id = c.id
        WHERE c.user_id = ?
        GROUP BY day
        ORDER BY day DESC
        LIMIT 7
    """, (user_id,))
    stats["activity_by_date"] = [dict(row) for row in cursor.fetchall()]
    
    # 4. Source Distribution (Direct LLM vs Web Search etc)
    cursor.execute("""
        SELECT i.source, COUNT(*) as count
        FROM interactions i
        JOIN conversations c ON i.conversation_id = c.id
        WHERE c.user_id = ?
        GROUP BY i.source
    """, (user_id,))
    stats["source_distribution"] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return stats

def rename_conversation(conversation_id: str, new_title: str):
    """Renames a conversation."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE conversations SET title = ? WHERE id = ?", (new_title, conversation_id))
    conn.commit()
    conn.close()

def log_interaction(user_prompt: str, web_context: str, llm_response: str, source: str, sources: list, conversation_id: str = None):
    """Logs a complete user interaction to the database and returns its ID."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    sources_json = json.dumps(sources)
    cursor.execute(
        "INSERT INTO interactions (user_prompt, web_context, llm_response, source, sources, conversation_id) VALUES (?, ?, ?, ?, ?, ?)",
        (user_prompt, web_context, llm_response, source, sources_json, conversation_id)
    )
    interaction_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return interaction_id

def update_interaction_rating(interaction_id: int, rating: int):
    """Updates the rating for a specific interaction."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE interactions SET rating = ? WHERE id = ?", (rating, interaction_id))
    conn.commit()
    conn.close()

def get_rated_interactions(user_id: str):
    """Retrieves all rated interactions (memories) for a user (positive and negative)."""
    if not os.path.exists(DB_FILE): return []
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.id, i.user_prompt, i.llm_response, i.timestamp, i.rating
        FROM interactions i
        JOIN conversations c ON i.conversation_id = c.id
        WHERE c.user_id = ? AND i.rating != 0
        ORDER BY i.timestamp DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_individual_interaction(interaction_id: int):
    """Deletes a specific interaction (memory)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM interactions WHERE id = ?", (interaction_id,))
    conn.commit()
    conn.close()

def find_similar_interaction(query: str):
    """Finds a similar, highly-rated past interaction (Positive)."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT user_prompt, llm_response 
        FROM interactions 
        WHERE user_prompt LIKE ? AND rating >= 1
        ORDER BY rating DESC, timestamp DESC
        LIMIT 1
        """,
        (f'%{query.strip()}%',)
    )
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"past_question": result["user_prompt"], "past_answer": result["llm_response"]}
    return None

def find_similar_negative_interaction(query: str):
    """Finds a similar, negatively-rated past interaction (Avoidance)."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT user_prompt, llm_response 
        FROM interactions 
        WHERE user_prompt LIKE ? AND rating <= -1
        ORDER BY rating ASC, timestamp DESC
        LIMIT 1
        """,
        (f'%{query.strip()}%',)
    )
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"past_question": result["user_prompt"], "past_answer": result["llm_response"]}
    return None

def load_chat_history_from_db(conversation_id: str = None, limit: int = 50):
    """Loads the last N interactions for a specific conversation."""
    if not os.path.exists(DB_FILE): return []
    
    # If no conversation ID, return empty (clean state for new chat)
    if not conversation_id:
        return []

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM interactions WHERE conversation_id = ? ORDER BY timestamp DESC LIMIT ?", (conversation_id, limit))

    rows = cursor.fetchall()
    conn.close()
    messages = []
    for row in reversed(rows):
        messages.append({"role": "user", "content": row["user_prompt"]})
        messages.append({
            "role": "assistant",
            "content": row["llm_response"],
            "source": row["source"],
            "sources": json.loads(row["sources"]) if row["sources"] else [],
            "interaction_id": row["id"]
        })
    return messages


def load_query_history_from_db(limit: int = 10):
    """Loads the last N user prompts from the DB for the dashboard."""
    if not os.path.exists(DB_FILE): return []
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_prompt FROM interactions ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    # We create a history list compatible with the dashboard dataframe
    history = [{"Query": row[0], "Type": "RAG Agent"} for row in rows]
    return history

