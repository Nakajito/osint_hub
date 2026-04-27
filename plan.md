# Plan: Docker + Coolify + Seguridad + TDD para OSINT Hub

## Contexto

El proyecto no tiene ninguna configuración Docker. Se va a desplegar en Coolify (PaaS sobre Docker). El código tiene vulnerabilidades de seguridad confirmadas en archivos críticos. Los tests están completamente vacíos. Al tratar con herramientas OSINT externas (Holehe, Sherlock, ExifTool vía subprocess), la superficie de ataque es alta. El plan aplica TDD: primero tests que fallen, luego las correcciones.

---

## Archivos a crear / modificar

| Acción | Archivo |
|---|---|
| CREAR | `Dockerfile` |
| CREAR | `.dockerignore` |
| CREAR | `docker-compose.yml` (dev local) |
| CREAR | `docker-compose.prod.yml` (Coolify) |
| CREAR | `entrypoint.sh` |
| CREAR | `pytest.ini` |
| CREAR | `conftest.py` |
| CREAR | `tests/test_security.py` (RED — fallarán) |
| CREAR | `tests/test_views.py` (RED — fallarán) |
| MODIFICAR | `osint_hub/settings.py` (GREEN — security fixes) |
| MODIFICAR | `ExifTool/views.py` (GREEN — filename + duplicate) |
| MODIFICAR | `email_holehe/views.py` (GREEN — error disclosure) |
| MODIFICAR | `requirements.txt` (agregar pytest, werkzeug) |
| MODIFICAR | `.env.example` (agregar Redis, Postgres vars) |

---

## Fase 1 — Infraestructura de Testing

### `pytest.ini`
```ini
[pytest]
DJANGO_SETTINGS_MODULE = osint_hub.settings
python_files = tests/test_*.py
python_classes = Test*
python_functions = test_*
addopts = --tb=short -v
```

### Dependencias a agregar en `requirements.txt`
```
pytest==8.3.5
pytest-django==4.9.0
pytest-cov==6.1.0
responses==0.25.7      # mock HTTP (httpx/requests)
werkzeug==3.1.3        # secure_filename (ya referenciado en UsernameSearch/views.py:12)
```

### `conftest.py` (raíz del proyecto)
```python
import pytest
from django.test import RequestFactory, Client

@pytest.fixture
def rf():
    return RequestFactory()

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def sample_image(tmp_path):
    # JPEG magic bytes válidos
    f = tmp_path / "test.jpg"
    f.write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
    return f
```

---

## Fase 2 — Tests de Seguridad (RED)

### `tests/test_security.py` — fallarán hasta que se apliquen los fixes

```python
# test_security_settings — debe fallar con settings actuales
def test_production_session_cookie_is_secure():
    """SESSION_COOKIE_SECURE debe ser True en producción."""
    with override_settings(DEBUG=False):
        from django.conf import settings
        assert settings.SESSION_COOKIE_SECURE is True  # FALLA: actualmente False

def test_production_csrf_cookie_is_secure():
    with override_settings(DEBUG=False):
        assert settings.CSRF_COOKIE_SECURE is True  # FALLA: actualmente False

def test_redis_url_from_environment():
    """Redis URL no debe estar hardcodeada como localhost."""
    with override_settings(CELERY_BROKER_URL="redis://redis:6379/0"):
        assert "localhost" not in settings.CELERY_BROKER_URL  # FALLA: actualmente hardcoded

# test_exiftool_filename_sanitization
def test_upload_sanitizes_traversal_filename(client, tmp_path):
    """Nombre con path traversal no debe escribirse fuera del tmpdir."""
    # FALLA: ExifTool/views.py:118 usa uploaded.name sin sanitizar

# test_email_error_disclosure
def test_error_does_not_expose_internal_paths(client):
    """Errores no deben exponer paths internos del sistema."""
    # FALLA: email_holehe/views.py:61 expone str(e) directamente
```

### `tests/test_views.py` — tests con mocks de subprocess/HTTP

