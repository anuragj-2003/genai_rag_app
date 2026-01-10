import streamlit as st
from streamlit_option_menu import option_menu # Import the component
from utils.state_manager import init_state
from views.dashboard_page import render_page as render_dashboard
from views.chat_page import render_page as render_chat
from views.settings_page import render_page as render_settings
from views.account_page import render_page as render_account
from views.auth_page import render_page as render_auth
from utils.auth_manager import init_db

# Initialize User Database
init_db()

# Set page configuration
st.set_page_config(
    page_title="GenAI Workspace",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
init_state()

# Authentication Logic (Hybrid: Native Google + Custom Email/Pass)

# Check Native Google Auth first
# Note: accessing st.user might require newer streamlit, ensuring graceful fallback or direct usage
if hasattr(st, "user") and st.user.email:
    # Sync Native Auth to Session State
    if not st.session_state.get("authenticated"):
        email = st.user.email
        # Register/Update in DB
        from utils.auth_manager import login_google_user
        login_google_user(email, "google_native")
        
        st.session_state["user_email"] = email
        st.session_state["authenticated"] = True
        st.session_state["auth_mode"] = "google_native"
        st.rerun()

# Check Session State for any Auth
if not st.session_state.get("authenticated"):
    render_auth()
    st.stop()

# Post-Auth: Force Password Setup for Google Users (if missing)
from utils.auth_manager import has_password, update_password
user_email = st.session_state.get("user_email")

if not has_password(user_email):
    st.title("🔐 Setup Password")
    st.info("Since you logged in with Google, please set a backup password for your account.")
    
    with st.form("set_google_pass"):
        p1 = st.text_input("New Password", type="password")
        p2 = st.text_input("Confirm Password", type="password")
        if st.form_submit_button("Set Password & Continue"):
            if p1 == p2 and len(p1) >= 6:
                success, msg = update_password(user_email, p1)
                if success:
                    st.success("Password Set!")
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.error("Passwords must match and be 6+ chars.")
    st.stop() # Stop here until password is set

# API Key Verification & Setup
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

# Navigation Logic
default_index = 0
options = ["Dashboard", "Agent Chat", "Settings", "Account"]

if "switch_page" in st.session_state and st.session_state.switch_page:
    target = st.session_state.switch_page
    if target in options:
        default_index = options.index(target)
    # Clear the switch signal
    st.session_state.switch_page = None

# Sidebar 
with st.sidebar:
    st.header("GenAI Workspace")
    
    selected_page = option_menu(
        "Navigation", 
        options,
        icons=["speedometer2", "robot", "search", "gear", "person-circle"],
        menu_icon="cast", 
        default_index=default_index,
    )
    
    st.markdown("---")
    st.caption(f"Logged in as: {st.session_state.user_email}")

# Routing
if selected_page == "Dashboard":
    render_dashboard()
elif selected_page == "Agent Chat":
    render_chat()
elif selected_page == "Settings":
    render_settings()
elif selected_page == "Account":
    render_account()
