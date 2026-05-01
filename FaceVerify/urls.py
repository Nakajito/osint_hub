from django.urls import path

from . import views

app_name = "faceverify"

urlpatterns = [
    path("", views.index, name="index"),
    path("status/<str:task_id>/", views.task_status, name="status"),
]
