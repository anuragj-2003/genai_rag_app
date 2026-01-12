from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from routers.auth import get_current_user
from models.auth import User
from models.chat import ChatRequest, ChatResponse, ConversationUpdate
from utils.retriever_agent import get_retriever_decision, RetrievalStrategy
from state import vector_store
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import os
import sqlite3
import json
import uuid
from datetime import datetime

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

# Use absolute path for DB (same as auth.py)
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "interactions.db"))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_interaction_db(user_id, conversation_id, user_prompt, llm_response, source, sources):
    conn = get_db_connection()
    c = conn.cursor()
    sources_json = json.dumps(sources)
    c.execute(
        "INSERT INTO interactions (user_prompt, web_context, llm_response, source, sources, conversation_id, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_prompt, "", llm_response, source, sources_json, conversation_id, datetime.now())
    )
    conn.commit()
    conn.close()

def create_conversation_db(user_id, title):
    conn = get_db_connection()
    c = conn.cursor()
    conv_id = str(uuid.uuid4())
    c.execute("INSERT INTO conversations (id, user_id, title, created_at, is_pinned) VALUES (?, ?, ?, ?, 0)", (conv_id, user_id, title, datetime.now()))
    conn.commit()
    conn.close()
    return conv_id

def get_chat_history(conversation_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM interactions WHERE conversation_id = ? ORDER BY timestamp DESC LIMIT 10", (conversation_id,))
    rows = c.fetchall()
    conn.close()
    messages = []
    for row in reversed(rows):
        messages.append(HumanMessage(content=row["user_prompt"]))
        messages.append(AIMessage(content=row["llm_response"]))
    return messages

@router.post("/", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, current_user: User = Depends(get_current_user)):
    user_id = current_user.email 
    
    # Check Conversation ID
    if not request.conversation_id:
        title = request.message[:30] + "..."
        request.conversation_id = create_conversation_db(user_id, title)
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")

    # 1. Decide Strategy (Simple/Manual for now to match reference)
    # We can assume Vector Search if documents exist, or Web if explicit.
    # For now, we'll do a simple "Smart Retrieval" check.
    
    # NOTE: In 'junior dev' style, we might just search indiscriminately to be safe and simple.
    # But let's use the helper if available, or just default to vector search k=2
    
    context = ""
    sources = []
    strategy = "direct"
    
    # Simple Heuristic: If there are docs in vector store, search them.
    # But checking vector_store size is hard without a count method.
    # Let's just try to search and see if we get anything good.
    try:
        docs = vector_store.similarity_search(request.message, k=2)
        if docs:
            context_text = "\n\n".join([d.page_content for d in docs])
            context = f"Context from uploaded documents:\n{context_text}"
            sources = [{"title": "Document Context", "url": "#"}]
            strategy = "vector"
    except Exception:
        pass # Vector store might be empty or uninitialized

    # 2. Setup LLM
    llm = ChatGroq(temperature=0.3, groq_api_key=api_key, model_name=request.model)

    # 3. Construct System Prompt (The "Reasoning" Part)
    # Ref: Reference project uses "IMPORTANT: ... Explain all code..."
    
    reasoning_instruction = (
        "You are a smart AI assistant. "
        "Think step-by-step before answering. "
        "If the user asks for code, explain it clearly in comments. "
        "If you use context, cite it."
    )
    
    base_system = request.system_prompt if request.system_prompt else "You are a helpful assistant."
    full_system_prompt = f"{base_system}\n\n[INSTRUCTIONS]: {reasoning_instruction}\n\n{context}"

    # 4. Chat History
    history = get_chat_history(request.conversation_id)
    
    # 5. Build Message List
    messages = [SystemMessage(content=full_system_prompt)] + history + [HumanMessage(content=request.message)]
    
    # 6. Run
    response = llm.invoke(messages)
    response_text = response.content
    
    # 7. Log
    log_interaction_db(user_id, request.conversation_id, request.message, response_text, strategy, sources)
    
    return ChatResponse(
        response=response_text,
        conversation_id=request.conversation_id,
        sources=sources,
        strategy=strategy
    )

@router.get("/history")
def get_conversations(current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    c = conn.cursor()
    # Sort by pinned (DESC) then created_at (DESC)
    c.execute("SELECT * FROM conversations WHERE user_id = ? ORDER BY is_pinned DESC, created_at DESC", (current_user.email,))
    rows = c.fetchall()
    conn.close()
    
    conversation_list = []
    for row in rows:
        conversation_list.append(dict(row))
        
    return conversation_list

@router.put("/conversations/{conversation_id}")
def update_conversation(conversation_id: str, update: ConversationUpdate, current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT user_id FROM conversations WHERE id = ?", (conversation_id,))
    conv = c.fetchone()
    if not conv or conv["user_id"] != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if update.title is not None:
        c.execute("UPDATE conversations SET title = ? WHERE id = ?", (update.title, conversation_id))
    
    if update.is_pinned is not None:
        # Toggle pin status or set specific value? Pydantic model usually sends explicit bool/int
        c.execute("UPDATE conversations SET is_pinned = ? WHERE id = ?", (1 if update.is_pinned else 0, conversation_id))
        
    conn.commit()
    conn.close()
    return {"message": "Conversation updated"}

@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT user_id FROM conversations WHERE id = ?", (conversation_id,))
    conv = c.fetchone()
    if not conv or conv["user_id"] != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    c.execute("DELETE FROM interactions WHERE conversation_id = ?", (conversation_id,))
    c.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()
    return {"message": "Conversation deleted"}

@router.get("/history/{conversation_id}")
def get_conversation_messages(conversation_id: str, current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    c = conn.cursor()
    # Verify ownership
    c.execute("SELECT user_id FROM conversations WHERE id = ?", (conversation_id,))
    conv = c.fetchone()
    
    if not conv or conv["user_id"] != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    c.execute("SELECT * FROM interactions WHERE conversation_id = ? ORDER BY timestamp ASC", (conversation_id,))
    rows = c.fetchall()
    conn.close()
    
    formatted_messages = []
    for row in rows:
        formatted_messages.append({
            "role": "user",
            "content": row["user_prompt"]
        })
        
        sources_list = []
        if row["sources"]:
            sources_list = json.loads(row["sources"])
            
        formatted_messages.append({
            "role": "assistant",
            "content": row["llm_response"],
            "sources": sources_list
        })
        
    return formatted_messages
