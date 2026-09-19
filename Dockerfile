# Root Production Dockerfile for FastAPI Backend Deployment
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements supporting either root context or backend context
COPY requirements.txt* backend/requirements.txt* /app/temp_req/
RUN if [ -f /app/temp_req/requirements.txt ]; then \
        pip install --no-cache-dir -r /app/temp_req/requirements.txt; \
    elif [ -f /app/temp_req/backend/requirements.txt ]; then \
        pip install --no-cache-dir -r /app/temp_req/backend/requirements.txt; \
    fi && rm -rf /app/temp_req

# Copy application source code supporting either context
COPY . /app/temp_src
RUN if [ -d /app/temp_src/backend/app ]; then \
        cp -r /app/temp_src/backend/* /app/; \
    else \
        cp -r /app/temp_src/* /app/; \
    fi && rm -rf /app/temp_src

EXPOSE 8000

CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
