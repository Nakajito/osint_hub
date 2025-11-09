# OSINT Hub 🔍

Una plataforma web integrada para utilizar diversas herramientas de OSINT (Open Source Intelligence) de manera centralizada y eficiente.

## 📋 Descripción

OSINT Hub es una aplicación web desarrollada con Django que centraliza múltiples herramientas de inteligencia de fuentes abiertas (OSINT) en una sola plataforma. El proyecto facilita la investigación y recopilación de información de fuentes públicas de manera organizada y profesional.

## 🚀 Características

- **Búsqueda de Email (Holehe)**: Verifica la presencia de un correo electrónico en múltiples plataformas y servicios
- Interfaz web intuitiva y responsiva
- Sistema modular para agregar nuevas herramientas OSINT
- Historial de búsquedas y resultados

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python 3.12**: Lenguaje de programación principal
- **Django 5.2**: Framework web de alto nivel
- **python-decouple**: Gestión de variables de entorno
- **Holehe**: Herramienta OSINT para búsqueda de emails

### Frontend
- **HTML5**: Estructura de las páginas
- **Bootstrap 5**: Framework CSS para diseño responsivo
- **JavaScript**: Interactividad del lado del cliente

### Base de Datos
- **SQLite**: Base de datos por defecto (desarrollo)
- Compatible con PostgreSQL, MySQL (producción)

## 📁 Estructura del Proyecto

```
osint_hub/                          # Carpeta raíz del proyecto
├── manage.py                       # Script de gestión de Django
├── requirements.txt                # Dependencias del proyecto
├── .env                           # Variables de entorno (NO subir a git)
├── .gitignore                     # Archivos a ignorar en git
├── README.md                      # Documentación del proyecto
│
├── osint_hub/                     # Carpeta de configuración del proyecto
│   ├── __init__.py
│   ├── settings.py                # Tu archivo actual
│   ├── urls.py                    # URLs principales
│   ├── wsgi.py                    # WSGI para producción
│   └── asgi.py                    # ASGI para apps asíncronas
│
├── apps/                          # Carpeta para todas las apps (opcional pero recomendado)
│   ├── email_holehe/             # Tu app actual
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── forms.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── tests.py
│   │   ├── serializers.py        # Si usas Django REST Framework
│   │   ├── migrations/
│   │   │   └── __init__.py
│   │   └── templates/             # Templates específicos de la app
│   │       └── email_holehe/
│   │
│   └── otra_app/
│
├── templates/                     # Templates globales
│   ├── base.html
│   ├── home.html
│   └── includes/
│       ├── navbar.html
│       └── footer.html
│
├── static/                        # Archivos estáticos
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   └── main.js
│   ├── img/
│   └── vendor/                    # Librerías de terceros
│
├── media/                         # Archivos subidos por usuarios
│   └── uploads/
│
├── staticfiles/                   # Archivos estáticos recolectados (producción)
│
├── locale/                        # Archivos de traducción
│   └── es/
│
├── tests/                         # Tests globales
│   ├── __init__.py
│   └── test_integration.py
│
└── utils/                         # Utilidades compartidas
    ├── __init__.py
    ├── helpers.py
    └── validators.py
```

## 🔧 Instalación

### Prerrequisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- virtualenv (recomendado)

### Pasos de instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/Nakajito/osint_hub.git
cd osint_hub
```

2. **Crear y activar entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Linux/Mac
# venv\Scripts\activate   # En Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Ejecutar migraciones**
```bash
python manage.py migrate
```

6. **Crear superusuario (opcional)**
```bash
python manage.py createsuperuser
```

7. **Recolectar archivos estáticos**
```bash
python manage.py collectstatic
```

8. **Ejecutar servidor de desarrollo**
```bash
python manage.py runserver
```

Accede a la aplicación en: `http://localhost:8000`

## ⚙️ Configuración

### Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=tu-clave-secreta-super-segura
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

### Configuración de Producción

Para producción, asegúrate de:
- Establecer `DEBUG=False`
- Usar una base de datos robusta (PostgreSQL recomendado)
- Configurar `ALLOWED_HOSTS` correctamente
- Usar un servidor web como Nginx + Gunicorn

## 📚 Uso

### Búsqueda de Email

1. Accede a la sección "Email Search"
2. Ingresa el correo electrónico a investigar
3. Haz clic en "Buscar"
4. Revisa los resultados mostrando en qué plataformas está registrado el email

## 🔐 Seguridad

- Las claves secretas se manejan mediante variables de entorno
- CSRF protection habilitado
- Validación de formularios del lado del servidor
- Sanitización de inputs para prevenir XSS

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para contribuir:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/NuevaHerramienta`)
3. Commit tus cambios (`git commit -m 'Agrega nueva herramienta OSINT'`)
4. Push a la rama (`git push origin feature/NuevaHerramienta`)
5. Abre un Pull Request

## 📝 Roadmap

- [ ] Integración con más herramientas OSINT
- [ ] Sistema de autenticación de usuarios
- [ ] API REST para acceso programático
- [ ] Exportación de resultados (PDF, CSV, JSON)
- [ ] Dashboard con estadísticas
- [ ] Búsqueda por nombre de usuario
- [ ] Búsqueda por número telefónico
- [ ] Integración con redes sociales

## ⚖️ Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## ⚠️ Disclaimer

Esta herramienta está diseñada únicamente para fines educativos y de investigación legal. El uso de estas herramientas debe cumplir con todas las leyes y regulaciones aplicables. Los desarrolladores no se hacen responsables del mal uso de esta aplicación.

## 👨‍💻 Autor

**Tu Nombre**
- GitHub: [@nakajito](https://github.com/nakajito)
- Email: nakajito@proton.me

## 🙏 Agradecimientos

- [Holehe](https://github.com/megadose/holehe) - Herramienta de búsqueda de emails
- Django Community
- Bootstrap Team
- Comunidad OSINT

---

⭐ Si este proyecto te resulta útil, considera darle una estrella en GitHub