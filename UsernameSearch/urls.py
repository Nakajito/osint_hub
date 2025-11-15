from django.urls import path
from . import views

app_name = "usersearch"

urlpatterns = [
    path("search/", views.search_username, name="search"),
    path("results/", views.show_results, name="results"),
    path("download/", views.download_results, name="download"),
]
