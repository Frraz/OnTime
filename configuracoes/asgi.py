"""
Configuração ASGI para o projeto OnTime.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "configuracoes.desenvolvimento")

application = get_asgi_application()