# -------------------------------------------------------------------------------------------------
# LEED.io Backend · Dockerfile
# -------------------------------------------------------------------------------------------------
# • Builds a minimal, secure Python 3.11 image
# • Installs system libs required for psycopg2-binary
# • Installs all Python deps from backend/requirements.txt
# • Copies only the backend code (lower Docker context, faster builds)
# • Uses Gunicorn with shell form so $PORT expands at runtime inside Railway
# • Defaults to 8080; Railway automatically sets PORT env-var on container start
# -------------------------------------------------------------------------------------------------

# ---- 1. Base image ----------------------------------------------------------------------------- #
FROM python:3.11-slim AS base

# ---- 2. System packages ------------------------------------------------------------------------ #
# gcc & libpq-dev are required to build psycopg2-binary wheels on slim images[3][16]
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# ---- 3. Runtime directories -------------------------------------------------------------------- #
WORKDIR /app

# ---- 4. Dependency installation --------------------------------------------------------------- #
# Copy only requirements to leverage Docker layer caching
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- 5. Copy application code ------------------------------------------------------------------ #
# We copy the backend code under /app backend/src → /app/src
COPY backend/src ./src
COPY backend/railway.toml ./       # Optional: keep config-as-code inside image

# ---- 6. Environment configuration -------------------------------------------------------------- #
# Prevent Python from buffering stdout/stderr (safer logging on Railway)
ENV PYTHONUNBUFFERED=1
# Provide a sane default; Railway overrides PORT at runtime[6][37]
ENV PORT=8080

# ---- 7. Network exposure ----------------------------------------------------------------------- #
# EXPOSE MUST be a literal integer at build time—variables are illegal[30][37]
# We expose 8080 (default) purely for documentation purposes. Actual routing
# inside Railway uses the runtime $PORT env-var.
EXPOSE 8080

# ---- 8. Application start command -------------------------------------------------------------- #
# Use “shell form” via sh -c so $PORT expands inside the container at runtime[8][10].
# Gunicorn entry-point: four workers, pre-fork model, binds to 0.0.0.0
CMD ["/bin/sh", "-c", "gunicorn -w 4 -b 0.0.0.0:${PORT} src.main:app"]
