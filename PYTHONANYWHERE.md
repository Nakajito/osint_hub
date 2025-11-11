# 🐍 Guía de Despliegue en PythonAnywhere

## 📋 Prerrequisitos

- Cuenta en [PythonAnywhere](https://www.pythonanywhere.com) (gratuita o de pago)
- Repositorio Git del proyecto (GitHub, GitLab, etc.)
- Conocimientos básicos de Bash/Linux

## 🚀 Pasos para Desplegar

### 1️⃣ Crear Cuenta y Configurar

1. Regístrate en [PythonAnywhere](https://www.pythonanywhere.com)
2. Confirma tu email
3. Inicia sesión en tu dashboard

### 2️⃣ Clonar el Repositorio

Abre una **Bash Console** en PythonAnywhere:

```bash
# Ir al directorio home
cd ~

# Clonar el repositorio
git clone https://github.com/Nakajito/osint_hub.git
cd osint_hub
```

### 3️⃣ Crear Entorno Virtual

```bash
# Crear entorno virtual
mkvirtualenv osint_hub_env --python=/usr/bin/python3.10

# El entorno se activará automáticamente
# Deberías ver (osint_hub_env) en tu prompt

# Para activar manualmente en el futuro:
workon osint_hub_env
```

### 4️⃣ Instalar Dependencias

```bash
# Asegúrate de estar en el directorio del proyecto
cd ~/osint_hub

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
pip list
```

### 5️⃣ Configurar Variables de Entorno

Crea un archivo `.env` en el directorio del proyecto:

```bash
cd ~/osint_hub
nano .env
```

Agrega el siguiente contenido (ajusta según necesites):

```bash
SECRET_KEY=tu-clave-secreta-super-segura-aqui
DEBUG=False
ALLOWED_HOSTS=tu-usuario.pythonanywhere.com,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://tu-usuario.pythonanywhere.com
DATABASE_URL=sqlite:///db.sqlite3
```

**Importante:** Reemplaza `tu-usuario` con tu nombre de usuario de PythonAnywhere.

Guarda con `Ctrl + O`, `Enter`, y sal con `Ctrl + X`.

### 6️⃣ Ejecutar Migraciones

```bash
cd ~/osint_hub
python manage.py migrate
```

### 7️⃣ Crear Superusuario (Opcional)

```bash
python manage.py createsuperuser
# Sigue las instrucciones
```

### 8️⃣ Recolectar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

### 9️⃣ Configurar Web App en PythonAnywhere

1. Ve a la pestaña **"Web"** en tu dashboard
2. Click en **"Add a new web app"**
3. Selecciona tu dominio: `tu-usuario.pythonanywhere.com`
4. Selecciona **"Manual configuration"**
5. Selecciona **Python 3.10** (o la versión que uses)

### 🔟 Configurar WSGI

1. En la pestaña **"Web"**, en la sección **"Code"**
2. Click en el archivo **WSGI configuration file** (link azul)
3. **REEMPLAZA TODO** el contenido con el archivo `pythonanywhere_wsgi.py`
4. **Actualiza** la variable `username` con tu nombre de usuario:

```python
# Línea 18 aproximadamente
username = 'TU_USUARIO'  # ⚠️ CAMBIA ESTO por tu usuario de PythonAnywhere
```

5. Guarda el archivo (botón verde "Save")

### 1️⃣1️⃣ Configurar Virtualenv

En la pestaña **"Web"**, en la sección **"Virtualenv"**:

1. En **"Enter path to a virtualenv"**, ingresa:
```
/home/TU_USUARIO/.virtualenvs/osint_hub_env
```
(Reemplaza `TU_USUARIO` con tu nombre de usuario)

2. Click en el ✓ (check) para confirmar

### 1️⃣2️⃣ Configurar Archivos Estáticos

En la pestaña **"Web"**, en la sección **"Static files"**:

1. Agrega las siguientes entradas:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/TU_USUARIO/osint_hub/staticfiles/` |
| `/media/` | `/home/TU_USUARIO/osint_hub/media/` |

(Reemplaza `TU_USUARIO` con tu nombre de usuario)

### 1️⃣3️⃣ Configurar Source Code

En la pestaña **"Web"**, en la sección **"Code"**:

1. **Source code:** `/home/TU_USUARIO/osint_hub`
2. **Working directory:** `/home/TU_USUARIO/osint_hub`

### 1️⃣4️⃣ Reload y Probar

1. Scroll hasta arriba en la pestaña **"Web"**
2. Click en el botón verde **"Reload TU_USUARIO.pythonanywhere.com"**
3. Espera unos segundos
4. Visita: `https://tu-usuario.pythonanywhere.com`

## ✅ Verificación

Si todo está correcto, deberías ver tu aplicación OSINT Hub funcionando.

### ❌ Solución de Problemas

#### Error 502 - Bad Gateway

**Revisa el log de errores:**
1. Pestaña **"Web"** → **"Log files"**
2. Click en **"Error log"**
3. Busca el último error

**Causas comunes:**
- Virtualenv mal configurado
- Rutas incorrectas en WSGI
- Módulos no instalados

#### Error 500 - Internal Server Error

```bash
# Verifica que DEBUG esté en False
cd ~/osint_hub
cat .env | grep DEBUG

# Revisa el error log
tail -50 /var/log/tu-usuario.pythonanywhere.com.error.log
```

#### ImportError: No module named 'django'

```bash
# Verifica que el virtualenv esté activo
workon osint_hub_env

# Reinstala dependencias
cd ~/osint_hub
pip install -r requirements.txt
```

#### Archivos estáticos no cargan

```bash
# Recolecta archivos estáticos nuevamente
cd ~/osint_hub
workon osint_hub_env
python manage.py collectstatic --noinput --clear

# Verifica permisos
ls -la ~/osint_hub/staticfiles/
```

#### No such table: django_session

```bash
# Ejecuta migraciones
cd ~/osint_hub
workon osint_hub_env
python manage.py migrate
```

## 🔄 Actualizar la Aplicación

Cuando hagas cambios en el código:

```bash
# 1. Abre Bash Console
cd ~/osint_hub

# 2. Activa el entorno virtual
workon osint_hub_env

# 3. Pull cambios desde Git
git pull origin main

# 4. Instala nuevas dependencias (si hay)
pip install -r requirements.txt

# 5. Ejecuta migraciones (si hay cambios en models)
python manage.py migrate

# 6. Recolecta archivos estáticos
python manage.py collectstatic --noinput

# 7. Reload la aplicación
# Ve a la pestaña Web y click en Reload
```

O desde la consola:

```bash
# Desde Bash Console
touch /var/www/tu-usuario_pythonanywhere_com_wsgi.py
```

## 📊 Limitaciones del Plan Gratuito

- ✅ 512 MB de espacio en disco
- ✅ 1 aplicación web
- ✅ Sin tarjeta de crédito requerida
- ⚠️ CPU limitada (100 segundos/día)
- ⚠️ Sin soporte para tareas programadas complejas
- ⚠️ Acceso limitado a internet desde código (whitelist)

## 🔐 Seguridad

### Generar SECRET_KEY Segura

```bash
cd ~/osint_hub
workon osint_hub_env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copia la clave generada y actualiza tu archivo `.env`.

### Proteger .env

```bash
# El archivo .env NO debe subirse a Git
# Verifica que esté en .gitignore
cat ~/osint_hub/.gitignore | grep .env
```

## 📝 Comandos Útiles

```bash
# Ver logs en tiempo real
tail -f /var/log/tu-usuario.pythonanywhere.com.error.log

# Acceder a Django shell
cd ~/osint_hub
workon osint_hub_env
python manage.py shell

# Ver versión de Python
python --version

# Listar paquetes instalados
pip list

# Verificar configuración de Django
python manage.py check

# Crear backup de la base de datos
cp ~/osint_hub/db.sqlite3 ~/osint_hub/db.sqlite3.backup

# Ver espacio en disco usado
du -sh ~/osint_hub
```

## 🆙 Upgrade a Plan de Pago

Si necesitas más recursos:
- **Hacker Plan ($5/mes):** Sin límites de CPU, más espacio
- **Web Developer Plan ($12/mes):** Múltiples apps, más storage

## 📞 Soporte

- [Documentación PythonAnywhere](https://help.pythonanywhere.com/)
- [Foro de PythonAnywhere](https://www.pythonanywhere.com/forums/)
- [Django en PythonAnywhere](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/)

## ✅ Checklist de Despliegue

- [ ] Repositorio clonado en PythonAnywhere
- [ ] Entorno virtual creado (`osint_hub_env`)
- [ ] Dependencias instaladas
- [ ] Archivo `.env` creado y configurado
- [ ] Migraciones ejecutadas
- [ ] Archivos estáticos recolectados
- [ ] Web app creada en dashboard
- [ ] WSGI configurado con rutas correctas
- [ ] Virtualenv configurado
- [ ] Archivos estáticos configurados
- [ ] Source code configurado
- [ ] App reloaded
- [ ] Aplicación funcionando en el navegador

---

🎉 **¡Tu aplicación OSINT Hub está desplegada en PythonAnywhere!**

URL: `https://tu-usuario.pythonanywhere.com`
