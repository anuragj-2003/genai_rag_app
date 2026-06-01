"""
markdown_converter.py — Convert PDF/DOCX/PPTX/HTML → clean Markdown.
OCR fallback for scanned/image-only PDFs.
Heading-aware chunker for semantically coherent retrieval.
"""

import os
import re
from markitdown import MarkItDown
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

_md = MarkItDown()


def convert_to_markdown(file_path: str, mime_type: str) -> str:
    """
    Convert uploaded file to clean Markdown.
    For PDFs: detect scanned pages (low char count) → OCR fallback.
    Returns empty string on unrecoverable failure.
    """
    if "pdf" in mime_type:
        try:
            doc = fitz.open(file_path)
            total_chars = sum(len(page.get_text()) for page in doc)
            doc.close()
            if total_chars < 100:  # scanned PDF — image-only
                return _ocr_pdf(file_path)
        except Exception:
            return _ocr_pdf(file_path)

    try:
        result = _md.convert(file_path)
        md = (result.text_content or "").strip()
        if not md:
            if "pdf" in mime_type:
                return _ocr_pdf(file_path)
            return ""
        return md
    except Exception as e:
        if "pdf" in mime_type:
            return _ocr_pdf(file_path)
        print(f"[MarkItDown] Conversion failed for {file_path}: {e}")
        return ""


def _ocr_pdf(file_path: str) -> str:
    """
    Rasterize each PDF page at 200 dpi, run Tesseract OCR, join with '---' separators.
    """
    try:
        doc = fitz.open(file_path)
        pages = []
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img)
            if text.strip():
                pages.append(text.strip())
        doc.close()
        return "\n\n---\n\n".join(pages) if pages else ""
    except Exception as e:
        print(f"[OCR] Failed: {e}")
        return ""


def chunk_markdown(md: str, max_chars: int = 600) -> list[str]:
    """
    Heading-aware chunker:
    1. Split on ## headings (section boundaries).
    2. Sub-split large sections on paragraph breaks (\\n\\n).
    3. Never use fixed character-window splitting on raw prose.
    4. Filter out chunks < 50 chars (noise).
    """
    if not md.strip():
        return []

    # Split on ## headers (keep header with its section)
    sections = re.split(r'\n(?=##\s)', md)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        if len(section) <= max_chars:
            if len(section) > 50:
                chunks.append(section)
        else:
            # Sub-split on paragraph breaks
            paragraphs = section.split('\n\n')
            current: list[str] = []
            buf_len = 0

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                if buf_len + len(para) > max_chars and current:
                    chunk = '\n\n'.join(current).strip()
                    if len(chunk) > 50:
                        chunks.append(chunk)
                    current = []
                    buf_len = 0
                current.append(para)
                buf_len += len(para) + 2  # +2 for '\n\n'

            if current:
                chunk = '\n\n'.join(current).strip()
                if len(chunk) > 50:
                    chunks.append(chunk)

    return chunks
