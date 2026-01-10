import os
import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from utils.auth_manager import login_google_user

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'openid']

def get_google_auth_url():
    """Generates the Google Auth URL."""
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return None, "client_secret.json not found"
        
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="http://localhost:8501" # Start with local default
    )
    
    auth_url, _ = flow.authorization_url(prompt='consent')
    return auth_url, None

def handle_google_auth(code):
    """Exchanges auth code for credentials and logs user in."""
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri="http://localhost:8501"
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Verify and get email using google-api-python-client or just requests
        # Using requests for simplicity to get user info
        import requests
        headers = {'Authorization': f'Bearer {credentials.token}'}
        user_info = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers=headers).json()
        
        email = user_info.get('email')
        google_id = user_info.get('id')
        
        if email and google_id:
            success = login_google_user(email, google_id)
            if success:
                st.session_state["user_email"] = email
                st.session_state["authenticated"] = True
                st.session_state["auth_mode"] = "google"
                return True, "Login successful"
        
        return False, "Failed to get user info"
        
    except Exception as e:
        return False, str(e)
