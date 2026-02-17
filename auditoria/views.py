"""Views do domínio Auditoria."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import LogAuditoria, TipoAcao
from usuarios.models import PapelUsuario


@login_required
def listar_logs_view(request):
    """
    Lista logs de auditoria.
    Apenas superusuários têm acesso.
    """
    usuario = request.user
    empresa = request.empresa
    
    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")
    
    # Apenas superusuários
    if usuario.papel != PapelUsuario.SUPERUSUARIO:
        messages.error(request, "Apenas superusuários têm acesso aos logs de auditoria.")
        return redirect("jornada:painel")
    
    # Filtros
    tipo_acao = request.GET.get("tipo_acao")
    usuario_filtro = request.GET.get("usuario")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    
    # Query base
    logs = LogAuditoria.objects.filter(empresa=empresa)
    
    # Aplicar filtros
    if tipo_acao:
        logs = logs.filter(tipo_acao=tipo_acao)
    if usuario_filtro:
        logs = logs.filter(usuario_id=usuario_filtro)
    if data_inicio:
        logs = logs.filter(criado_em__date__gte=data_inicio)
    if data_fim:
        logs = logs.filter(criado_em__date__lte=data_fim)
    
    # Ordenar e carregar relacionamentos
    logs = logs.select_related("usuario").order_by("-criado_em")[:500]  # Limitar a 500 registros
    
    # Usuários (para filtro)
    from usuarios.models import Usuario
    usuarios = Usuario.objects.filter(empresa=empresa, ativo=True).order_by("username")
    
    context = {
        "logs": logs,
        "tipos_acao": TipoAcao.choices,
        "usuarios": usuarios,
        "tipo_acao_filtro": tipo_acao,
        "usuario_filtro": usuario_filtro,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    }
    
    return render(request, "auditoria/logs.html", context)