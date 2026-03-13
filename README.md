# OSINT Hub

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-green?logo=django&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple?logo=bootstrap&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Version](https://img.shields.io/badge/version-0.0.1-blue)

Una plataforma web integrada para utilizar diversas herramientas de OSINT (Open Source Intelligence) de manera centralizada y eficiente.

---

## Tabla de Contenidos

- [Descripción](#descripción)
- [Características](#características)
- [Capturas de Pantalla](#capturas-de-pantalla)
- [Tecnologías](#tecnologías)
- [Requisitos del Sistema](#requisitos-del-sistema)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Despliegue en Producción](#despliegue-en-producción)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Roadmap](#roadmap)
- [Contribuciones](#contribuciones)
- [Seguridad](#seguridad)
- [Licencia](#licencia)
- [Autor](#autor)
- [Agradecimientos](#agradecimientos)

---

## Descripción

OSINT Hub es una aplicación web desarrollada con Django que centraliza múltiples herramientas de inteligencia de fuentes abiertas (OSINT) en una sola plataforma. El proyecto facilita la investigación y recopilación de información de fuentes públicas de manera organizada y profesional, eliminando la necesidad de cambiar entre distintas herramientas durante una investigación.

---

## Características

| Herramienta | Descripción | Ruta |
|---|---|---|
| **Email Search** | Verifica la presencia de un correo electrónico en múltiples plataformas usando Holehe | `/email/` |
| **EXIF Metadata** | Extrae metadatos EXIF, XMP e IPTC de imágenes, videos y PDFs. Incluye extracción de coordenadas GPS y enlace a mapa | `/exiftool/` |
| **Hash Tool** | Genera y verifica huellas digitales criptográficas: MD5, SHA1, SHA256, SHA512, BLAKE2 | `/hash/` |
| **IP Lookup** | Consulta geolocalización, ASN e información de red de una dirección IP | `/ip/` |
| **Username Search** | Busca un nombre de usuario en más de 300 sitios y redes sociales usando Sherlock. Exporta resultados a CSV | `/user/` |
| **Phone Search** | Busca información de números de teléfono internacionales de forma asíncrona | `/phone/` |

**Características generales:**
- Interfaz web responsiva y accesible (Bootstrap 5)
- Sistema modular para agregar nuevas herramientas
- Soporte para modo oscuro/claro
- Políticas de seguridad CSP, HSTS y anti-clickjacking
- Archivos SEO: `robots.txt`, `sitemap.xml`, `security.txt`

---

## Capturas de Pantalla

> Las capturas de pantalla se agregarán próximamente. Para agregar las tuyas, coloca los archivos en `static/img/screenshots/` y actualiza esta sección.

---

## Tecnologías

### Backend
- **Python 3.12** — Lenguaje principal
- **Django 5.2** — Framework web
- **Celery 5.6** — Cola de tareas asíncronas
- **Redis** — Message broker para Celery
- **Gunicorn** — Servidor WSGI para producción
- **WhiteNoise** — Servicio de archivos estáticos en producción
- **django-csp** — Content Security Policy

### Herramientas OSINT
- **[Holehe 1.61](https://github.com/megadose/holehe)** — Búsqueda de emails en plataformas
- **[Sherlock 0.16](https://github.com/sherlock-project/sherlock)** — Búsqueda de usuarios en 300+ sitios
- **[PyExifTool 0.5.6](https://github.com/sylikc/pyexiftool)** — Extracción de metadatos EXIF
- **[phonenumbers 9.0](https://github.com/daviddrysdale/python-phonenumbers)** — Análisis de números telefónicos

### Frontend
- **Bootstrap 5** — Framework CSS responsivo
- **Bootstrap Icons** — Iconos SVG
- **JavaScript** (vanilla) — Interactividad del cliente

### Base de Datos
- **SQLite 3** — Desarrollo
- **PostgreSQL** — Producción (recomendado)

---

## Requisitos del Sistema

- **Python 3.12+**
- **ExifTool** (binario del sistema):
  ```bash
  # Debian/Ubuntu
  sudo apt install libimage-exiftool-perl

  # macOS
  brew install exiftool
  ```
- **Redis** (opcional, requerido si se usa Celery):
  ```bash
  # Debian/Ubuntu
  sudo apt install redis-server
  sudo systemctl start redis
  ```
- **pip** y **virtualenv**

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Nakajito/osint_hub.git
cd osint_hub
```

### 2. Crear y activar entorno virtual

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tu configuración
```

### 5. Ejecutar migraciones

```bash
python manage.py migrate
```

### 6. Recolectar archivos estáticos

```bash
python manage.py collectstatic
```

### 7. Ejecutar el servidor de desarrollo

```bash
python manage.py runserver
```

Accede a la aplicación en: `http://localhost:8000`

---

## Configuración

### Variables de entorno

Crea un archivo `.env` en la raíz del proyecto basándote en `.env.example`:

```env
SECRET_KEY=tu-clave-secreta-super-segura
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000
DATABASE_URL=sqlite:///db.sqlite3
```

| Variable | Descripción | Ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave secreta de Django | `django-insecure-...` |
| `DEBUG` | Modo debug (`True` en desarrollo) | `False` |
| `ALLOWED_HOSTS` | Hosts permitidos, separados por coma | `midominio.com,www.midominio.com` |
| `CSRF_TRUSTED_ORIGINS` | Orígenes de confianza para CSRF | `https://midominio.com` |
| `DATABASE_URL` | URL de conexión a la base de datos | `postgres://user:pass@host/db` |

---

## Uso

### Email Search

1. Navega a `http://localhost:8000/email/search/`
2. Ingresa el correo electrónico a investigar
3. Haz clic en **Buscar**
4. Revisa los resultados: plataformas donde el email está registrado

### EXIF Metadata

1. Navega a `http://localhost:8000/exiftool/upload/`
2. Sube un archivo (JPEG, PNG, GIF, TIFF, MP4, PDF — máx. 50 MB)
3. La herramienta extrae todos los metadatos disponibles
4. Si el archivo contiene coordenadas GPS, se genera un enlace a OpenStreetMap

### Hash Tool

1. Navega a `http://localhost:8000/hash/`
2. **Generar:** escribe un texto o sube un archivo, selecciona el algoritmo (MD5, SHA1, SHA256, SHA512, BLAKE2) y haz clic en **Generar**
3. **Verificar:** ingresa el hash esperado para comprobar la integridad del archivo o texto

### IP Lookup

1. Navega a `http://localhost:8000/ip/search/`
2. Ingresa una dirección IP válida
3. Obtén: ciudad, país, zona horaria, coordenadas, ASN y bloque de red

### Username Search

1. Navega a `http://localhost:8000/user/search/`
2. Ingresa el nombre de usuario a investigar
3. Sherlock buscará en más de 300 sitios (proceso puede tomar varios segundos)
4. Descarga los resultados en formato CSV desde la página de resultados

### Phone Search

1. Navega a `http://localhost:8000/phone/search/`
2. Ingresa el número de teléfono en formato internacional (ej. `+521234567890`)
3. La búsqueda se ejecuta de forma asíncrona
4. Revisa los resultados en plataformas disponibles

---

## Despliegue en Producción

### Con Gunicorn

```bash
gunicorn osint_hub.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### En PythonAnywhere

El archivo `pythonanywhere_wsgi.py` está preconfigurado. En el panel de PythonAnywhere:

1. Apunta el archivo WSGI a `pythonanywhere_wsgi.py`
2. Configura las variables de entorno en el panel
3. Ejecuta `collectstatic` desde la consola de PythonAnywhere

### Variables de entorno para producción

```env
SECRET_KEY=clave-muy-larga-y-aleatoria
DEBUG=False
ALLOWED_HOSTS=midominio.com,www.midominio.com
CSRF_TRUSTED_ORIGINS=https://midominio.com,https://www.midominio.com
DATABASE_URL=postgres://usuario:contraseña@host:5432/nombre_db
```

---

## Estructura del Proyecto

```
osint_hub/
├── osint_hub/                  # Configuración del proyecto Django
│   ├── settings.py             # Ajustes principales
│   ├── urls.py                 # Enrutamiento principal
│   ├── celery.py               # Configuración de Celery
│   ├── wsgi.py                 # WSGI para producción
│   └── asgi.py                 # ASGI para soporte asíncrono
│
├── email_holehe/               # App: búsqueda de email (Holehe)
├── ExifTool/                   # App: extracción de metadatos EXIF
├── HashTool/                   # App: generación y verificación de hashes
├── IPLookup/                   # App: geolocalización de IPs
├── PhoneSearch/                # App: búsqueda de números telefónicos
├── UsernameSearch/             # App: búsqueda de usuarios (Sherlock)
│
├── templates/                  # Templates globales
│   ├── base.html
│   ├── home.html
│   ├── 404.html
│   ├── 500.html
│   └── includes/               # Componentes reutilizables
│       ├── navbar.html
│       ├── footer.html
│       ├── hero.html
│       ├── features.html
│       └── disclaimer.html
│
├── static/                     # Archivos estáticos
│   ├── css/
│   ├── js/
│   ├── img/
│   └── bootstrap-icons/
│
├── staticfiles/                # Estáticos recolectados (producción)
├── utils/                      # Funciones utilitarias compartidas
├── test/                       # Tests de integración
│
├── manage.py
├── requirements.txt
├── .env.example
├── pythonanywhere_wsgi.py
└── README.md
```

---

## Roadmap

- [ ] Sistema de autenticación de usuarios
- [ ] API REST para acceso programático
- [ ] Exportación de resultados en PDF
- [ ] Dashboard con estadísticas de uso
- [ ] Integración con más herramientas OSINT
- [ ] Integración con redes sociales

---

## Contribuciones

Las contribuciones son bienvenidas. Para contribuir:

1. Haz fork del proyecto
2. Crea una rama para tu feature:
   ```bash
   git checkout -b feature/nueva-herramienta
   ```
3. Realiza tus cambios y haz commit siguiendo [Conventional Commits](https://www.conventionalcommits.org/):
   ```bash
   git commit -m "feat: agrega herramienta de búsqueda DNS"
   ```
4. Sube tu rama:
   ```bash
   git push origin feature/nueva-herramienta
   ```
5. Abre un Pull Request describiendo el cambio

---

## Seguridad

- **CSRF protection** habilitado en todos los formularios
- **Content Security Policy (CSP)** configurada con restricciones estrictas
- **HSTS, XSS protection y anti-clickjacking** activos en producción
- **Sanitización de entradas** para prevenir inyecciones y path traversal
- **Variables de entorno** para gestión segura de credenciales
- **Timeouts** en todos los procesos externos (Holehe: 60s, Sherlock: 300s, IP: 15s)

Para reportar vulnerabilidades de seguridad consulta el archivo `.well-known/security.txt` o contacta directamente al autor.

---

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

## Autor

**nakajito**
- GitHub: [@nakajito](https://github.com/nakajito)
- Email: nakajito@proton.me

---

## Agradecimientos

- [Holehe](https://github.com/megadose/holehe) — Herramienta de búsqueda de emails
- [Sherlock Project](https://github.com/sherlock-project/sherlock) — Búsqueda de usuarios
- [ExifTool](https://exiftool.org/) — Extracción de metadatos
- Django Community
- Bootstrap Team
- Comunidad OSINT

---

> Si este proyecto te resulta útil, considera darle una estrella en GitHub.
