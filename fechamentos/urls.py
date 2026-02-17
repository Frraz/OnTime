from django.urls import path
from . import views

app_name = "fechamentos"

urlpatterns = [
    path("", views.listar_fechamentos_view, name="listar"),
    path("fechar/", views.fechar_semana_view, name="fechar"),
    path("reabrir/<int:fechamento_id>/", views.reabrir_semana_view, name="reabrir"),
]