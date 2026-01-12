import streamlit as st
from utils.auth_manager import login_user, update_password, delete_user, logout_user
from views.dashboard_page import render_page as render_dashboard
from views.settings_page import render_page as render_settings

def render_page():
    """Renders the Account Management Page with Profile, Dashboard, and Settings tabs."""
    st.title("User Account")
    
    if not st.session_state.get("authenticated"):
        st.warning("Please log in to view account settings.")
        return

    # Modern Tab Layout
    tab1, tab2, tab3 = st.tabs(["👤 Profile", "📊 Dashboard", "⚙️ Settings"])
    
    email = st.session_state.get("user_email")
    auth_type = st.session_state.get("auth_mode", "email_password")
    
    # Tab 1: Profile
    with tab1:
        # Profile Section
        with st.container(border=True):
            st.subheader("Profile Info")
            col1, col2 = st.columns([1, 3])
            with col1:
                 st.markdown("# 🧑‍💻") # Avatar placeholder
            with col2:
                 st.markdown(f"**Email:** `{email}`")
                 st.caption(f"**Login Method:** {auth_type.replace('_', ' ').title()}")

        st.markdown("---")

        # Security Section
        st.subheader("🔐 Security")
        with st.container(border=True):
            with st.expander("Change Password", expanded=False):
                with st.form("change_pass_form"):
                    st.caption("Update your local password for email login.")
                    old_p = st.text_input("Current Password", type="password")
                    new_p = st.text_input("New Password", type="password")
                    confirm_p = st.text_input("Confirm New Password", type="password")
                    
                    if st.form_submit_button("Update Password", use_container_width=True):
                        # Verify old
                        if login_user(email, old_p):
                            if new_p == confirm_p and len(new_p) >=6:
                                success, msg = update_password(email, new_p)
                                if success:
                                    st.success("✅ Password Updated Successfully!")
                                else:
                                    st.error(msg)
                            else:
                                st.error("New passwords must match and be 6+ chars.")
                        else:
                            st.error("Current password incorrect.")

        st.markdown("---")

        # Data & Privacy
        with st.expander("Data & Privacy", expanded=False):
            st.warning("Actions here are permanent.")
            if st.button("Delete Account", type="primary"):
                st.session_state.confirm_delete = True
                
            if st.session_state.get("confirm_delete"):
                st.error("This will delete all your data permanently.")
                col_del_1, col_del_2 = st.columns(2)
                if col_del_1.button("Yes, Delete"):
                     from utils.database import delete_all_user_conversations
                     delete_all_user_conversations(email)
                     
                     if delete_user(email):
                         st.success("Account deleted.")
                         logout_user()
                     else:
                         st.error("Failed to delete account.")
                if col_del_2.button("Cancel"):
                    st.session_state.confirm_delete = False
                    st.rerun()

        st.markdown("---")
        
        # Logout
        if st.button("Log Out", use_container_width=True, type="secondary"):
            if st.session_state.get("auth_mode") == "google_native":
                st.logout()
            logout_user()

    # Tab 2: Dashboard
    with tab2:
        render_dashboard()
        
    # Tab 3: Settings
    with tab3:
        render_settings()
