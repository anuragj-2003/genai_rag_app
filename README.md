# RAG App

A modern, full-stack AI-powered search and research assistant. Built with **React (Vite + Tailwind CSS)** on the frontend and **FastAPI** on the backend. It features advanced document interaction and query routing decision agents.

## Features

-   **Agentic Reasoning**: An AI agent that routes queries using LlamaIndex and Groq models.
-   **Advanced Document RAG**: Upload documents to a **local ChromaDB** vector store using local cached embeddings (`sentence-transformers`), eliminating API costs for embeddings.
-   **Hybrid Search & Reranking**: Combines semantic search with keyword search (`BM25`/`Whoosh`) and cross-encoder reranking for highly accurate retrieval.
-   **Rich Document Support**: Extract and convert text from PDFs, Images (OCR with Tesseract), Word documents, and Excel spreadsheets using `markitdown`.
-   **Semantic Caching & LLM Judge**: Accelerates repeated queries via semantic caching and evaluates response quality using an LLM-as-a-judge.
-   **Demo Mode (Guest Limits)**: Unauthenticated guest users can perform up to 5 usages (chats & uploads combined), persisted in SQLite. Once exceeded, users are prompted to log in/register via a modern Landing Page.
-   **Modern UI**: Sleek, responsive "Black" theme dashboard built with Tailwind CSS. Real-time chat with support for renaming, pinning, and deleting conversations. Edit & rerun messages.
-   **Secure Auth**: Email/Password authentication with Gmail SMTP OTP verification and JWT sessions. Rate limiting using `slowapi`.
-   **Production-Ready**: 
    - **Docker** support for easy backend containerization.
    - **Sentry** integration for monitoring and error tracking.
    - Automated nightly database backups (with optional S3 upload) and weekly data retention via `apscheduler`.

## Tech Stack

-   **Frontend**: React, Vite, Tailwind CSS, Lucide Icons, Axios.
-   **Backend**: FastAPI, Python, SQLite, LlamaIndex.
-   **Vector Database**: ChromaDB (Local, zero API cost).
-   **Search & Embeddings**: Sentence-Transformers, Whoosh, BM25, Cross-Encoder Reranker.
-   **AI Providers**: Groq.

## Getting Started

### Prerequisites

-   npm
-   Python 3.10+
-   Groq API Key
-   Tesseract OCR (for image parsing)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/j-anurag/genai_rag_app.git
    cd genai_rag_app
    ```

2.  **Backend Setup:**
    ```bash
    make myenv  # Or create environment: python3 -m venv myenv
    source myenv/bin/activate
    pip install -r backend/requirements.txt
    ```

3.  **Frontend Setup:**
    ```bash
    cd frontend
    npm install
    ```

4.  **Environment Variables:**
    Create a `.env` file in the root `genai_rag_app/` directory and `backend/` directory:
    ```env
    SMTP_SERVER=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=your_email@gmail.com
    SMTP_PASSWORD=your_app_password
    GROQ_API_KEY=your_groq_api_key
    SENTRY_DSN=your_sentry_dsn # Optional
    S3_BUCKET=your_s3_bucket # Optional, for backups
    ```

### Running the App

1.  **Start Backend (Port 8000):**
    ```bash
    source myenv/bin/activate
    python backend/main.py
    ```

2.  **Start Frontend (Port 5173):**
    ```bash
    cd frontend
    npm run dev
    ```

    Open your browser at `http://localhost:5173`.

### Docker (Backend)

You can run the backend application using Docker:
```bash
docker build -t genai_rag_backend .
docker run -p 8000:8000 --env-file .env genai_rag_backend
```

## Folder Structure

-   `backend/`: FastAPI application, database logic, AI utilities (hybrid search, caching, reranker), and LlamaIndex configurations.
-   `frontend/`: React application, UI components, pages (Landing, Settings, Chat, etc.), and state management.
-   `backend/data/`: SQLite databases and local ChromaDB persistence.
