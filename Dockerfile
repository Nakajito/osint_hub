# Stage 1: Builder
FROM python:3.12-slim AS builder
# Aprovechamos uv al máximo
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    gcc

COPY pyproject.toml uv.lock ./

# Usamos uv para generar los wheels directamente, es más rápido y seguro
RUN uv export --format requirements-txt > requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime
WORKDIR /app

# Agregamos libgl1 y libglib2.0-0, esenciales para OpenCV/DeepFace
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

# Creamos los directorios antes de copiar el código para asegurar permisos
RUN mkdir -p /app/staticfiles /app/media /app/data/search_results /home/appuser/.deepface \
    && chown -R appuser:appuser /app /home/appuser/.deepface

COPY --chown=appuser:appuser . .

USER appuser

# Exponemos el puerto que usa Gunicorn según tus logs
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]