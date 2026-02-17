"""Configurações do projeto OnTime."""
# Isso garante que o Celery seja sempre importado quando o Django inicia
from .celery import app as celery_app

__all__ = ('celery_app',)