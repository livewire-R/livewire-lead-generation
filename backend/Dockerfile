# LEED.io Backend - Emergency Dockerfile (Bypasses requirements.txt)
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages directly (bypasses requirements.txt issues)
RUN pip install --no-cache-dir \
    Flask==3.0.0 \
    Flask-CORS==4.0.0 \
    gunicorn==21.2.0 \
    requests==2.31.0 \
    psycopg2-binary==2.9.9

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE $PORT

# Start command
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "1", "--timeout", "120", "src.main:app"]

