# Stage 1: Build Python wheels
FROM python:3.12-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime
WORKDIR /app

# Install ExifTool and libpq
RUN apt-get update && apt-get install -y --no-install-recommends \
    libimage-exiftool-perl libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache /wheels/*

# Non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

# Copy source
COPY --chown=appuser:appuser . .

# Persistent dirs
RUN mkdir -p /app/staticfiles /app/media /app/data/search_results \
    && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:8000/robots.txt || exit 1

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
