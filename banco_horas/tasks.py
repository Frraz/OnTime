"""Tasks do Celery para banco de horas."""
from datetime import date, timedelta
from celery import shared_task
from django.utils import timezone

from empresas.models import Empresa
from usuarios.models import Usuario
from .services import BancoHorasService


@shared_task
def calcular_banco_horas_dia_anterior():
    """
    Task agendada para calcular banco de horas do dia anterior.
    Roda todo dia às 01:00.
    
    Não fecha a semana, apenas calcula as horas trabalhadas.
    """
    ontem = date.today() - timedelta(days=1)
    ano_iso = ontem.isocalendar()[0]
    semana_iso = ontem.isocalendar()[1]
    
    print(f"[CELERY] Calculando banco de horas para {ontem} ({ano_iso}S{semana_iso:02d})")
    
    total_calculados = 0
    total_erros = 0
    
    # Iterar por todas as empresas ativas
    empresas = Empresa.objects.filter(ativa=True)
    
    for empresa in empresas:
        usuarios = Usuario.objects.filter(
            empresa=empresa,
            ativo=True,
        )
        
        for usuario in usuarios:
            try:
                # Calcular sem fechar
                BancoHorasService.calcular_saldo_semana(
                    usuario=usuario,
                    empresa=empresa,
                    ano=ano_iso,
                    semana=semana_iso,
                    fechar=False,
                )
                total_calculados += 1
                
            except Exception as e:
                total_erros += 1
                print(f"[CELERY] Erro ao calcular para {usuario.username}: {str(e)}")
    
    print(f"[CELERY] Cálculo concluído: {total_calculados} calculados, {total_erros} erros")
    
    return {
        'calculados': total_calculados,
        'erros': total_erros,
        'data': str(ontem),
    }


@shared_task
def recalcular_saldos_usuario(usuario_id, empresa_id, ano_inicio, semana_inicio):
    """
    Task para recalcular todos os saldos de um usuário a partir de uma semana.
    Útil quando há ajustes retroativos.
    """
    from usuarios.models import Usuario
    from empresas.models import Empresa
    
    try:
        usuario = Usuario.objects.get(id=usuario_id)
        empresa = Empresa.objects.get(id=empresa_id)
        
        # Pegar a semana atual
        hoje = date.today()
        ano_atual = hoje.isocalendar()[0]
        semana_atual = hoje.isocalendar()[1]
        
        ano = ano_inicio
        semana = semana_inicio
        
        recalculados = 0
        
        # Recalcular até a semana atual
        while (ano < ano_atual) or (ano == ano_atual and semana <= semana_atual):
            BancoHorasService.calcular_saldo_semana(
                usuario=usuario,
                empresa=empresa,
                ano=ano,
                semana=semana,
                fechar=False,  # Não fechar ao recalcular
            )
            recalculados += 1
            
            # Próxima semana
            semana += 1
            if semana > 52:
                semana = 1
                ano += 1
        
        return {
            'status': 'success',
            'recalculados': recalculados,
            'usuario': usuario.username,
        }
        
    except Exception as e:
        return {'status': 'error', 'message': str(e)}