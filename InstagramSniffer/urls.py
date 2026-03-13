from django.urls import path
from . import views

app_name = "instasniffer"

urlpatterns = [
    path("search/", views.search_username, name="search"),
    path("results/", views.show_results, name="results"),
    path("media/", views.search_media, name="media"),
    path("media/results/", views.show_media_results, name="media_results"),
]
