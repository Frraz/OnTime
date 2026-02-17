"""Views do dashboard."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from .services_stats import DashboardService
from usuarios.models import PapelUsuario


@login_required
def dashboard_pessoal_view(request):
    """Dashboard pessoal do colaborador."""
    usuario = request.user
    empresa = request.empresa
    
    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")
    
    # Resumo de hoje
    resumo_hoje = DashboardService.get_resumo_hoje(usuario, empresa)
    
    # Semana atual
    semana_atual = DashboardService.get_semana_atual(usuario, empresa)
    
    # Últimas 12 semanas
    ultimas_semanas = DashboardService.get_ultimas_semanas(usuario, empresa, 12)
    
    # Evolução banco de horas
    evolucao_banco = DashboardService.get_evolucao_banco_horas(usuario, empresa, 12)
    
    # Horas por dia da semana
    horas_dia_semana = DashboardService.get_horas_por_dia_semana(usuario, empresa)
    
    context = {
        'resumo_hoje': resumo_hoje,
        'semana_atual': semana_atual,
        'ultimas_semanas': ultimas_semanas,
        'evolucao_banco': evolucao_banco,
        'horas_dia_semana': horas_dia_semana,
    }
    
    return render(request, "jornada/dashboard_pessoal.html", context)


@login_required
def dashboard_gerencial_view(request):
    """Dashboard gerencial (apenas admin)."""
    usuario = request.user
    empresa = request.empresa
    
    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")
    
    # Apenas admins
    if not usuario.eh_administrador:
        messages.error(request, "Você não tem permissão para acessar este dashboard.")
        return redirect("jornada:dashboard_pessoal")
    
    # Estatísticas gerais
    stats_gerais = DashboardService.get_estatisticas_gerais(empresa)
    
    # Ranking de usuários
    ranking = DashboardService.get_ranking_usuarios(empresa, 10)
    
    context = {
        'stats_gerais': stats_gerais,
        'ranking': ranking,
    }
    
    return render(request, "jornada/dashboard_gerencial.html", context)