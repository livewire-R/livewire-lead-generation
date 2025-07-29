# -------------------------------------------------------------------------------------------------
# LEED.io Backend · Dockerfile (Backend Root Directory Version)
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

# Copy requirements (now from backend directory root)
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code (src is now directly accessible)
COPY src ./src

# Environment configuration
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

# Start command
CMD ["/bin/sh", "-c", "gunicorn -w 4 -b 0.0.0.0:${PORT} src.main:app"]
