from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Message(BaseModel):
    role: str
    content: str
    
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: str = "llama-3.3-70b-versatile"
    system_prompt: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: List[dict] = []
    strategy: str

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None
