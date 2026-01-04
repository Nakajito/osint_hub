from django.urls import path
from . import views

app_name = "phonesearch"

urlpatterns = [
    path("search/", views.search_phone, name="search"),
    path("check_results/", views.check_results, name="check_results"),
    path("results/", views.show_results, name="results"),
    path(
        "test_celery/", views.test_celery_view, name="test_celery"
    ),  # Ruta para probar Celery
]
