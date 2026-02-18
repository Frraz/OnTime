"""Views do domínio Jornada."""
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse

from nucleo.excecoes import (
    SequenciaRegistroInvalida,
    ValidacaoLocalizacaoFalhou,
    ValidacaoIPFalhou,
    FotoObrigatoriaAusente,
)
from .services import JornadaService, SolicitacaoAjusteService
from .models import (
    RegistroPonto,
    TipoRegistro,
    OrigemRegistro,
    StatusRegistro,
    SolicitacaoAjuste,
    LocalPermitido,
    IPPermitido,
)
from usuarios.models import PapelUsuario


def get_client_ip(request):
    """Obtém o IP real do cliente, considerando proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def painel_view(request):
    """Painel principal de bater ponto."""
    usuario = request.user
    empresa = request.empresa

    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")

    proximo_tipo = JornadaService.obter_proximo_tipo(empresa, usuario)

    # Usa localtime para garantir data no fuso de Brasília
    hoje = timezone.localtime().date()
    precisa_foto = not RegistroPonto.objects.filter(
        empresa=empresa,
        usuario=usuario,
        data_hora__date=hoje,
        status=StatusRegistro.ATIVO,
    ).exists()

    registros_hoje = RegistroPonto.objects.filter(
        empresa=empresa,
        usuario=usuario,
        data_hora__date=hoje,
        status=StatusRegistro.ATIVO,
    ).order_by("data_hora")

    vinculo_info = {
        'tipo': usuario.get_vinculo_display(),
        'precisa_gps': usuario.vinculo in ['EXTERNO', 'INTERNO'],
        'precisa_local': usuario.vinculo == 'INTERNO',
        'livre': usuario.vinculo == 'CONFIANCA',
    }

    context = {
        "proximo_tipo": proximo_tipo,
        "registros_hoje": registros_hoje,
        "precisa_foto": precisa_foto,
        "vinculo_info": vinculo_info,
    }

    return render(request, "jornada/painel.html", context)


@login_required
def registrar_ponto_view(request):
    """Endpoint para registrar ponto (com foto e GPS)."""
    if request.method != "POST":
        return redirect("jornada:painel")

    usuario = request.user
    empresa = request.empresa

    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")

    latitude = request.POST.get("latitude")
    longitude = request.POST.get("longitude")
    foto_base64 = request.POST.get("foto")
    justificativa_sem_foto = request.POST.get("justificativa_sem_foto", "")
    ip_origem = get_client_ip(request)

    lat_decimal = Decimal(latitude) if latitude else None
    lon_decimal = Decimal(longitude) if longitude else None

    try:
        registro = JornadaService.registrar_ponto(
            empresa=empresa,
            usuario=usuario,
            origem=OrigemRegistro.SISTEMA,
            registrado_por=usuario,
            latitude=lat_decimal,
            longitude=lon_decimal,
            ip_origem=ip_origem,
            foto_base64=foto_base64,
            justificativa_sem_foto=justificativa_sem_foto,
        )

        # Exibe horário no fuso local de Brasília
        hora_local = timezone.localtime(registro.data_hora).strftime('%H:%M')
        messages.success(
            request,
            f"{registro.get_tipo_display()} registrado com sucesso às {hora_local}!"
        )

    except SequenciaRegistroInvalida as e:
        messages.error(request, str(e))
    except ValidacaoLocalizacaoFalhou as e:
        messages.error(request, f"❌ Localização: {str(e)}")
    except ValidacaoIPFalhou as e:
        messages.error(request, f"❌ Localização: {str(e)}")
    except FotoObrigatoriaAusente as e:
        messages.error(request, f"📸 Foto: {str(e)}")
    except Exception as e:
        messages.error(request, f"Erro ao registrar ponto: {str(e)}")

    return redirect("jornada:painel")


@login_required
def historico_view(request):
    """Lista histórico de registros com filtros avançados."""
    usuario = request.user
    empresa = request.empresa

    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")

    data_inicio  = request.GET.get("data_inicio")
    data_fim     = request.GET.get("data_fim")
    tipo_filtro  = request.GET.get("tipo")
    origem_filtro = request.GET.get("origem")

    registros = RegistroPonto.objects.filter(
        empresa=empresa,
        usuario=usuario,
        status=StatusRegistro.ATIVO,
    ).select_related('local_utilizado', 'registrado_por')

    if data_inicio:
        registros = registros.filter(data_hora__date__gte=data_inicio)
    if data_fim:
        registros = registros.filter(data_hora__date__lte=data_fim)
    if tipo_filtro:
        registros = registros.filter(tipo=tipo_filtro)
    if origem_filtro:
        registros = registros.filter(origem=origem_filtro)

    registros = registros.order_by('-data_hora')

    total_registros      = registros.count()
    registros_com_foto   = registros.exclude(foto='').count()
    registros_com_gps    = registros.filter(latitude__isnull=False, longitude__isnull=False).count()
    dias_trabalhados     = registros.values('data_hora__date').distinct().count()

    # ── Agrupar por data no fuso horário de Brasília ──────────────────────
    # IMPORTANTE: usar timezone.localtime() antes de .date() para evitar
    # que registros feitos entre 21h e 00h (Brasília) apareçam no dia seguinte
    # (o banco armazena em UTC, e sem localtime() um registro das 23:30 BRT
    # aparece como 02:30 UTC do dia seguinte).
    registros_por_data = defaultdict(list)
    for registro in registros:
        data_local = timezone.localtime(registro.data_hora).date()
        registros_por_data[data_local].append(registro)

    # Ordenar datas (mais recente primeiro)
    registros_por_data = dict(sorted(registros_por_data.items(), reverse=True))

    context = {
        "registros_por_data": registros_por_data,
        "data_inicio":        data_inicio,
        "data_fim":           data_fim,
        "tipo_filtro":        tipo_filtro,
        "origem_filtro":      origem_filtro,
        "total_registros":    total_registros,
        "registros_com_foto": registros_com_foto,
        "registros_com_gps":  registros_com_gps,
        "dias_trabalhados":   dias_trabalhados,
    }

    return render(request, "jornada/historico.html", context)


@login_required
def solicitar_ajuste_view(request, registro_id):
    """Solicita ajuste de um registro de ponto."""
    usuario = request.user
    empresa = request.empresa

    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")

    registro = get_object_or_404(
        RegistroPonto,
        id=registro_id,
        empresa=empresa,
        usuario=usuario,
        status=StatusRegistro.ATIVO,
    )

    if request.method == "POST":
        data_desejada = request.POST.get("data_desejada")
        hora_desejada = request.POST.get("hora_desejada")
        justificativa = request.POST.get("justificativa")

        if not data_desejada or not hora_desejada or not justificativa:
            messages.error(request, "Preencha todos os campos obrigatórios.")
            return redirect("jornada:solicitar_ajuste", registro_id=registro_id)

        try:
            from datetime import datetime
            data_hora_desejada = datetime.strptime(
                f"{data_desejada} {hora_desejada}",
                "%Y-%m-%d %H:%M"
            )
            data_hora_desejada = timezone.make_aware(data_hora_desejada)

            SolicitacaoAjusteService.criar_solicitacao(
                solicitante=usuario,
                empresa=empresa,
                registro_original=registro,
                data_hora_desejada=data_hora_desejada,
                justificativa=justificativa,
            )

            messages.success(
                request,
                "Solicitação de ajuste enviada com sucesso! Aguarde a análise de um administrador."
            )
            return redirect("jornada:historico")

        except Exception as e:
            messages.error(request, f"Erro ao criar solicitação: {str(e)}")

    context = {
        "registro": registro,
    }

    return render(request, "jornada/solicitar_ajuste.html", context)

@login_required
def listar_solicitacoes_view(request):
    """Lista solicitações de ajuste."""
    usuario = request.user
    empresa = request.empresa

    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")

    status_filtro = request.GET.get("status")

    if usuario.eh_administrador:
        solicitacoes = SolicitacaoAjuste.objects.filter(empresa=empresa)
    else:
        solicitacoes = SolicitacaoAjuste.objects.filter(
            empresa=empresa,
            solicitante=usuario,
        )

    if status_filtro:
        solicitacoes = solicitacoes.filter(status=status_filtro)

    solicitacoes = solicitacoes.select_related(
        "solicitante",
        "registro_original",
        "analisado_por",
    ).order_by("-criado_em")

    pendentes = SolicitacaoAjuste.objects.filter(
        empresa=empresa,
        status=SolicitacaoAjuste.StatusSolicitacao.PENDENTE,
    ).count()

    context = {
        "solicitacoes": solicitacoes,
        "status_filtro": status_filtro,
        "pendentes": pendentes,
    }

    return render(request, "jornada/solicitacoes.html", context)


@login_required
def analisar_solicitacao_view(request, solicitacao_id):
    """Aprova ou rejeita uma solicitação de ajuste (apenas admin)."""
    usuario = request.user
    empresa = request.empresa

    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")

    if not usuario.eh_administrador:
        messages.error(request, "Você não tem permissão para analisar solicitações.")
        return redirect("jornada:listar_solicitacoes")

    solicitacao = get_object_or_404(
        SolicitacaoAjuste,
        id=solicitacao_id,
        empresa=empresa,
        status=SolicitacaoAjuste.StatusSolicitacao.PENDENTE,
    )

    if request.method == "POST":
        acao = request.POST.get("acao")
        observacao = request.POST.get("observacao", "")
        ip_origem = get_client_ip(request)

        try:
            if acao == "aprovar":
                SolicitacaoAjusteService.aprovar_solicitacao(
                    solicitacao=solicitacao,
                    analisado_por=usuario,
                    observacao_analise=observacao,
                    ip_origem=ip_origem,
                )
                messages.success(request, "Solicitação aprovada com sucesso!")

            elif acao == "rejeitar":
                if not observacao:
                    messages.error(request, "Justificativa obrigatória para rejeição.")
                    return redirect("jornada:analisar_solicitacao", solicitacao_id=solicitacao_id)

                SolicitacaoAjusteService.rejeitar_solicitacao(
                    solicitacao=solicitacao,
                    analisado_por=usuario,
                    observacao_analise=observacao,
                    ip_origem=ip_origem,
                )
                messages.success(request, "Solicitação rejeitada.")

            return redirect("jornada:listar_solicitacoes")

        except Exception as e:
            messages.error(request, f"Erro ao analisar solicitação: {str(e)}")

    context = {
        "solicitacao": solicitacao,
    }

    return render(request, "jornada/analisar_solicitacao.html", context)


@login_required
def gerenciar_locais_view(request):
    """Gerenciar locais permitidos (apenas admin)."""
    usuario = request.user
    empresa = request.empresa

    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")

    if not usuario.eh_administrador:
        messages.error(request, "Você não tem permissão para gerenciar locais.")
        return redirect("jornada:painel")

    if request.method == "POST":
        acao = request.POST.get("acao")

        if acao == "criar":
            nome = request.POST.get("nome")
            latitude = request.POST.get("latitude")
            longitude = request.POST.get("longitude")
            raio_metros = request.POST.get("raio_metros")

            try:
                LocalPermitido.objects.create(
                    empresa=empresa,
                    nome=nome,
                    latitude=Decimal(latitude),
                    longitude=Decimal(longitude),
                    raio_metros=int(raio_metros),
                )
                messages.success(request, f"Local '{nome}' cadastrado com sucesso!")
            except Exception as e:
                messages.error(request, f"Erro ao cadastrar local: {str(e)}")

        elif acao == "deletar":
            local_id = request.POST.get("local_id")
            try:
                local = LocalPermitido.objects.get(id=local_id, empresa=empresa)
                local.delete()
                messages.success(request, "Local removido com sucesso!")
            except Exception as e:
                messages.error(request, f"Erro ao remover local: {str(e)}")

        return redirect("jornada:gerenciar_locais")

    locais = LocalPermitido.objects.filter(empresa=empresa).order_by("nome")

    context = {
        "locais": locais,
    }

    return render(request, "jornada/gerenciar_locais.html", context)


@login_required
def gerenciar_ips_view(request):
    """Gerenciar IPs permitidos (apenas admin)."""
    usuario = request.user
    empresa = request.empresa

    if not empresa:
        messages.error(request, "Você não está vinculado a nenhuma empresa.")
        return redirect("usuarios:perfil")

    if not usuario.eh_administrador:
        messages.error(request, "Você não tem permissão para gerenciar IPs.")
        return redirect("jornada:painel")

    if request.method == "POST":
        acao = request.POST.get("acao")

        if acao == "criar":
            nome = request.POST.get("nome")
            ip = request.POST.get("ip")

            try:
                IPPermitido.objects.create(
                    empresa=empresa,
                    nome=nome,
                    ip=ip,
                )
                messages.success(request, f"IP '{nome}' cadastrado com sucesso!")
            except Exception as e:
                messages.error(request, f"Erro ao cadastrar IP: {str(e)}")

        elif acao == "deletar":
            ip_id = request.POST.get("ip_id")
            try:
                ip_obj = IPPermitido.objects.get(id=ip_id, empresa=empresa)
                ip_obj.delete()
                messages.success(request, "IP removido com sucesso!")
            except Exception as e:
                messages.error(request, f"Erro ao remover IP: {str(e)}")

        return redirect("jornada:gerenciar_ips")

    ips = IPPermitido.objects.filter(empresa=empresa).order_by("nome")

    context = {
        "ips": ips,
    }

    return render(request, "jornada/gerenciar_ips.html", context)


@login_required
def detectar_ip_view(request):
    """Retorna o IP do cliente considerando proxies reversos."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    return JsonResponse({'ip': ip})