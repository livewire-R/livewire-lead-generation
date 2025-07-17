# LEED.io Backend Dockerfile - Railway Optimized
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port (Railway sets this automatically)
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/health || exit 1

# Start command - using python -m for better module resolution
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "1", "--timeout", "120", "--worker-class", "sync", "src.main:app"]

