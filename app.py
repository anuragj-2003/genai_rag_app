import streamlit as st
from streamlit_option_menu import option_menu # Import the component
from utils.state_manager import init_state
from views.dashboard_page import render_page as render_dashboard
from views.chat_page import render_page as render_chat
from views.settings_page import render_page as render_settings
from views.account_page import render_page as render_account
from views.auth_page import render_page as render_auth
from utils.auth_manager import init_db
from utils.database import get_conversations, create_conversation, delete_conversation, rename_conversation

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
if hasattr(st, "user") and getattr(st.user, "email", None):
    # Sync Native Auth to Session State
    # Only if not authenticated AND not explicitly logged out
    if not st.session_state.get("authenticated") and not st.session_state.get("logged_out"):
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
from utils.auth_manager import has_password, update_password, get_user_name, update_user_name
user_email = st.session_state.get("user_email")

# 1. Check Name (Onboarding)
current_name = get_user_name(user_email)
st.session_state["user_full_name"] = current_name # Sync to session

if not current_name:
    st.title("👋 Welcome!")
    st.info("Let's get to know you. What should we call you?")
    
    with st.form("set_name_form"):
        name_in = st.text_input("Full Name", placeholder="John Doe")
        if st.form_submit_button("Continue"):
            if name_in.strip():
                if update_user_name(user_email, name_in.strip()):
                    st.success("Nice to meet you!")
                    st.session_state["user_full_name"] = name_in.strip()
                    st.rerun()
                else:
                    st.error("Failed to save name.")
            else:
                st.error("Please enter a name.")
    st.stop() # Stop until name is set

# 2. Check Password (Security) for Google Users
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

# Start fresh if explicit login just happened
if st.session_state.get("auth_mode") == "google_native" and "joined" not in st.session_state:
    st.session_state.joined = True
    # Auto-load the last conversation for this user
    user_convs = get_conversations(st.session_state.user_email)
    if user_convs:
        st.session_state.current_conversation_id = user_convs[0]["id"]
    else:
        st.session_state.current_conversation_id = None

# Navigation Logic
# States: "Agent Chat", "Account"
if "current_page" not in st.session_state:
    st.session_state.current_page = "Agent Chat"

if "switch_page" in st.session_state and st.session_state.switch_page:
    target = st.session_state.switch_page
    # Map old targets if necessary, though simplified now
    if target in ["Dashboard", "Settings"]:
        st.session_state.current_page = "Account" # Redirect to Account hub
    elif target in ["Agent Chat", "Account"]:
         st.session_state.current_page = target
    st.session_state.switch_page = None

# Sidebar Layout (Strict ChatGPT Style)
with st.sidebar:
    # 1. App Header
    st.title("GenAI Workspace")
    
    # 2. New Chat Button (Primary Action)
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        st.session_state.current_conversation_id = None
        st.session_state.chat_messages = []
        st.session_state.current_page = "Agent Chat"
        st.rerun()
        
    st.markdown("---")
    
    # 3. History List (Scrollable - takes most space)
    st.caption("Recent")
    # CSS to make this container take remaining height could be complex in pure Streamlit,
    # but we can set a fixed large height or rely on natural flow.
    # ChatGPT puts history here.
    with st.container(height=500): 
        # Pass user_email to get_conversations
        user_email = st.session_state.get("user_email")
        conversations = get_conversations(user_email) if user_email else []
        
        for conv in conversations:
            # Highlight current conversation
            is_current = st.session_state.get("current_conversation_id") == conv["id"]
            
            # Truncate title strictly to avoid wrapping (approx 18 chars max)
            display_title = conv["title"]
            if len(display_title) > 18:
                display_title = display_title[:15] + "..."
            
            label = f"**{display_title}**" if is_current else display_title
            
            if st.button(label, key=f"conv_{conv['id']}", help=conv['title'], use_container_width=True):
                st.session_state.current_conversation_id = conv["id"]
                st.session_state.current_page = "Agent Chat" 
                # Clear messages in global state so chat_page reloads them
                st.session_state.chat_messages = [] 
                st.rerun()
    
    # 4. Bottom Account Button
    st.markdown("---")
    
    # Use a styled button for Account
    # We want it to look like a user profile item at the bottom.
    user_label = st.session_state.user_email
    if len(user_label) > 20: user_label = user_label[:18] + "..."
    
    if st.button(f"👤 {user_label}", use_container_width=True):
        st.session_state.current_page = "Account"
        st.rerun()

# Routing
if st.session_state.current_page == "Account":
    # This now renders the Hub (Profile, Dashboard, Settings)
    from views.account_page import render_page as render_account_hub
    render_account_hub()
else:
    # Default to Chat
    render_chat()

