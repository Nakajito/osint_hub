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
