import os
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

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

def load_keys():
    """
    Loads API keys from environment variables.
    
    Output:
        dict: Dictionary containing API keys.
    """
    # Simply return values from os.environ as load_dotenv is called on import/init
    return {
        "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY"),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY")
    }
