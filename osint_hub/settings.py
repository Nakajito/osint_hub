from pathlib import Path
import os
from decouple import config
import dj_database_url


BASE_DIR = Path(__file__).resolve().parent.parent

# Usar variables de entorno
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-4gnf%1w^*a8a10-9f&l3s+fd0f0^88segf3o47&)bn=v6x2sd(",
)
DEBUG = config("DEBUG", default=True, cast=bool)

# ALLOWED_HOSTS - Compatible con PythonAnywhere y Render
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
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Whitenoise para archivos estáticos
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


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
SEARCH_RESULTS_DIR = os.environ.get(
    "SEARCH_RESULTS_DIR",
    os.path.expanduser("~/.local/share/osint_hub/search_results"),
)

# Configuración de seguridad para producción
if not DEBUG:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# CSRF Trusted Origins (para Render.com y PythonAnywhere)
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://*.pythonanywhere.com,https://*.onrender.com",
    cast=lambda v: [s.strip() for s in v.split(",")] if v else [],
)

# Configurar path a ExifTool
EXIFTOOL_PATH = "/usr/bin/exiftool"  # Ruta por defecto en Ubuntu

if not os.path.exists(EXIFTOOL_PATH):
    EXIFTOOL_PATH = "/usr/local/bin/exiftool"  # Ruta alternativa


# Celery Configuration
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos
CELERY_RESULT_EXPIRES = 3600  # 1 hora
CELERY_CACHE_BACKEND = "default"

# En desarrollo, permitir que Celery ejecute tareas de forma síncrona
# para evitar depender de un broker (útil para debugging local).
# if DEBUG:
# CELERY_TASK_ALWAYS_EAGER = True
# CELERY_TASK_EAGER_PROPAGATES = True

# Opcional: para periodic tasks
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
