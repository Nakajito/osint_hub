from django.urls import path
from . import views

app_name = "HashTool"

urlpatterns = [
    path("", views.index, name="index"),
    path("verify/", views.verify, name="verify"),
]
