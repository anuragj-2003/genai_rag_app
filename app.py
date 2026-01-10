import streamlit as st
from streamlit_option_menu import option_menu # Import the component
from utils.state_manager import init_state
from views.dashboard_page import render_page as render_dashboard
from views.custom_search_page import render_page as render_custom_search
from views.llm_search_page import render_page as render_llm_search
from views.settings_page import render_page as render_settings

# Set page configuration
st.set_page_config(
    page_title="GenAI Workspace",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
init_state()

#  API Key Verification & Setup 
# This ensures the app doesn't crash if deployed without secrets
if not st.session_state.get("GROQ_API_KEY") or not st.session_state.get("TAVILY_API_KEY"):
    st.title("⚙️ Setup Required")
    st.warning("API Keys are missing. Please provide them below to continue.")
    
    with st.form("api_key_form"):
        groq_key = st.text_input("Groq API Key", type="password", help="Get it from console.groq.com")
        tavily_key = st.text_input("Tavily API Key", type="password", help="Get it from tavily.com")
        
        if st.form_submit_button("Save & Continue", width="stretch"):
            if groq_key and tavily_key:
                st.session_state["GROQ_API_KEY"] = groq_key
                st.session_state["TAVILY_API_KEY"] = tavily_key
                st.success("Keys saved! Reloading...")
                st.rerun()
            else:
                st.error("Both keys are required.")
    
    st.stop() # Stop execution here until keys are provided

#  Navigation Logic 
# Determine default index based on potential page switch
default_index = 0
options = ["Dashboard", "Custom Search", "RAG Agent", "Settings"]

if "switch_page" in st.session_state and st.session_state.switch_page:
    target = st.session_state.switch_page
    if target in options:
        default_index = options.index(target)
    # Clear the switch signal so we don't get stuck
    st.session_state.switch_page = None

#  Sidebar 
with st.sidebar:
    st.header("GenAI Workspace")
    
    # Main Navigation Menu
    page = option_menu(
        menu_title=None,
        options=options,
        icons=["speedometer2", "search", "robot", "sliders"],
        menu_icon="cast",
        default_index=default_index,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#a0a0a0", "font-size": "18px"}, 
            "nav-link": {
                "font-size": "15px", "text-align": "left", "margin":"0px", "color": "#a0a0a0",
                "--hover-color": "#3c4043"
            },
            "nav-link-selected": {"background-color": "#2c2f33", "color": "#ffffff"},
        }
    )
    
    st.divider()

    # Conditionally display LLM settings
    if page == "RAG Agent":
        st.header("LLM Settings")
        
        st.session_state.llm_provider = "Groq"
        st.success("Using Groq")

        if st.button("Clear Chat History", width="stretch"):
            st.session_state.chat_messages = []
            st.rerun()

if page == "Dashboard":
    render_dashboard()
elif page == "Custom Search":
    render_custom_search()
elif page == "RAG Agent":
    render_llm_search()
elif page == "Settings":
    render_settings()

