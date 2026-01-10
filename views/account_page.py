import streamlit as st
from utils.auth_manager import login_user, update_password, delete_user, logout_user

def render_page():
    """Renders the Account Management Page."""
    st.title("👤 Account Settings")
    
    if not st.session_state.get("authenticated"):
        st.warning("Please log in to view account settings.")
        return

    email = st.session_state.get("user_email")
    auth_type = st.session_state.get("auth_mode", "email_password")
    
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
        if auth_type == "google_native":
             st.info("ℹ️ Your password is managed by Google. You cannot change it here.")
        else:
            with st.expander("Change Password", expanded=False):
                with st.form("change_pass_form"):
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

    # Danger Zone
    with st.expander("🚨 Danger Zone", expanded=False):
        st.warning("These actions are irreversible.")
        if st.button("Delete Account", type="primary"):
            st.session_state.confirm_delete = True
            
        if st.session_state.get("confirm_delete"):
            st.error("Are you sure? This will delete all your data permanently.")
            col_del_1, col_del_2 = st.columns(2)
            if col_del_1.button("Yes, Delete Everything"):
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
    if st.button("🚪 Log Out", use_container_width=True, type="secondary"):
        if st.session_state.get("auth_mode") == "google_native":
            st.logout()
        logout_user()
