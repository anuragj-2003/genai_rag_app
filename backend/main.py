import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

load_dotenv()

from routers import auth, chat, documents, settings, feedback
from init_dbs import init_dbs

# Initialize Database on Startup (Crucial for Render)
init_dbs()

app = FastAPI(title="GenAI Workspace API")

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(settings.router)
app.include_router(feedback.router)

# Origins for CORS
origins = [
    "http://localhost:5173", # Vite Default
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "https://genai-agent-app.netlify.app", # Old Name
    "https://agentic-rag.netlify.app", # Actual Netlify Name
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "GenAI Workspace API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
