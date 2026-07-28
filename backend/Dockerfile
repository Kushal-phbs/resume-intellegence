# =============================================================================
# Stage 1 — Build dependencies
# =============================================================================
FROM python:3.12-slim AS builder

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

WORKDIR /build

# Install system build dependencies required by some Python packages
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  gcc \
  libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Copy only the dependency manifests so Docker can cache this layer
COPY requirements.txt .

# Install dependencies into a local "site-packages" directory so the final
# stage can copy them without bringing in build tools.
RUN pip install --no-cache-dir \
  --target=/build/deps \
  -r requirements.txt


# =============================================================================
# Stage 2 — Runtime image
# =============================================================================
FROM python:3.12-slim AS runtime

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONPATH=/app

# Install only runtime system libraries (no build tools)
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  libpq5 \
  && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group for running the application
RUN groupadd --system --gid 1001 app && \
  useradd --system --uid 1001 --gid app --no-create-home --shell /usr/sbin/nologin app

# Create the application directory and the uploads directory
RUN mkdir -p /app/uploads/resumes && \
  chown -R app:app /app

WORKDIR /app

# Copy pre-built dependencies from the builder stage
COPY --from=builder --chown=app:app /build/deps /app/deps

# Copy the application code
COPY --chown=app:app alembic.ini .
COPY --chown=app:app alembic/ ./alembic/
COPY --chown=app:app app/ ./app/

# Make the installed dependencies importable by adding them to sys.path
ENV PYTHONPATH=/app/deps:/app

# Switch to the non-root user
USER app

# Healthcheck — uses the lightweight /live endpoint which does not require
# any external dependencies.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/live')" || exit 1

# Expose the application port
EXPOSE 8000

# Production startup — Uvicorn with:
#   - workers controlled by UVICORN_WORKERS env var (default 4)
#   - graceful shutdown via SIGTERM
#   - no reload (production)
#   - no access log (structured logging is used instead)
CMD python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-4} --no-access-log