import streamlit as st
import time
from utils.auth_manager import login_user, register_user, user_exists, update_password
from utils.email_service import generate_otp, send_otp_email

# Styling Injection
def inject_custom_css():
    st.markdown("""
        <style>
        .auth-container {
            padding: 2rem;
            background-color: #f0f2f5; 
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .app-title {
            color: #1877f2;
            font-weight: 800;
            font-size: 3.5rem;
            margin-bottom: 0.5rem;
        }
        .app-tagline {
            font-size: 1.5rem;
            color: #333;
        }
        [data-testid="stForm"] {
            border: none;
            padding: 0;
        }
        .stButton>button {
            border-radius: 6px;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

@st.dialog("Sign Up")
def signup_dialog():
    st.caption("It's quick and easy.")
    with st.form("signup_modal_form"):
        new_email = st.text_input("Email")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        # Submit
        submitted = st.form_submit_button("Sign Up", type="primary", use_container_width=True)
        if submitted:
            if new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
            elif user_exists(new_email):
                st.error("User already exists.")
            else:
                # Initiate OTP
                otp_code = generate_otp()
                success, msg = send_otp_email(new_email, otp_code)
                if success:
                    st.session_state.otp_context = {
                        "active": True, 
                        "email": new_email, 
                        "code": otp_code, 
                        "type": "signup",
                        "data": {"password": new_password}
                    }
                    st.rerun()
                else:
                    st.error(f"Failed to send email: {msg}")

@st.dialog("Forgot Password")
def forgot_password_dialog():
    st.caption("We will send you a code to reset your password.")
    with st.form("forgot_pw_form"):
        rec_email = st.text_input("Email Address")
        submitted = st.form_submit_button("Send Recovery Code", type="primary", use_container_width=True)
        if submitted:
            if user_exists(rec_email):
                otp_code = generate_otp()
                success, msg = send_otp_email(rec_email, otp_code)
                if success:
                    st.session_state.otp_context = {
                        "active": True,
                        "email": rec_email,
                        "code": otp_code,
                        "type": "forgot_password",
                        "data": {}
                    }
                    st.rerun()
                else:
                    st.error(f"Email Error: {msg}")
            else:
                st.error("Account not found.")

def render_page():
    inject_custom_css()
    
    # OTP Verification Overlay
    if st.session_state.get("otp_context", {}).get("active"):
        with st.container(border=True):
            st.markdown("## 🔐 Verify Email")
            st.info(f"Enter the code sent to {st.session_state.otp_context['email']}")
            
            otp_input = st.text_input("Enter 6-digit Code", max_chars=6, key="otp_in")
            
            c1, c2 = st.columns(2)
            if c1.button("Confirm", type="primary", use_container_width=True):
                if otp_input == st.session_state.otp_context["code"]:
                    ctx = st.session_state.otp_context
                    if ctx["type"] == "signup":
                         register_user(ctx["email"], ctx["data"]["password"])
                         st.success("Account Created! Please Login.")
                         st.session_state.otp_context["active"] = False
                         time.sleep(1)
                         st.rerun()
                    elif ctx["type"] == "forgot_password":
                         st.session_state.otp_context["verified_for_reset"] = True
                         st.rerun()
                else:
                    st.error("Incorrect Code")
            
            if c2.button("Cancel", use_container_width=True):
                st.session_state.otp_context = {"active": False}
                st.rerun()
        return

    # Verified Reset Password View
    if st.session_state.get("otp_context", {}).get("verified_for_reset"):
        with st.container(border=True):
            st.subheader("Reset Password")
            p1 = st.text_input("New Password", type="password")
            p2 = st.text_input("Confirm", type="password")
            if st.button("Update Password", type="primary"):
                 if p1==p2 and len(p1)>=6:
                     update_password(st.session_state.otp_context["email"], p1)
                     st.success("Password Reset! Please Login.")
                     st.session_state.otp_context = {"active": False}
                     time.sleep(1)
                     st.rerun()
                 else:
                     st.error("Passwords must match (6+ chars).")
        return

    # Main Facebook-Style Layout
    # Spacer to center vertically somewhat
    st.write("")
    st.write("")
    
    col_left, col_right = st.columns([1.2, 1], gap="large")
    
    with col_left:
        st.markdown('<div class="app-title">GenAI Workspace</div>', unsafe_allow_html=True)
        st.markdown('<div class="app-tagline">Unlock the power of RAG and AI agents in one dynamic platform.</div>', unsafe_allow_html=True)
    
    with col_right:
        with st.container(border=True):
            # Login Form
            with st.form("main_login_form"):
                email = st.text_input("Email address", placeholder="Email address")
                password = st.text_input("Password", type="password", placeholder="Password")
                
                # Main Login Button
                login_btn = st.form_submit_button("Log In", type="primary", use_container_width=True)
                
                if login_btn:
                    if login_user(email, password):
                         st.session_state["user_email"] = email
                         st.session_state["authenticated"] = True
                         st.rerun()
                    else:
                        st.error("Invalid credentials.")

            # Forgot Password (Link style using button with no border? Streamlit doesn't support links easily)
            col_fwd, col_google = st.columns(2)
            if st.button("Forgotten password?", type="tertiary"):
                forgot_password_dialog()
            
            # Google Login
            if st.button("Log in with Google", icon="🕸️", use_container_width=True):
                 st.login(provider="google")
            
            st.markdown("---")
            
            # Create New Account (Green-ish button style if possible, strictly using type="secondary" or primary)
            # We keep it centralized
            c_center = st.columns([1,2,1])
            with c_center[1]:
                if st.button("Create new account", type="secondary", use_container_width=True):
                    signup_dialog()
