import streamlit as st
import json
from utils.config_utils import load_config, save_config

def render_page():
    """
    Renders the Settings page.
    Allows users to configure model parameters and API keys.
    """
    st.title("⚙️ Model Configuration")

    # Model Settings Section
    st.subheader("LLM Parameters")
    
    current_settings = st.session_state.settings
    
    # 1. Groq Model Selection
    new_model = st.selectbox(
        "Groq Model",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma-7b-it"],
        index=0
    )
    
    # 2. Search Depth (Tavily)
    search_depth = st.slider(
        "Search Depth (Tavily)",
        min_value=1, max_value=10, 
        value=current_settings.get("tavily_depth", 5)
    )
    
    # 3. Temperature
    temperature = st.slider(
        "Temperature",
        min_value=0.0, max_value=1.0, 
        value=current_settings.get("temperature", 0.5)
    )

    # Save Button
    if st.button("Save Configuration", type="primary"):
        # Update Session State
        st.session_state.settings.update({
            "groq_model": new_model,
            "tavily_depth": search_depth,
            "temperature": temperature
        })
        
        # Save to Persistent Config (JSON)
        save_config(st.session_state.settings)
        
        st.success("✅ Settings saved successfully!")
    
    st.markdown("---")
    st.info("These settings control the behavior of the RAG Agent and Chat.")
