from pathlib import Path
import os
from decouple import config
import dj_database_url


BASE_DIR = Path(__file__).resolve().parent.parent

# Usar variables de entorno
SECRET_KEY = config(
    "SECRET_KEY",
)
DEBUG = config("DEBUG", default=False, cast=bool)

# ALLOWED_HOSTS configurado desde variable de entorno
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=lambda v: [s.strip() for s in v.split(",")],
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_bootstrap5",
    "email_holehe",
    "ExifTool",
    "PhoneSearch",
    "UsernameSearch",
    "HashTool",
    "IPLookup",
    "InstagramSniffer",
    "django_celery_results",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Whitenoise para archivos estáticos
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "csp.middleware.CSPMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "osint_hub.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "osint_hub.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# settings.py

db_url = config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
DATABASES = {"default": dj_database_url.parse(db_url)}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # Para producción
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Configuración de Whitenoise para archivos estáticos
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Directory to persist username search results (outside project root by default).
# Can be overridden with an environment-specific absolute path via
# the SEARCH_RESULTS_DIR setting or env var when deploying.
SEARCH_RESULTS_DIR = config(
    "SEARCH_RESULTS_DIR",
    default=str(BASE_DIR / "data" / "search_results"),
)

# Configuración de seguridad para producción
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = False   # Traefik/Coolify handles TLS externally
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configuración de CSRF_TRUSTED_ORIGINS desde variable de entorno
csrf_trusted_origins_str = config("CSRF_TRUSTED_ORIGINS", default="")
if csrf_trusted_origins_str:
    CSRF_TRUSTED_ORIGINS = [url.strip() for url in csrf_trusted_origins_str.split(",")]
else:
    CSRF_TRUSTED_ORIGINS = []

# 2. Configura los proxies de seguridad (necesario para Nginx/DigitalOcean)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Configurar path a ExifTool
EXIFTOOL_PATH = "/usr/bin/exiftool"  # Ruta por defecto en Ubuntu

if not os.path.exists(EXIFTOOL_PATH):
    EXIFTOOL_PATH = "/usr/local/bin/exiftool"  # Ruta alternativa


# Celery Configuration
REDIS_URL = config("REDIS_URL", default="redis://redis:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos
CELERY_RESULT_EXPIRES = 3600  # 1 hora
CELERY_CACHE_BACKEND = "default"

# Opcional: para periodic tasks
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# --- Configuración CSP (Content Security Policy) ---

# 1. Política por defecto: Bloquear todo lo que no esté explícitamente permitido
CSP_DEFAULT_SRC = ("'self'",)

# 2. Scripts: Permitir local, CDN de Bootstrap y scripts con 'nonce' (para inlines)
CSP_SCRIPT_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net",  # Bootstrap 5 JS
    "https://code.jquery.com",  # Si usas jQuery
)

# 3. Estilos: Permitir local y CDNs
CSP_STYLE_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net",  # Bootstrap 5 CSS
    "https://fonts.googleapis.com",  # Si usas Google Fonts
)

# 4. Imágenes: Permitir local, data URIs (base64) y tiles de OpenStreetMap
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https://*.openstreetmap.org",
    "https://*.tile.openstreetmap.org",
)

# 5. Fuentes
CSP_FONT_SRC = (
    "'self'",
    "https://fonts.gstatic.com",
    "https://cdn.jsdelivr.net",  # Bootstrap Icons
)

# 6. Iframes: Si embebes el mapa de OpenStreetMap en lugar de solo enlazarlo
CSP_FRAME_SRC = (
    "'self'",
    "https://www.openstreetmap.org",
)

# 7. Configuración de Nonce (Número usado una vez)
# Esto permite ejecutar scripts inline específicos (<script nonce="...">)
# sin permitir 'unsafe-inline' globalmente.
CSP_INCLUDE_NONCE_IN = ["script-src"]

# --- Modo Reporte (Recomendado para inicio) ---
# Si pones esto en True, el navegador solo avisará en la consola pero no bloqueará nada.
# Úsalo para probar en producción un par de días y luego cámbialo a False.
CSP_REPORT_ONLY = False
