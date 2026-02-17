from django.urls import path
from . import views

app_name = "auditoria"

urlpatterns = [
    path("logs/", views.listar_logs_view, name="logs"),
]