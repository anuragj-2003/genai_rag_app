FROM python:3.11-slim

# System dependencies: tesseract-ocr for OCR, libmagic1 for MIME detection
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libmagic1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cache layer)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# Create data directory
RUN mkdir -p /app/data /app/chroma_db

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
