from enum import Enum

class RetrievalStrategy(str, Enum):
    """
    Enum defining the available retrieval strategies for the Intelligent Agent.
    """
    DIRECT_LLM = "Direct LLM"
    WEB_SEARCH = "Web Search"
    
    # Vector-Based
    VECTOR = "Vector Retriever"
    VECTOR_CYPHER = "Vector Cypher Retriever"
    EMBEDDING = "Embedding-Based Retriever"
    
    # Keyword-Based
    KEYWORD = "Keyword-Based Retriever"
    CUSTOM = "Custom Retriever"
    
    # Graph-Based
    GRAPH_QL = "GraphQl-Based Retriever"
    GRAPH = "Graph-Based Retriever"
    
    # Contextual
    CONTEXTUAL = "Contextual Based Retriever"
    ENTITY = "Entity Based Retriever"
    
    # Hybrid/Specialized
    HYBRID = "Hybrid Retriever"
    TEXT2CYPHER = "Text2Cypher Retriever"
    RECOMMENDATION = "Recommendation Retriever"
    
    # Pattern/Temporal
    PATTERN = "Pattern Based Retriever"
    TEMPORAL = "Temporal Based Retriever"


