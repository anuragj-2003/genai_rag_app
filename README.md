# AI Search Assistant

A powerful, AI-powered search and research assistant built with Streamlit. This application combines web search capabilities with a Retrieval-Augmented Generation (RAG) agent to help you find and synthesize information efficiently.

## Features

-   **🔍 Custom Search**: Perform targeted web searches using specialized tools.
-   **🤖 RAG Agent**: Chat with an AI that has access to your search results and documents.
-   **📊 Dashboard**: View analytics on your usage, including search counts and token usage.
-   **⚙️ Settings**: Configure your LLM providers (Groq) and search parameters.

## Getting Started

### Prerequisites

-   Python 3.8+
-   [Groq API Key](https://console.groq.com/)
-   [Tavily API Key](https://tavily.com/)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd AI-Search-Assistant
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the root directory and add your API keys:
    ```env
    GROQ_API_KEY=your_groq_api_key
    TAVILY_API_KEY=your_tavily_api_key
    ```

### Running the App

```bash
streamlit run app.py
```

## Project Structure

-   `app.py`: Main entry point of the application.
-   `views/`: Contains the individual pages (Dashboard, Search, RAG Agent, Settings).
-   `utils/`: Helper functions for database, state management, and API clients.
-   `data/`: Stores local interaction history (sqlite database).
-   `prompts/`: System prompts for the AI agent.

## Technology Stack

-   **Frontend**: Streamlit
-   **LLM Integration**: Groq
-   **Search**: Tavily Search API
-   **Database**: SQLite

## Deployment

### Handling Secrets

When deploying to platforms like Streamlit Cloud, the `.env` file is not uploaded. You must set your secrets in the platform's dashboard.

**Streamlit Cloud:**
1.  Go to your app dashboard.
2.  Click "Edit" -> "Settings" -> "Secrets".
3.  Paste your keys in TOML format:
    ```toml
    GROQ_API_KEY = "your_key_here"
    TAVILY_API_KEY = "your_key_here"
    ```

**Fallback:**
If secrets are not configured, the app will automatically show a "Setup Required" screen where you can enter your API keys securely for the session.
