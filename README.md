# AI Workspace

A modern, full-stack AI-powered search and research assistant. Built with **React (Vite + Tailwind CSS)** on the frontend and **FastAPI** on the backend. It features an intelligent ReAct agent for reasoning and document interaction.

## Features

-   **🧠 Agentic Reasoning**: An AI agent that thinks step-by-step to answer complex queries.
-   **🎨 Modern UI**: Sleek, responsive "Black" theme dashboard built with Tailwind CSS.
-   **💬 Chat Interface**: Real-time chat with support for renaming, pinning, and deleting conversations.
-   **✏️ Edit & Rerun**: Edit your messages and rerun the AI response.
-   **📂 Document RAG**: Upload documents for the AI to analyze and reference.
-   **🔐 Secure Auth**: Email/Password authentication with OTP verification and JWT sessions.

## Tech Stack

-   **Frontend**: React, Vite, Tailwind CSS, Lucide Icons, Axios.
-   **Backend**: FastAPI, Python, SQLite, LangChain.
-   **AI Providers**: Groq (LLM), HuggingFace (Embeddings - Lazy Loaded).

## Getting Started

### Prerequisites

-   Node.js & npm
-   Python 3.10+
-   Groq API Key

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd react-app
    ```

2.  **Backend Setup:**
    ```bash
    cd backend
    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Frontend Setup:**
    ```bash
    cd ../frontend
    npm install
    ```

4.  **Environment Variables:**
    Create a `.env` file in the root `react-app/` directory:
    ```env
    GROQ_API_KEY=your_groq_api_key
    # Add email config for OTP if needed
    ```

### Running the App

1.  **Start Backend (Port 8002):**
    ```bash
    cd backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8002
    ```

2.  **Start Frontend:**
    ```bash
    cd frontend
    npm run dev
    ```

    Open your browser at `http://localhost:5173`.

## Folder Structure

-   `backend/`: FastAPI application, database logic, and AI agents.
-   `frontend/`: React application, UI components, and state management.
-   `data/`: SQLite databases (users.db, interactions.db).

## License

MIT
