"""Views do domínio Banco de Horas."""
from datetime import date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import SaldoBancoHoras
from .services import BancoHorasService


@login_required
def extrato_view(request):
    """
    Extrato de banco de horas do usuário.
    Mostra saldo acumulado e histórico semanal.
    """
    usuario = request.user
    empresa = request.empresa
    
    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")
    
    # Saldo atual
    saldo_atual = BancoHorasService.obter_saldo_atual(usuario, empresa)
    
    # Histórico de saldos
    saldos = SaldoBancoHoras.objects.filter(
        empresa=empresa,
        usuario=usuario,
    ).order_by("-ano", "-semana")[:12]  # Últimas 12 semanas
    
    context = {
        "saldo_atual": saldo_atual,
        "saldos": saldos,
    }
    
    return render(request, "banco_horas/extrato.html", context)


@login_required
def painel_view(request):
    """
    Painel resumido de banco de horas.
    """
    usuario = request.user
    empresa = request.empresa
    
    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")
    
    saldo_atual = BancoHorasService.obter_saldo_atual(usuario, empresa)
    
    # Calcular semana atual
    hoje = date.today()
    ano = hoje.isocalendar()[0]
    semana = hoje.isocalendar()[1]
    
    # Calcular ou obter saldo da semana atual (sem fechar)
    saldo_semana = BancoHorasService.calcular_saldo_semana(
        usuario, empresa, ano, semana, fechar=False
    )
    
    context = {
        "saldo_atual": saldo_atual,
        "saldo_semana": saldo_semana,
    }
    
    return render(request, "banco_horas/painel.html", context)