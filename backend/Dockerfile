# Production Dockerfile for FastAPI Backend Deployment on Render
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

EXPOSE 8000

# Run Uvicorn server bound to 0.0.0.0 and dynamic PORT assigned by Render
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
