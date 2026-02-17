"""Views do domínio Fechamentos."""
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q

from banco_horas.models import SaldoBancoHoras
from banco_horas.services import BancoHorasService
from usuarios.models import Usuario, PapelUsuario
from nucleo.excecoes import FechamentoJaRealizado


@login_required
def listar_fechamentos_view(request):
    """
    Lista todos os fechamentos da empresa.
    Apenas administradores podem acessar.
    """
    usuario = request.user
    empresa = request.empresa
    
    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")
    
    # Apenas administradores
    if usuario.papel not in [PapelUsuario.ADMINISTRADOR, PapelUsuario.SUPERUSUARIO]:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("jornada:painel")
    
    # Filtros
    ano = request.GET.get("ano")
    semana = request.GET.get("semana")
    usuario_filtro = request.GET.get("usuario")
    fechado = request.GET.get("fechado")
    
    # Query base
    fechamentos = SaldoBancoHoras.objects.filter(
        empresa=empresa,
    ).select_related("usuario", "fechado_por")
    
    # Aplicar filtros
    if ano:
        fechamentos = fechamentos.filter(ano=ano)
    if semana:
        fechamentos = fechamentos.filter(semana=semana)
    if usuario_filtro:
        fechamentos = fechamentos.filter(usuario_id=usuario_filtro)
    if fechado == "sim":
        fechamentos = fechamentos.filter(fechado=True)
    elif fechado == "nao":
        fechamentos = fechamentos.filter(fechado=False)
    
    # Ordenar
    fechamentos = fechamentos.order_by("-ano", "-semana", "usuario__username")
    
    # Usuários da empresa (para filtro)
    usuarios = Usuario.objects.filter(
        empresa=empresa,
        ativo=True,
    ).order_by("username")
    
    # Anos disponíveis (para filtro)
    anos = SaldoBancoHoras.objects.filter(
        empresa=empresa,
    ).values_list("ano", flat=True).distinct().order_by("-ano")
    
    # Calcular ano e semana atual
    hoje = date.today()
    ano_atual = hoje.isocalendar()[0]
    semana_atual = hoje.isocalendar()[1]
    
    context = {
        "fechamentos": fechamentos,
        "usuarios": usuarios,
        "anos": anos,
        "ano_filtro": ano,
        "semana_filtro": semana,
        "usuario_filtro": usuario_filtro,
        "fechado_filtro": fechado,
        "ano_atual": ano_atual,
        "semana_atual": semana_atual,
    }
    
    return render(request, "fechamentos/listar.html", context)


@login_required
def fechar_semana_view(request):
    """
    Fecha a semana de um ou mais usuários.
    Apenas administradores podem fechar.
    """
    usuario = request.user
    empresa = request.empresa
    
    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")
    
    # Apenas administradores
    if usuario.papel not in [PapelUsuario.ADMINISTRADOR, PapelUsuario.SUPERUSUARIO]:
        messages.error(request, "Você não tem permissão para realizar esta ação.")
        return redirect("jornada:painel")
    
    if request.method != "POST":
        return redirect("fechamentos:listar")
    
    # Parâmetros
    ano = int(request.POST.get("ano"))
    semana = int(request.POST.get("semana"))
    usuario_id = request.POST.get("usuario_id")
    fechar_todos = request.POST.get("fechar_todos") == "on"
    
    fechados = 0
    erros = 0
    
    try:
        if fechar_todos:
            # Fechar para todos os usuários ativos da empresa
            usuarios_ativos = Usuario.objects.filter(
                empresa=empresa,
                ativo=True,
            )
            
            for usr in usuarios_ativos:
                try:
                    BancoHorasService.calcular_saldo_semana(
                        usuario=usr,
                        empresa=empresa,
                        ano=ano,
                        semana=semana,
                        fechar=True,
                        fechado_por=usuario,
                    )
                    fechados += 1
                except FechamentoJaRealizado:
                    # Ignorar se já estiver fechado
                    pass
                except Exception as e:
                    erros += 1
                    messages.warning(request, f"Erro ao fechar semana para {usr.username}: {str(e)}")
        else:
            # Fechar apenas para um usuário específico
            usr = Usuario.objects.get(id=usuario_id, empresa=empresa)
            BancoHorasService.calcular_saldo_semana(
                usuario=usr,
                empresa=empresa,
                ano=ano,
                semana=semana,
                fechar=True,
                fechado_por=usuario,
            )
            fechados = 1
        
        if fechados > 0:
            messages.success(
                request,
                f"Fechamento realizado com sucesso! {fechados} semana(s) fechada(s)."
            )
        
        if erros > 0:
            messages.warning(request, f"{erros} erro(s) durante o fechamento.")
    
    except FechamentoJaRealizado:
        messages.error(request, "Esta semana já foi fechada anteriormente.")
    except Exception as e:
        messages.error(request, f"Erro ao fechar semana: {str(e)}")
    
    return redirect("fechamentos:listar")


@login_required
def reabrir_semana_view(request, fechamento_id):
    """
    Reabre uma semana já fechada.
    Apenas superusuários podem reabrir.
    """
    usuario = request.user
    empresa = request.empresa
    
    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")
    
    # Apenas superusuários
    if usuario.papel != PapelUsuario.SUPERUSUARIO:
        messages.error(request, "Apenas superusuários podem reabrir fechamentos.")
        return redirect("fechamentos:listar")
    
    try:
        fechamento = SaldoBancoHoras.objects.get(
            id=fechamento_id,
            empresa=empresa,
        )
        
        if not fechamento.fechado:
            messages.warning(request, "Esta semana não está fechada.")
            return redirect("fechamentos:listar")
        
        # Reabrir
        fechamento.fechado = False
        fechamento.data_fechamento = None
        fechamento.fechado_por = None
        fechamento.save()
        
        messages.success(
            request,
            f"Semana {fechamento.ano}S{fechamento.semana:02d} reaberta com sucesso para {fechamento.usuario.username}!"
        )
    
    except SaldoBancoHoras.DoesNotExist:
        messages.error(request, "Fechamento não encontrado.")
    except Exception as e:
        messages.error(request, f"Erro ao reabrir semana: {str(e)}")
    
    return redirect("fechamentos:listar")