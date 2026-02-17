from django.urls import path
from . import views, views_dashboard

app_name = "jornada"

urlpatterns = [
    # Dashboard
    path("dashboard/", views_dashboard.dashboard_pessoal_view, name="dashboard_pessoal"),
    path("dashboard/gerencial/", views_dashboard.dashboard_gerencial_view, name="dashboard_gerencial"),
    
    # Painel e Registro
    path("painel/", views.painel_view, name="painel"),
    path("registrar/", views.registrar_ponto_view, name="registrar"),
    path("historico/", views.historico_view, name="historico"),
    
    # Solicitações de ajuste
    path("solicitar-ajuste/<int:registro_id>/", views.solicitar_ajuste_view, name="solicitar_ajuste"),
    path("solicitacoes/", views.listar_solicitacoes_view, name="listar_solicitacoes"),
    path("analisar-solicitacao/<int:solicitacao_id>/", views.analisar_solicitacao_view, name="analisar_solicitacao"),
    
    # Gerenciamento (admin)
    path("gerenciar-locais/", views.gerenciar_locais_view, name="gerenciar_locais"),
    path("gerenciar-ips/", views.gerenciar_ips_view, name="gerenciar_ips"),
    
    # API - Detectar IP
    path("detectar-ip/", views.detectar_ip_view, name="detectar_ip"),
]