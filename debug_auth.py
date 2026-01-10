import streamlit as st
import os

st.title("Debug Auth")

st.write(f"Streamlit Version: {st.__version__}")

st.write("Current Working Directory:", os.getcwd())

secrets_path = os.path.join(os.getcwd(), ".streamlit", "secrets.toml")
st.write(f"Secrets File Exists: {os.path.exists(secrets_path)}")

if os.path.exists(secrets_path):
    with open(secrets_path, "r") as f:
        st.code(f.read(), language="toml")

st.subheader("Loaded Secrets")
try:
    st.json(dict(st.secrets))
except Exception as e:
    st.error(f"Error loading secrets: {e}")
