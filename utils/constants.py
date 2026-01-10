from enum import Enum

class RetrievalStrategy(str, Enum):
    """
    Enum defining the available retrieval strategies for the Intelligent Agent.
    """
    DIRECT_LLM = "Direct LLM"
    VECTOR_BASED = "Vector-Based"
    HYBRID = "Hybrid"
    WEB_SEARCH = "Web Search"


