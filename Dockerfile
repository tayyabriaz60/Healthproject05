FROM python:3.10-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install build dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY app ./app
COPY frontend ./frontend

# Expose FastAPI port
EXPOSE 8000

# Default environment variables (override in production)
ENV GEMINI_API_KEY="" \
    APP_NAME="Chatbot API" \
    APP_VERSION="1.0.0" \
    DEBUG="false"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

