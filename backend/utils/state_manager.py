import streamlit as st
import os
import json
from dotenv import load_dotenv
from .database import setup_database, load_query_history_from_db, load_chat_history_from_db
from .config_utils import load_keys, load_config
from .vector_store_manager import VectorStoreManager

STATS_FILE = os.path.join(os.path.dirname(__file__), "stats.json")

def load_stats():
    """Loads dashboard statistics from the stats file."""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_stats():
    """Saves the current dashboard statistics to the stats file."""
    stats_data = {
        "search_count": st.session_state.search_count,
        "llm_call_count": st.session_state.llm_call_count,
        "token_count": st.session_state.token_count,
        "pages_scraped_count": st.session_state.pages_scraped_count,
        "llm_provider_usage": st.session_state.llm_provider_usage,
        "llm_model_usage": st.session_state.llm_model_usage,
    }
    with open(STATS_FILE, "w") as f:
        json.dump(stats_data, f)

def init_state():
    if "app_started" not in st.session_state:
        setup_database()
        
        # 1. Try loading from .env explicitly (force reload to pick up changes)
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        load_dotenv(env_path, override=True)
        
        # 2. Try getting keys from multiple sources (Session > Secrets > Env)
        # We check st.secrets first (Streamlit native), then os.environ
        
        def get_secret(key):
            try:
                if key in st.secrets:
                    return st.secrets[key]
            except FileNotFoundError:
                pass # No secrets file found, fall back to env
            except Exception:
                pass 
            return os.getenv(key)

        tavily = get_secret("TAVILY_API_KEY")
        if tavily: st.session_state.TAVILY_API_KEY = tavily.strip()
        
        groq = get_secret("GROQ_API_KEY")
        if groq: st.session_state.GROQ_API_KEY = groq.strip()
        
        stats = load_stats()
        st.session_state.setdefault("search_count", stats.get("search_count", 0))
        st.session_state.setdefault("llm_call_count", stats.get("llm_call_count", 0))
        st.session_state.setdefault("token_count", stats.get("token_count", 0))
        st.session_state.setdefault("pages_scraped_count", stats.get("pages_scraped_count", 0))
        st.session_state.setdefault("llm_provider_usage", stats.get("llm_provider_usage", {"Groq (Web-based)": 0}))
        st.session_state.setdefault("llm_model_usage", stats.get("llm_model_usage", {}))
        
        st.session_state.setdefault("llm_provider_usage", stats.get("llm_provider_usage", {"Groq (Web-based)": 0}))
        # Filter out "Ollama" if it exists in loaded stats
        if "Ollama" in st.session_state.llm_provider_usage:
             del st.session_state.llm_provider_usage["Ollama"]
             
        st.session_state.setdefault("llm_model_usage", stats.get("llm_model_usage", {}))
        
        # Load query history from the database
        st.session_state.setdefault("query_history", load_query_history_from_db())

        # Load settings from config file or use defaults
        saved_settings = load_config()
        default_settings = {
            "tavily_depth": 5, 
            "temperature": 0.5,
            "groq_model": "llama-3.3-70b-versatile",
            "search_count": 5
        }
        # Merge saved into defaults (saved takes precedence)
        st.session_state.setdefault("settings", {**default_settings, **saved_settings})
        st.session_state.setdefault("chat_messages", load_chat_history_from_db())
        
        # Initialize Vector Store Manager
        if "vector_store_manager" not in st.session_state:
             st.session_state.vector_store_manager = VectorStoreManager()
             
        st.session_state.app_started = True
