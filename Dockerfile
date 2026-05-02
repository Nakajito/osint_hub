# Stage 1: Builder con uv
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /build

# Dependencias para compilar Pillow, Postgres y OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libjpeg-dev zlib1g-dev libpng-dev gcc

COPY pyproject.toml uv.lock ./
# Generamos los wheels con uv para asegurar consistencia
RUN uv export --format requirements-txt > requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim AS runtime
WORKDIR /app

# Librerías necesarias para Pillow, OpenCV y ExifTool
RUN apt-get update && apt-get install -y --no-install-recommends \
    libimage-exiftool-perl \
    libpq5 \
    libjpeg62-turbo \
    libpng16-16 \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache /wheels/*

RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser
COPY --chown=appuser:appuser . .

# Asegurar directorios de static y media con permisos
RUN mkdir -p /app/staticfiles /app/media /app/data/search_results \
    && chown -R appuser:appuser /app

USER appuser
ENTRYPOINT ["/app/entrypoint.sh"]