import os
import faiss
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.docstore.in_memory import InMemoryDocstore

from langchain_core.documents import Document

# Global variable to hold the vector store in memory for the session
# In a production app, you might want to persist this to disk.
# For this Streamlit app, we'll keep it simple or allow persistence.

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

class VectorStoreManager:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        self.vector_store = None # Documents from upload
        self.memory_store = None # Past query-answer pairs

    def create_vector_store(self, documents):
        """
        Creates a new FAISS vector store from the given documents.
        
        Input:
            documents (list): List of LangChain Document objects.
            
        Output:
            FAISS: The initialized vector store.
        """
        if not documents:
            return None
        
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        return self.vector_store

    def add_documents(self, documents):
        """
        Adds documents to the existing vector store. If none exists, creates one.
        
        Input:
            documents (list): List of LangChain Document objects.
        """
        if not documents:
            return

        if self.vector_store is None:
            self.create_vector_store(documents)
        else:
            self.vector_store.add_documents(documents)

    def add_to_memory(self, query, answer):
        """
        Adds a query-answer pair to the memory store.
        """
        doc = Document(page_content=query, metadata={"answer": answer})
        if self.memory_store is None:
            self.memory_store = FAISS.from_documents([doc], self.embeddings)
        else:
            self.memory_store.add_documents([doc])

    def check_memory(self, query, threshold=0.3):
        """
        Checks memory for a semantically similar query.
        Returns the cached answer if found and within threshold.
        """
        if self.memory_store is None:
            return None
            
        # similarity_search_with_score returns L2 distance (lower is better)
        docs_and_scores = self.memory_store.similarity_search_with_score(query, k=1)
        
        if not docs_and_scores:
            return None
            
        doc, score = docs_and_scores[0]
        # Heuristic: < 0.3 usually means very close meaning for MiniLM
        if score < threshold:
            return doc.metadata.get("answer")
        return None

    def get_retriever(self, search_type="similarity", k=4):
        """
        Returns a retriever object from the vector store.
        
        Input:
            search_type (str): Retrieval type (e.g., 'similarity', 'mmr').
            k (int): Number of documents to retrieve.
            
        Output:
            VectorStoreRetriever: The retriever object.
        """
        if self.vector_store is None:
            return None
        return self.vector_store.as_retriever(search_type=search_type, search_kwargs={"k": k})

    def similarity_search(self, query, k=4):
        """
        Performs a raw similarity search.
        
        Input:
            query (str): The search query.
            k (int): Number of documents to return.
            
        Output:
            list: List of matching Document objects.
        """
        if self.vector_store is None:
            return []
        return self.vector_store.similarity_search(query, k=k)

# Simple singleton pattern for the app session
if "vector_store_manager" not in os.environ:
    # Just a placeholder, actual instantiation happens in app state
    pass
