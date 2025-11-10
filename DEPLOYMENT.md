# 🚀 Guía de Despliegue en Render.com

## 📋 Prerrequisitos

- Cuenta en [Render.com](https://render.com)
- Repositorio de GitHub con el código del proyecto
- Git instalado localmente

## 🔧 Archivos de Configuración Creados

### 1. `build.sh`
Script de construcción que se ejecuta al desplegar:
- Instala dependencias de Python
- Ejecuta migraciones de Django
- Recolecta archivos estáticos

### 2. `render.yaml`
Configuración de infraestructura para Render:
- Define el servicio web (Django + Gunicorn)
- Configura la base de datos PostgreSQL
- Establece variables de entorno

### 3. `requirements.txt`
Dependencias actualizadas con:
- `gunicorn` - Servidor WSGI para producción
- `whitenoise` - Servir archivos estáticos
- `psycopg2-binary` - Adaptador PostgreSQL
- `dj-database-url` - Parser de URLs de base de datos

### 4. `.env.example`
Template de variables de entorno

## 📝 Pasos para Desplegar

### 1️⃣ Preparar el Repositorio

```bash
# Asegurarse de que todos los cambios estén commiteados
git add .
git commit -m "Configuración para despliegue en Render"
git push origin dev
```

### 2️⃣ Crear el Servicio en Render

1. Ve a [Render Dashboard](https://dashboard.render.com/)
2. Click en **"New +"** → **"Blueprint"**
3. Conecta tu repositorio de GitHub
4. Selecciona el repositorio `osint_hub`
5. Render detectará automáticamente el archivo `render.yaml`
6. Click en **"Apply"**

### 3️⃣ Configurar Variables de Entorno

Render creará automáticamente las siguientes variables, pero debes verificar:

**Variables Automáticas:**
- `DATABASE_URL` - Generada automáticamente
- `SECRET_KEY` - Generada automáticamente
- `PYTHON_VERSION` - 3.12.3

**Variables que DEBES agregar manualmente:**

1. Ve a tu servicio en Render Dashboard
2. Click en **"Environment"** en el menú lateral
3. Agrega las siguientes variables:

```
ALLOWED_HOSTS=tu-app.onrender.com
CSRF_TRUSTED_ORIGINS=https://tu-app.onrender.com
DEBUG=False
```

**Importante:** Reemplaza `tu-app` con el nombre real de tu aplicación.

### 4️⃣ Despliegue Automático

Render comenzará el despliegue automáticamente:

1. **Build**: Ejecuta `build.sh`
   - Instala dependencias
   - Ejecuta migraciones
   - Recolecta archivos estáticos

2. **Deploy**: Inicia el servidor con Gunicorn
   
3. **Health Check**: Verifica que la app esté funcionando

### 5️⃣ Verificar el Despliegue

Una vez completado, tu aplicación estará disponible en:
```
https://tu-app.onrender.com
```

## 🔒 Configuración de Seguridad

El proyecto incluye configuración de seguridad para producción en `settings.py`:

✅ SSL/HTTPS habilitado
✅ Cookies seguras
✅ CSRF protection
✅ XSS protection
✅ HSTS habilitado
✅ Whitenoise para archivos estáticos

## 🗄️ Base de Datos

Render crea automáticamente una base de datos PostgreSQL:
- Plan gratuito incluido
- Backups automáticos
- Conexión segura vía `DATABASE_URL`

**Nota:** La base de datos gratuita se elimina después de 90 días de inactividad.

## 📊 Monitoreo

En el Dashboard de Render puedes ver:
- Logs en tiempo real
- Métricas de rendimiento
- Estado del servicio
- Historial de despliegues

## 🔄 Actualizaciones

Para actualizar la aplicación:

```bash
git add .
git commit -m "Tu mensaje de commit"
git push origin dev
```

Render detectará el push y redesplegará automáticamente.

## ⚙️ Comandos Útiles

### Acceder a la Shell de Django en Render

1. Ve a tu servicio en Render
2. Click en **"Shell"** en el menú superior
3. Ejecuta comandos Django:

```bash
python manage.py createsuperuser
python manage.py migrate
python manage.py collectstatic
```

### Ver Logs

```bash
# En el Dashboard de Render, ve a "Logs"
# O usa Render CLI:
render logs -f
```

## 🐛 Solución de Problemas

### Error: "Application failed to respond"
- Verifica que `ALLOWED_HOSTS` incluya tu dominio de Render
- Revisa los logs en Render Dashboard

### Error de Base de Datos
- Asegúrate de que `DATABASE_URL` esté configurada
- Verifica que las migraciones se ejecutaron correctamente

### Archivos Estáticos no Cargan
- Verifica que `build.sh` ejecutó `collectstatic`
- Comprueba que `STATIC_ROOT` esté configurado correctamente

### Error 500
- Revisa los logs detallados en Render
- Verifica que todas las variables de entorno estén configuradas
- Asegúrate de que `DEBUG=False` en producción

## 📱 Configuración Adicional Recomendada

### 1. Dominio Personalizado
1. Ve a **Settings** → **Custom Domain**
2. Agrega tu dominio
3. Configura los DNS según las instrucciones

### 2. Notificaciones de Despliegue
1. Ve a **Settings** → **Notifications**
2. Configura notificaciones por email o Slack

### 3. Auto-Deploy desde Pull Requests
1. Ve a **Settings** → **Build & Deploy**
2. Habilita **Auto-Deploy** para pull requests

## 🔐 Variables de Entorno de Producción

Crea un archivo `.env` local basado en `.env.example`:

```bash
cp .env.example .env
```

**NO subas el archivo `.env` a Git** (ya está en `.gitignore`)

## 📞 Soporte

- [Documentación de Render](https://render.com/docs)
- [Comunidad de Render](https://community.render.com)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)

## ✅ Checklist de Despliegue

- [ ] Código commiteado y pusheado a GitHub
- [ ] `render.yaml` configurado correctamente
- [ ] Variables de entorno configuradas en Render
- [ ] `ALLOWED_HOSTS` incluye el dominio de Render
- [ ] `CSRF_TRUSTED_ORIGINS` configurado
- [ ] `DEBUG=False` en producción
- [ ] Migraciones ejecutadas correctamente
- [ ] Archivos estáticos recolectados
- [ ] Superusuario creado (opcional)
- [ ] Aplicación accesible y funcionando

---

🎉 **¡Tu aplicación OSINT Hub está lista para producción!**
