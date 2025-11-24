#!/usr/bin/env bash
# exit on error
set -o errexit

# Instalar dependencias de Python
pip install --upgrade pip
pip install -r requirements.txt

# Ejecutar migraciones
python manage.py makemigrations
python manage.py migrate

# Recolectar archivos estáticos
python manage.py collectstatic --no-input --clear