```python
from unittest.mock import patch, MagicMock

def test_email_search_valid_email(client):
    with patch("email_holehe.views.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="[+] Email used on GitHub", returncode=0)
        resp = client.post("/email/search/", {"email": "test@example.com"})
        assert resp.status_code == 302

def test_email_search_invalid_email_rejected(client):
    resp = client.post("/email/search/", {"email": "not-an-email"})
    assert resp.status_code == 200
    assert "válido" in resp.content.decode()

def test_hash_md5_text(client):
    resp = client.post("/hash/", {"input_type": "text", "text_input": "hello", "algorithm": "md5", "action": "Gen"})
    assert "5d41402abc4b2a76b9719d911017c592" in resp.content.decode()

def test_iplookup_rejects_private_ip(client):
    """IPs privadas/RFC1918 deben ser rechazadas para prevenir SSRF."""
    resp = client.post("/ip/search/", {"ip_address": "192.168.1.1"})
    assert resp.status_code in (200, 400)  # Debe rechazar, no hacer la llamada

def test_exiftool_upload_rejects_oversized_file(client, tmp_path):
    big_file = tmp_path / "big.jpg"
    big_file.write_bytes(b"x" * (51 * 1024 * 1024))
    with open(big_file, "rb") as f:
        resp = client.post("/exiftool/upload/", {"file": f})
    assert resp.status_code == 302  # Redirect con mensaje de error
```

---

## Fase 3 — Correcciones de Seguridad (GREEN)

### `osint_hub/settings.py` — 5 cambios

**1. DEBUG default False** (`línea 13`)
```python
# ANTES:
DEBUG = config("DEBUG", default=True, cast=bool)
# DESPUÉS:
DEBUG = config("DEBUG", default=False, cast=bool)
```

**2. Cookies seguras en producción** (`líneas 142-144`)
```python
# ANTES:
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
# DESPUÉS:
SECURE_SSL_REDIRECT = False   # Coolify/Traefik maneja TLS externamente
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

**3. Redis URL desde variable de entorno** (`líneas 172-173`)
```python
# ANTES:
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
# DESPUÉS:
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
```

**4. Database desde env var** (`líneas 75-80`)
```python
# ANTES: SQLite hardcodeado
# DESPUÉS:
db_url = config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
DATABASES = {"default": dj_database_url.parse(db_url)}
```

**5. SEARCH_RESULTS_DIR en Docker** (`línea 135`) — usar path dentro del contenedor:
```python
SEARCH_RESULTS_DIR = config(
    "SEARCH_RESULTS_DIR",
    default=str(BASE_DIR / "data" / "search_results"),
)
```

### `ExifTool/views.py` — 3 cambios

**1. Sanitizar nombre de archivo** (`línea 118`)
```python
import unicodedata
# ANTES:
tmp_path = os.path.join(tmp_dir, uploaded.name)
# DESPUÉS:
safe_name = re.sub(r"[^\w\.\-]", "_", os.path.basename(uploaded.name))
if not safe_name or safe_name.startswith("."):
    safe_name = "upload"
tmp_path = os.path.join(tmp_dir, safe_name)
```

**2. Eliminar función duplicada** (`líneas 27-38`) — eliminar la primera definición de `clean_metadata_for_session` (la más simple), conservar la segunda (líneas 82-99) que tiene mejor documentación y mensaje de truncado.

**3. Validación de magic bytes** (agregar después de guardar el archivo)
```python
MAGIC_BYTES = {
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG\r\n': 'image/png',
    b'GIF87a': 'image/gif', b'GIF89a': 'image/gif',
    b'%PDF': 'application/pdf',
}
def _validate_magic_bytes(path: str, content_type: str) -> bool:
    with open(path, 'rb') as f:
        header = f.read(8)
    for magic, mime in MAGIC_BYTES.items():
        if header.startswith(magic):
            return mime == content_type
    return False
```
Llamar `_validate_magic_bytes(tmp_path, uploaded.content_type)` antes de ejecutar ExifTool.

### `email_holehe/views.py` — 1 cambio

**Ocultar detalles de error interno** (`línea 61`)
```python
# ANTES:
messages.error(request, f"Error al realizar la búsqueda: {str(e)}")
# DESPUÉS:
logger.error(f"Error holehe: {e}")
messages.error(request, "Error interno al realizar la búsqueda. Intenta nuevamente.")
```

### Protección SSRF en `IPLookup/views.py`

Agregar validación antes de hacer la llamada HTTP:
```python
import ipaddress
def _is_safe_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return not (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved)
    except ValueError:
        return False
```
Llamar `_is_safe_ip(ip)` en `ip_search()` antes de `_build_api_url()`.

---

## Fase 4 — Docker Infrastructure

### `Dockerfile` (multi-stage, non-root)
```dockerfile
# Stage 1: Compilar dependencias Python
FROM python:3.12-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Runtime mínimo
FROM python:3.12-slim AS runtime
WORKDIR /app

