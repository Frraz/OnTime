"""Configuração do Celery para o OnTime."""
import os
from celery import Celery
from celery.schedules import crontab

# Define o módulo de settings padrão
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configuracoes.desenvolvimento')

app = Celery('ontime')

# Carregar configurações do Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descobrir tasks automaticamente
app.autodiscover_tasks()

# Configurar beat schedule (tarefas agendadas)
app.conf.beat_schedule = {
    'fechar-semanas-automaticamente': {
        'task': 'fechamentos.tasks.fechar_semanas_automatico',
        'schedule': crontab(hour=0, minute=5, day_of_week=1),  # Segunda-feira às 00:05
    },
    'calcular-banco-horas-diario': {
        'task': 'banco_horas.tasks.calcular_banco_horas_dia_anterior',
        'schedule': crontab(hour=1, minute=0),  # Todo dia às 01:00
    },
}

app.conf.timezone = 'America/Sao_Paulo'