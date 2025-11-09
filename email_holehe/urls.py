from django.urls import path
from . import views

app_name = "email_holehe"

urlpatterns = [
    path("search/", views.search_email, name="search"),
    path("results/", views.search_results, name="results"),
]
