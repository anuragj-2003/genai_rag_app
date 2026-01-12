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
        [
            "qwen/qwen3-32b", 
            "groq/compound", 
            "llama-3.1-8b-instant", 
            "llama-3.3-70b-versatile", 
            "openai/gpt-oss-120b", 
            "openai/gpt-oss-20b", 
            "whisper-large-v3"
        ],
        index=3 # Default to llama-3.3-70b-versatile if possible, or 0
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
    
    # 3. Custom Behavior (Persona)
    st.subheader("🧠 Agent Behavior")
    st.caption("Define a custom persona or set of rules for the agent.")
    
    custom_behavior = st.text_area(
        "Custom System Instructions",
        value=st.session_state.settings.get("custom_behavior", ""),
        placeholder="e.g., 'Always answer in a sarcastic tone.', 'Be extremely concise.', 'Format output as JSON.'",
        height=100
    )
    
    if custom_behavior != st.session_state.settings.get("custom_behavior", ""):
        if st.button("Save Behavior", type="primary", key="save_persona"):
            st.session_state.settings["custom_behavior"] = custom_behavior
            save_config(st.session_state.settings)
            st.success("Persona saved!")

    st.markdown("---")

    # 4. Memory Management
    st.subheader("💾 Saved Memories")
    st.caption("Manage interactions the agent learns from.")
    
    with st.expander("Manage Memories"):
        from utils.database import get_rated_interactions, delete_individual_interaction
        user_email = st.session_state.get("user_email")
        
        if user_email:
            memories = get_rated_interactions(user_email)
            if memories:
                for mem in memories:
                    c1, c2 = st.columns([0.85, 0.15])
                    with c1:
                        # Color code based on rating
                        if mem['rating'] > 0:
                            st.markdown("✅ **Reinforced Pattern** (Thumbs Up)")
                        else:
                            st.markdown("⛔ **Avoidance Pattern** (Thumbs Down)")
                            
                        st.markdown(f"**Q:** {mem['user_prompt'][:50]}...")
                        st.caption(f"**A:** {mem['llm_response'][:50]}...")
                    with c2:
                        if st.button("🗑️", key=f"del_mem_{mem['id']}"):
                            delete_individual_interaction(mem['id'])
                            st.rerun()
                    st.divider()
            else:
                st.info("No saved memories yet. Rate interactions 👍 or 👎 to add them.")

    st.markdown("---")
    
    # 5. Data Management
    st.subheader("Data Management")
    
    # Delete All Conversations
    with st.expander("Delete All Conversations"):
        st.write("This will permanently delete ALL your chat history.")
        if st.button("Delete All Chats", type="secondary"):
            st.session_state.confirm_delete_all = True
            
        if st.session_state.get("confirm_delete_all"):
            st.error("This cannot be undone.")
            col1, col2 = st.columns(2)
            if col1.button("Yes, Clear History"):
                from utils.database import delete_all_user_conversations
                user_email = st.session_state.get("user_email")
                if user_email:
                    delete_all_user_conversations(user_email)
                    st.success("All conversations deleted.")
                    st.session_state.confirm_delete_all = False
                    # Reset chat state
                    st.session_state.current_conversation_id = None
                    st.session_state.chat_messages = []
                    st.rerun()
            if col2.button("Cancel", key="cancel_del_all"):
                st.session_state.confirm_delete_all = False
                st.rerun()

    st.markdown("---")
    st.info("These settings control the behavior of the RAG Agent and Chat.")
