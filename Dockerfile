# Multi-stage Dockerfile for DataDynamos Healthcare Claims Platform
# Stage 1: Backend FastAPI Application
FROM python:3.12-slim as backend

# Install system dependencies for OpenCV and Tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app/backend

# Copy backend dependencies and source code
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --extra ocr --extra langextract --extra agent

COPY backend/ ./

EXPOSE 8000

ENV PYTORCH_ENABLE_MPS_FALLBACK=1
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
