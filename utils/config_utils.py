import os
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

import json

# Load environment variables
load_dotenv()

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "client_config.json")

def save_keys(tavily_api_key: str, groq_api_key: str):
    """
    Saves API keys to the .env file.
    
    Input:
        tavily_api_key (str): Tavily API Key.
        groq_api_key (str): Groq API Key.
    """
    # Create .env if it doesn't exist
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, "w") as f:
            f.write("")

    set_key(ENV_FILE, "TAVILY_API_KEY", tavily_api_key)
    set_key(ENV_FILE, "GROQ_API_KEY", groq_api_key)
    
    # Reload environment to apply changes immediately
    load_dotenv(ENV_FILE, override=True)

import streamlit as st

def get_env_var(key: str):
    """
    Helper to get an environment variable, prioritizing Streamlit secrets.
    """
    # 1. Try Streamlit Secrets (for Cloud Deployment)
    if hasattr(st, "secrets") and key in st.secrets:
        return st.secrets[key]
    
    # 2. Try OS Environment (for Local .env)
    return os.getenv(key)

def load_keys():
    """
    Loads API keys from Streamlit secrets or environment variables.
    
    Output:
        dict: Dictionary containing API keys.
    """
    return {
        "TAVILY_API_KEY": get_env_var("TAVILY_API_KEY"),
        "GROQ_API_KEY": get_env_var("GROQ_API_KEY")
    }

def load_config():
    """
    Loads general application settings from config file.
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config_data):
    """
    Saves application settings to config file.
    """
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=4)
