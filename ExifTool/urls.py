from django.urls import path
from . import views

app_name = "exiftool"

urlpatterns = [
    path("upload/", views.upload_file, name="upload"),
    path("metadata/", views.show_metadata, name="metadata"),
]
