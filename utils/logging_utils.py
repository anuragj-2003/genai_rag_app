import streamlit as st
from .state_manager import save_stats

def log_search(query: str, search_type: str, pages_scraped: int):
    """
    Logs a search query to session state and updates persistence stats.
    
    Input:
        query (str): The search query.
        search_type (str): Type of search (e.g., 'Custom Search', 'LLM Search').
        pages_scraped (int): Number of pages/results found.
    """
    st.session_state.search_count += 1
    st.session_state.pages_scraped_count += pages_scraped
    # We still add to the in-memory list for immediate updates on the dashboard
    st.session_state.query_history.insert(0, {"Query": query, "Type": search_type})
    st.session_state.query_history = st.session_state.query_history[:10]
    save_stats()

def log_llm_call(provider: str, model: str, prompt_tokens: int = 0, response_tokens: int = 0):
    """
    Logs an LLM call to session state and updates persistence stats.
    
    Input:
        provider (str): The LLM provider (e.g., 'Groq').
        model (str): The specific model used.
        prompt_tokens (int): Tokens in the prompt.
        response_tokens (int): Tokens in the response.
    """
    st.session_state.llm_call_count += 1
    st.session_state.llm_provider_usage[provider] = st.session_state.llm_provider_usage.get(provider, 0) + 1
    st.session_state.llm_model_usage[model] = st.session_state.llm_model_usage.get(model, 0) + 1
    st.session_state.token_count += prompt_tokens + response_tokens
    save_stats()
