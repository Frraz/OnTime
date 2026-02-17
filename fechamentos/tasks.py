"""Tasks do Celery para fechamentos."""
from datetime import date, timedelta
from celery import shared_task
from django.utils import timezone

from empresas.models import Empresa
from usuarios.models import Usuario
from banco_horas.services import BancoHorasService
from nucleo.excecoes import FechamentoJaRealizado


@shared_task
def fechar_semanas_automatico():
    """
    Task agendada para fechar automaticamente as semanas anteriores.
    Roda toda segunda-feira às 00:05.
    
    Fecha a semana que acabou de terminar (domingo anterior).
    """
    hoje = date.today()
    
    # Calcular a semana anterior (que terminou no domingo)
    # Se hoje é segunda, domingo foi há 1 dia
    dias_desde_domingo = (hoje.weekday() + 1) % 7 or 7
    domingo_anterior = hoje - timedelta(days=dias_desde_domingo)
    
    # Descobrir ano e semana ISO
    ano_iso = domingo_anterior.isocalendar()[0]
    semana_iso = domingo_anterior.isocalendar()[1]
    
    print(f"[CELERY] Iniciando fechamento automático para {ano_iso}S{semana_iso:02d}")
    
    total_fechados = 0
    total_erros = 0
    
    # Iterar por todas as empresas ativas
    empresas = Empresa.objects.filter(ativa=True)
    
    for empresa in empresas:
        print(f"[CELERY] Processando empresa: {empresa.razao_social}")
        
        # Pegar todos os usuários ativos da empresa
        usuarios = Usuario.objects.filter(
            empresa=empresa,
            ativo=True,
        )
        
        for usuario in usuarios:
            try:
                # Tentar fechar a semana
                BancoHorasService.calcular_saldo_semana(
                    usuario=usuario,
                    empresa=empresa,
                    ano=ano_iso,
                    semana=semana_iso,
                    fechar=True,
                    fechado_por=None,  # Fechamento automático
                )
                total_fechados += 1
                print(f"[CELERY] ✓ Fechado para {usuario.username}")
                
            except FechamentoJaRealizado:
                # Já estava fechado, tudo bem
                print(f"[CELERY] - Já fechado para {usuario.username}")
                pass
                
            except Exception as e:
                total_erros += 1
                print(f"[CELERY] ✗ Erro ao fechar para {usuario.username}: {str(e)}")
    
    print(f"[CELERY] Fechamento concluído: {total_fechados} fechados, {total_erros} erros")
    
    return {
        'fechados': total_fechados,
        'erros': total_erros,
        'ano': ano_iso,
        'semana': semana_iso,
    }


@shared_task
def fechar_semana_usuario(usuario_id, empresa_id, ano, semana, fechado_por_id=None):
    """
    Task para fechar a semana de um usuário específico.
    Pode ser chamada manualmente ou por outra task.
    """
    from usuarios.models import Usuario
    from empresas.models import Empresa
    
    try:
        usuario = Usuario.objects.get(id=usuario_id)
        empresa = Empresa.objects.get(id=empresa_id)
        fechado_por = Usuario.objects.get(id=fechado_por_id) if fechado_por_id else None
        
        BancoHorasService.calcular_saldo_semana(
            usuario=usuario,
            empresa=empresa,
            ano=ano,
            semana=semana,
            fechar=True,
            fechado_por=fechado_por,
        )
        
        return {'status': 'success', 'usuario': usuario.username}
        
    except Exception as e:
        return {'status': 'error', 'message': str(e)}