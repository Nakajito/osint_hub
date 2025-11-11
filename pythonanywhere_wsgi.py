"""
WSGI config for osint_hub project - PythonAnywhere

Esta configuración está optimizada para PythonAnywhere.
Actualiza las rutas según tu configuración específica.

Para usar este archivo en PythonAnywhere:
1. Ve a la pestaña "Web" en tu dashboard de PythonAnywhere
2. En "Code" -> "Source code", actualiza la ruta a: /home/TU_USUARIO/osint_hub
3. En "Code" -> "WSGI configuration file", edita y reemplaza el contenido con este archivo
4. Actualiza TU_USUARIO con tu nombre de usuario de PythonAnywhere
"""

import os
import sys

# ==========================================
# CONFIGURACIÓN DE RUTAS - ACTUALIZA ESTO
# ==========================================
# Reemplaza 'TU_USUARIO' con tu nombre de usuario de PythonAnywhere
username = "TU_USUARIO"  # ⚠️ CAMBIA ESTO

# Ruta al directorio del proyecto
path = f"/home/{username}/osint_hub"
if path not in sys.path:
    sys.path.insert(0, path)

# Ruta al entorno virtual
virtualenv_path = f"/home/{username}/.virtualenvs/osint_hub_env"
activate_this = f"{virtualenv_path}/bin/activate_this.py"

# Activar el entorno virtual
try:
    with open(activate_this) as file_:
        exec(file_.read(), dict(__file__=activate_this))
except FileNotFoundError:
    print(f"⚠️ WARNING: No se encontró el entorno virtual en {virtualenv_path}")
    print("Asegúrate de crear el entorno virtual primero")

# ==========================================
# CONFIGURACIÓN DE DJANGO
# ==========================================
os.environ["DJANGO_SETTINGS_MODULE"] = "osint_hub.settings"

# Importar la aplicación WSGI de Django
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
