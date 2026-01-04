from django.urls import path
from . import views

app_name = "phonesearch"

urlpatterns = [
    path("search/", views.search_phone, name="search"),
]