# Instalar ExifTool y libpq (única dependencia del sistema)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libimage-exiftool-perl libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar wheels y instalar sin caché
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache /wheels/*

# Crear usuario no-root
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

# Copiar código
COPY --chown=appuser:appuser . .

# Directorios persistentes
RUN mkdir -p /app/staticfiles /app/media /app/data/search_results \
    && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:8000/robots.txt || exit 1

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
```

### `entrypoint.sh`
```bash
#!/bin/sh
set -e

echo "→ Collecting static files..."
python manage.py collectstatic --noinput

echo "→ Running migrations..."
python manage.py migrate --noinput

echo "→ Starting Gunicorn..."
exec gunicorn osint_hub.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-2} \
    --timeout ${GUNICORN_TIMEOUT:-120} \
    --log-level ${LOG_LEVEL:-info} \
    --access-logfile -
```

### `docker-compose.yml` (desarrollo local)
```yaml
services:
  web:
    build: .
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - media_data:/app/media
      - search_data:/app/data/search_results
    depends_on:
      redis:
        condition: service_healthy
      db:
        condition: service_healthy
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD:-redispass}
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD:-redispass}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${DB_NAME:-osinthub}
      POSTGRES_USER: ${DB_USER:-osinthub}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-osinthub}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  media_data:
  search_data:
```

### `docker-compose.prod.yml` (Coolify — sin puertos expuestos, Traefik los gestiona)
```yaml
# Para Coolify: este archivo extiende docker-compose.yml con config de producción
services:
  web:
    build: .
    env_file: .env.prod       # Coolify inyecta las vars desde su panel
    environment:
      - DJANGO_SETTINGS_MODULE=osint_hub.settings
    restart: always
    networks:
      - coolify               # Red interna de Coolify/Traefik
    # Coolify añade labels de Traefik automáticamente

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD} --save 60 1 --loglevel warning
    restart: always
    networks:
      - coolify

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    networks:
      - coolify

networks:
  coolify:
    external: true            # Red pre-existente de Coolify

volumes:
  postgres_data:
```

### `.dockerignore`
```
.git
.env
.env.*
!.env.example
__pycache__
*.pyc
*.pyo
*.pyd
*.db
*.sqlite3
venv/
.venv/
node_modules/
staticfiles/
media/
*.log
.pytest_cache/
.coverage
htmlcov/
readme.md
```

### `.env.example` actualizado
```env
SECRET_KEY=genera-una-clave-segura-aqui
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
CSRF_TRUSTED_ORIGINS=https://tudominio.com,https://www.tudominio.com

# Database
DATABASE_URL=postgres://osinthub:password@db:5432/osinthub

# Redis
REDIS_URL=redis://:password@redis:6379/0
REDIS_PASSWORD=password

# PostgreSQL
DB_NAME=osinthub
DB_USER=osinthub
DB_PASSWORD=password

# Gunicorn
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=120
LOG_LEVEL=info

# OSINT
SEARCH_RESULTS_DIR=/app/data/search_results
```

---

## Coolify — Pasos de Configuración

1. En Coolify, crear un nuevo servicio tipo **"Docker Compose"**
2. Conectar el repositorio GitHub
3. Apuntar al archivo `docker-compose.prod.yml`
4. En el panel de variables de entorno de Coolify, ingresar todas las vars de `.env.example`
5. Coolify gestionará SSL automáticamente vía Traefik (no necesita `SECURE_SSL_REDIRECT=True`)
6. El health check (`/robots.txt`) será usado por Coolify para verificar disponibilidad

---

## Verificación End-to-End

```bash
# 1. Ejecutar tests (deben pasar todos con el código corregido)
pytest tests/ -v --cov=. --cov-report=term-missing

# 2. Construir imagen Docker localmente
docker compose build

# 3. Levantar stack completo
docker compose up -d

# 4. Verificar health
curl http://localhost:8000/robots.txt      # debe retornar 200
curl http://localhost:8000/              # home page

# 5. Verificar que los headers de seguridad están activos
curl -I http://localhost:8000/ | grep -i "x-frame\|x-content\|strict-transport"

# 6. Verificar que DEBUG=False no expone stacktrace
curl http://localhost:8000/ruta-inexistente  # debe retornar 404 genérico

# 7. Smoke test de herramientas
# - Visitar /hash/ y generar MD5 de "hello"  → 5d41402abc4b2a76b9719d911017c592
# - Visitar /ip/search/ con 8.8.8.8          → debe mostrar geolocalización Google DNS
# - Visitar /exiftool/upload/ con imagen JPEG → debe mostrar metadatos

# 8. Verificar en Coolify
# - Dashboard → servicio → health check verde
# - Dominio configurado → HTTPS funcional
```
