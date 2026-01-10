import streamlit as st
from utils.config_utils import save_keys


def render_page():
    """
    Renders the Settings page.
    Manages API keys and application configuration (Model, Temperature, Search Depth).
    """
    st.title("Settings")


    st.header("Manage API Keys")
    tavily_key = st.text_input("Tavily API Key", type="password", value=st.session_state.get("TAVILY_API_KEY", ""))
    groq_key = st.text_input("Groq API Key", type="password", value=st.session_state.get("GROQ_API_KEY", ""))


    if st.button("Save API Keys"):
        st.session_state.TAVILY_API_KEY = tavily_key
        st.session_state.GROQ_API_KEY = groq_key
        save_keys(tavily_key, groq_key)
        st.success("API keys saved!")
        st.rerun()


    st.divider()


    st.header("LLM & Search Configuration")
    with st.form("settings_form"):

        groq_models = ["openai/gpt-oss-120b", "qwen/qwen3-32b", "llama-3.3-70b-versatile", "whisper-large-v3"]
        current_groq = st.session_state.settings.get("groq_model", "llama-3.3-70b-versatile")
        if current_groq not in groq_models: current_groq = groq_models[0]
        selected_groq = st.selectbox("Groq Model", options=groq_models, index=groq_models.index(current_groq))
        
        selected_temp = st.slider("LLM Temperature", min_value=0.0, max_value=1.0, value=st.session_state.settings.get("temperature", 0.5), step=0.05)
        selected_depth = st.selectbox("Default Search Depth (1-2: Basic, 3-5: Adv)", options=[1, 2, 3, 4, 5], index=st.session_state.settings.get("tavily_depth", 5) - 1)
        selected_count = st.slider("Search Result Count", min_value=1, max_value=10, value=st.session_state.settings.get("search_count", 5))
        
        if st.form_submit_button("Save All Settings", width="stretch"):
            st.session_state.settings["groq_model"] = selected_groq
            st.session_state.settings["temperature"] = selected_temp
            st.session_state.settings["tavily_depth"] = selected_depth
            st.session_state.settings["search_count"] = selected_count
            st.success("Settings saved!")
