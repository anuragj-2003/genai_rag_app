import os

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

def load_prompt(filename: str) -> str:
    """Loads a prompt from the prompts directory."""
    path = os.path.join(PROMPTS_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return f"Error: Prompt file '{filename}' not found."
