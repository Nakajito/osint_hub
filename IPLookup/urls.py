from django.urls import path
from . import views

app_name = "iplookup"

urlpatterns = [
    path("", views.ip_search, name="search"),
    path("results/", views.results, name="results"),
]
