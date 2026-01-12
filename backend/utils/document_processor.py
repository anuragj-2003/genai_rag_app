import os
import tempfile
import pandas as pd
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def process_uploaded_file(uploaded_file):
    """
    Processes an uploaded file (PDF, DOCX, XLSX) and returns a list of LangChain Documents.
    
    Input:
        uploaded_file (UploadedFile): The file object from Streamlit uploader.
        
    Output:
        list: A list of LangChain Document objects with metadata (source, page).
    """
    if uploaded_file is None:
        return []

    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    documents = []

    # Create a temporary file to save the uploaded content because LangChain loaders often need a file path
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    try:
        if file_extension == ".pdf":
            loader = PyPDFLoader(tmp_file_path)
            documents = loader.load()
        elif file_extension == ".docx":
            loader = Docx2txtLoader(tmp_file_path)
            documents = loader.load()
            # Docx loader might not give page numbers, default to 1
            for doc in documents:
                doc.metadata["page"] = 1
        elif file_extension == ".xlsx" or file_extension == ".xls":
            # flexible handling for excel
            try:
                # First try pandas for a simpler text representation
                df = pd.read_excel(tmp_file_path)
                text_content = df.to_string()
                documents = [Document(page_content=text_content, metadata={"source": uploaded_file.name, "page": 1})]
            except Exception:
                # Fallback to loader
                loader = UnstructuredExcelLoader(tmp_file_path)
                documents = loader.load()
                for doc in documents:
                    if "page" not in doc.metadata:
                        doc.metadata["page"] = 1
        else:
            # Fallback for text files
            try:
                with open(tmp_file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                documents = [Document(page_content=text, metadata={"source": uploaded_file.name, "page": 1})]
            except Exception:
                pass
    finally:
        # Clean up temp file
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

    # Split text if we have documents
    if documents:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        split_docs = text_splitter.split_documents(documents)
        # Ensure source metadata is preserved/set
        for doc in split_docs:
            if "source" not in doc.metadata:
                doc.metadata["source"] = uploaded_file.name
            else:
                doc.metadata["source"] = f"{uploaded_file.name} - {doc.metadata.get('source', '')}"
        return split_docs
    
    return []
