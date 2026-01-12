from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from routers.auth import get_current_user
from models.auth import User
from state import vector_store
from utils.document_processor import process_uploaded_file
import shutil
import os

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        # process_uploaded_file expects a Streamlit UploadedFile-like object or needs adaptation.
        # It reads .name and .getvalue(). FastAPI UploadFile has .filename and .file (spooled temp file).
        
        # We need to adapt FastAPI UploadFile to what process_uploaded_file expects via duck typing.
        class AdaptedFile:
            def __init__(self, f: UploadFile):
                self.name = f.filename
                self.file = f.file
                
            def getvalue(self):
                self.file.seek(0)
                return self.file.read()
                
        adapted = AdaptedFile(file)
        
        docs = process_uploaded_file(adapted)
        
        if not docs:
            raise HTTPException(status_code=400, detail="Could not extract text from file.")
            
        vector_store.add_documents(docs)
        
        return {"filename": file.filename, "status": "processed", "chunks": len(docs)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
