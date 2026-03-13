from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls import handler404, handler500

urlpatterns = [
    # path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("email/", include("email_holehe.urls")),
    path("exiftool/", include("ExifTool.urls")),
    path("phone/", include("PhoneSearch.urls")),
    path("ip/", include("IPLookup.urls")),
    path("user/", include("UsernameSearch.urls")),
    path("hash/", include("HashTool.urls")),
    path("instagram/", include("InstagramSniffer.urls")),
    # Rutas SEO y Seguridad
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path(
        ".well-known/security.txt",
        TemplateView.as_view(
            template_name=".well-known/security.txt", content_type="text/plain"
        ),
    ),
    path(
        "sitemap.xml",
        TemplateView.as_view(
            template_name="sitemap.xml", content_type="application/xml"
        ),
    ),
]

# Handlers de errores personalizados
handler404 = "django.views.defaults.page_not_found"
handler500 = "django.views.defaults.server_error"

# En desarrollo, servir archivos estáticos y media
if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
