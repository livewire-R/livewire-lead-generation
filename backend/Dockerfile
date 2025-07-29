# -------------------------------------------------------------------------------------------------
# LEED.io Backend · Dockerfile (Repository Root Version)
# -------------------------------------------------------------------------------------------------

FROM python:3.11-slim AS base

# System packages
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements from backend folder
COPY backend/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code from backend/src to /app/src
COPY backend/src ./src

# Environment configuration
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

# Start command (using src.main since we copied src to /app/src)
CMD ["/bin/sh", "-c", "gunicorn -w 4 -b 0.0.0.0:${PORT} src.main:app"]
