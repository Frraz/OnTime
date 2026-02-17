from django.urls import path
from . import views

app_name = "banco_horas"

urlpatterns = [
    path("painel/", views.painel_view, name="painel"),
    path("extrato/", views.extrato_view, name="extrato"),
]