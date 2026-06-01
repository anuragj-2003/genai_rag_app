"""
state.py — Application-level singletons.
ChromaDB manager is initialized lazily on first use.
"""
# Re-export chroma_manager for any legacy imports
from utils import chroma_manager as vector_store

__all__ = ["vector_store"]
