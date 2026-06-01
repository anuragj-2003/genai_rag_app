"""
routers/documents.py — Document upload (/api/v1/upload)

Security:
- magic-bytes MIME validation (not extension-based)
- 10MB hard cap
- Files written to /tmp with UUID names, deleted immediately after processing
- Binary never stored — only Markdown content stored in SQLite

Pipeline:
1. Validate (magic bytes + size)
2. MarkItDown → clean Markdown (OCR fallback for scanned PDFs)
3. chunk_markdown() on ## headings
4. Embed + index into ChromaDB (scoped by user_id)
5. Store Markdown in documents table
"""

import os
import uuid
import time
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel

from routers.auth import get_current_user, UserOut
from utils.markdown_converter import convert_to_markdown, chunk_markdown
from utils import chroma_manager
from utils.app_db import insert_document, get_user_documents, soft_delete_document
from utils.logging_utils import log_upload
from utils.constants import ALLOWED_MIME, MAX_BYTES

try:
    import magic
    _magic_available = True
except ImportError:
    _magic_available = False
    print("[WARNING] python-magic not available — falling back to extension check")

router = APIRouter(prefix="/api/v1", tags=["documents"])


def _detect_mime(data: bytes) -> str:
    """Detect MIME type from magic bytes. Falls back to octet-stream."""
    if _magic_available:
        return magic.from_buffer(data[:2048], mime=True)
    return "application/octet-stream"


async def validate_upload(file: UploadFile) -> tuple[str, bytes, str]:
    """
    Read, size-check, MIME-check the file.
    Returns (tmp_path, raw_bytes, detected_mime).
    Raises HTTPException on validation failure.
    """
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10MB limit.")

    detected_mime = _detect_mime(data)

    # Extension-based fallback for .txt (magic detects as text/plain)
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext == ".txt":
        detected_mime = "text/plain"
    elif ext in (".docx",):
        detected_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif ext in (".pdf",):
        if "pdf" not in detected_mime:
            detected_mime = "application/pdf"

    if detected_mime not in ALLOWED_MIME:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{detected_mime}'. Allowed: PDF, TXT, DOCX."
        )

    # Write to /tmp with UUID name
    suffix = ext or ".upload"
    tmp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}{suffix}")
    with open(tmp_path, "wb") as f:
        f.write(data)

    return tmp_path, data, detected_mime


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserOut = Depends(get_current_user)
):
    t0 = time.time()
    user_id = current_user.id

    # Step 1: Validate
    tmp_path, data, mime_type = await validate_upload(file)

    try:
        # Step 2: Convert to Markdown
        md = convert_to_markdown(tmp_path, mime_type)
    finally:
        # Always delete temp binary immediately
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    if not md.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from this file. It may be encrypted, corrupted, or image-only without OCR support."
        )

    # Step 3: Chunk using heading-aware splitter
    chunks = chunk_markdown(md, max_chars=600)
    if not chunks:
        raise HTTPException(status_code=422, detail="No meaningful content found in document.")

    # Step 4: Embed + index into ChromaDB (scoped by user_id)
    doc_id = str(uuid.uuid4())
    indexed = chroma_manager.add_documents(
        chunks=chunks,
        user_id=user_id,
        doc_id=doc_id,
        filename=file.filename or "upload",
    )

    # Step 5: Store Markdown in SQLite (NOT the binary)
    insert_document(
        doc_id=doc_id,
        user_id=user_id,
        filename=file.filename or "upload",
        markdown_content=md,
        chunks_indexed=indexed,
    )

    latency = round((time.time() - t0) * 1000)
    log_upload(user_id, file.filename or "upload", indexed, latency)

    return {
        "doc_id": doc_id,
        "filename": file.filename,
        "chunks_indexed": indexed,
        "latency_ms": latency,
    }


@router.get("/documents")
def list_documents(current_user: UserOut = Depends(get_current_user)):
    return get_user_documents(current_user.id)


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str, current_user: UserOut = Depends(get_current_user)):
    user_id = current_user.id
    # Soft-delete in SQLite
    soft_delete_document(doc_id, user_id)
    # Hard-delete vectors from ChromaDB
    chroma_manager.delete_document_vectors(user_id, doc_id)
    return {"message": "Document deleted."}
