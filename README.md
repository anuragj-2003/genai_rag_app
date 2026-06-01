# RAG App

A modern, full-stack AI-powered search and research assistant. Built with **React (Vite + Tailwind CSS)** on the frontend and **FastAPI** on the backend. It features document interaction and query routing decision agents.

## Features

-   **Agentic Reasoning**: An AI agent that routing queries using LlamaIndex and Groq models.
-   **Demo Mode (Guest Limits)**: Unauthenticated guest users can perform up to 5 usages (chats & uploads combined), persisted in SQLite. Once exceeded, users are prompted to log in/register.
-   **Modern UI**: Sleek, responsive "Black" theme dashboard built with Tailwind CSS.
-   **Chat Interface**: Real-time chat with support for renaming, pinning, and deleting conversations.
-   **Edit & Rerun**: Edit your messages and rerun the AI response.
-   **Document RAG**: Upload documents to Pinecone vector store using server-side integrated embeddings.
-   **Secure Auth**: Email/Password authentication with Gmail SMTP OTP verification and JWT sessions.

## Tech Stack

-   **Frontend**: React, Vite, Tailwind CSS, Lucide Icons, Axios.
-   **Backend**: FastAPI, Python, SQLite, LlamaIndex.
-   **Vector Database**: Pinecone (Server-side integrated embeddings - no local memory overhead).
-   **AI Providers**: Groq (LLM - Default: `openai/gpt-oss-120b`).

## Getting Started

### Prerequisites

-   Node.js & npm
-   Python 3.10+
-   Groq API Key
-   Pinecone API Key & Index

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
    PINECONE_API_KEY=your_pinecone_key
    PINECONE_INDEX_NAME=quickstart-py
    GROQ_API_KEY=your_groq_api_key
    ```

### Running the App

1.  **Start Backend (Port 8002):**
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

## Folder Structure

-   `backend/`: FastAPI application, database logic, and LlamaIndex configurations.
-   `frontend/`: React application, UI components, and state management.
-   `backend/data/`: SQLite databases (users.db, interactions.db).

## License

MIT
