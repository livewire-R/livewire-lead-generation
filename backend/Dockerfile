FROM python:3.11-slim AS base

# Install dependencies for psycopg2 and general build
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY backend/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY backend/src ./src

# Set env vars
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

# Use shell to expand $PORT
CMD ["/bin/sh", "-c", "gunicorn -w 4 -b 0.0.0.0:${PORT} src.main:app"]
