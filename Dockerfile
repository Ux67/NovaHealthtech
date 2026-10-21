# ==============================================================================
# Nova Healthtech - Production Dockerfile
# Multi-stage security profile, non-root execution, and persistent volume ready
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered terminal logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    FLASK_DEBUG=False \
    DATABASE_PATH=/data/nova_health.db

# Install minimal system dependencies (curl is used for Docker HEALTHCHECK)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user and group
RUN groupadd -g 10001 nova && \
    useradd -u 10001 -g nova -s /bin/bash -m novauser

# Establish application directory and persistent volume mount point
# Establish application directory and persistent volume mount point
WORKDIR /app
ENV PYTHONPATH="/app/backend:/app"

RUN mkdir -p /data && chown -R novauser:nova /data /app

# Copy dependency manifest first to take advantage of Docker layer caching
COPY --chown=novauser:nova backend/requirements.txt ./backend/requirements.txt

# Install dependencies in non-cache mode
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend, frontend, and Gunicorn configuration
COPY --chown=novauser:nova backend ./backend
COPY --chown=novauser:nova frontend ./frontend
COPY --chown=novauser:nova gunicorn.conf.py ./gunicorn.conf.py

# Switch to unprivileged user
USER novauser

# Expose default HTTP port
EXPOSE 5000

# Container Healthcheck (polls the /api/health endpoint every 30s)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Execute WSGI server with production Gunicorn configuration
CMD ["gunicorn", "--config", "gunicorn.conf.py", "backend.app:app"]