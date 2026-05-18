# RxAccess AI — Production Dockerfile
FROM python:3.10-slim

# System dependencies: Tesseract OCR + Poppler for PDF
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p data/uploads data/chroma_db data/knowledge_base \
             data/synthetic models logs

# Initialize knowledge base on build
RUN python scripts/init_system.py && \
    python scripts/train_adherence_model.py

EXPOSE 8501

ENV PYTHONUNBUFFERED=1
ENV TESSERACT_PATH=tesseract
ENV POPPLER_PATH=/usr/bin

CMD ["streamlit", "run", "streamlit_app/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
