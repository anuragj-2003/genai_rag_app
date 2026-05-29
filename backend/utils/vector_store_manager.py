import os
import uuid
from pinecone import Pinecone

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "pcsk_ARp22_HtiWPrLqQWdfLirtFS3sfzd7fN8fPpJzve4tzSFjWUERphoYB4cWsdLJZ2bTLht")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "quickstart-py")

# Initialize Pinecone Client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create the index if it doesn't exist (using integrated embeddings model)
if not pc.has_index(INDEX_NAME):
    try:
        pc.create_index_for_model(
            name=INDEX_NAME,
            cloud="aws",
            region="us-east-1",
            embed={
                "model": "llama-text-embed-v2",
                "field_map": {"text": "chunk_text"}
            }
        )
    except Exception as e:
        print(f"Error creating Pinecone index: {e}")

# Get index handle
pinecone_index = pc.Index(INDEX_NAME)

class MockDocument:
    def __init__(self, page_content: str, metadata: dict):
        self.page_content = page_content
        self.metadata = metadata

class VectorStoreManager:
    def __init__(self):
        # We no longer need local HuggingFace embeddings since Pinecone embeds server-side!
        self.embeddings = None
        self.vector_store = pinecone_index

    def get_embeddings(self):
        # Dummy method to avoid breaking old references if any
        return None

    def create_vector_store(self, documents):
        """
        Clears the namespace and adds the documents to the Pinecone index.
        """
        if not documents:
            return None
        
        try:
            # Delete all documents in namespace "documents" to start fresh
            pinecone_index.delete(delete_all=True, namespace="documents")
        except Exception:
            pass # Namespace might not exist yet
            
        self.add_documents(documents)
        return self.vector_store

    def add_documents(self, documents):
        """
        Adds LlamaIndex Document objects to the namespace "documents" in Pinecone.
        """
        if not documents:
            return

        records = []
        for doc in documents:
            doc_id = str(uuid.uuid4())
            text = doc.text if hasattr(doc, 'text') else doc.get_content()
            
            # The record field mapped by field_map is "chunk_text"
            record = {
                "_id": doc_id,
                "chunk_text": text,
                "source": doc.metadata.get("source", ""),
                "page": str(doc.metadata.get("page", "1"))
            }
            records.append(record)

        # Upsert records in batches of 100
        for i in range(0, len(records), 100):
            try:
                pinecone_index.upsert_records(
                    namespace="documents",
                    records=records[i:i+100]
                )
            except Exception as e:
                print(f"Error upserting to Pinecone: {e}")

    def add_to_memory(self, query, answer):
        """
        Adds a query-answer pair to the namespace "memory" in Pinecone.
        """
        doc_id = str(uuid.uuid4())
        record = {
            "_id": doc_id,
            "chunk_text": query,
            "answer": answer
        }
        try:
            pinecone_index.upsert_records(
                namespace="memory",
                records=[record]
            )
        except Exception as e:
            print(f"Error saving to Pinecone memory: {e}")

    def check_memory(self, query, threshold=0.3):
        """
        Checks namespace "memory" for a semantically similar query.
        Returns the cached answer if found.
        """
        try:
            results = pinecone_index.search(
                namespace="memory",
                inputs={"text": query},
                top_k=1,
                fields=["chunk_text", "answer"]
            )
            
            hits = []
            if hasattr(results, "result") and hasattr(results.result, "hits"):
                hits = results.result.hits
            elif hasattr(results, "matches"):
                hits = results.matches
            elif isinstance(results, dict) and "result" in results and "hits" in results["result"]:
                hits = results["result"]["hits"]
                
            if not hits:
                return None
                
            hit = hits[0]
            score = hit.get("score") if isinstance(hit, dict) else getattr(hit, "score", 0.0)
            fields = hit.get("fields") if isinstance(hit, dict) else getattr(hit, "fields", {})
            
            # Cosine similarity threshold (score > 0.7 for high similarity)
            if score > 0.7:
                return fields.get("answer")
        except Exception as e:
            print(f"Error checking Pinecone memory: {e}")
        return None

    def similarity_search(self, query, k=4):
        """
        Performs a similarity search in namespace "documents".
        Returns a list of compatible MockDocument objects.
        """
        try:
            results = pinecone_index.search(
                namespace="documents",
                inputs={"text": query},
                top_k=k,
                fields=["chunk_text", "source", "page"]
            )
            
            hits = []
            if hasattr(results, "result") and hasattr(results.result, "hits"):
                hits = results.result.hits
            elif hasattr(results, "matches"):
                hits = results.matches
            elif isinstance(results, dict) and "result" in results and "hits" in results["result"]:
                hits = results["result"]["hits"]
                
            docs = []
            for hit in hits:
                fields = hit.get("fields") if isinstance(hit, dict) else getattr(hit, "fields", {})
                text = fields.get("chunk_text", "")
                source = fields.get("source", "")
                page = fields.get("page", "1")
                
                docs.append(MockDocument(
                    page_content=text,
                    metadata={
                        "source": source,
                        "page": page
                    }
                ))
            return docs
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []
