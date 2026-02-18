"""
Configurações para ambiente de desenvolvimento.

Como usar:
    python manage.py runserver
    (o .env é carregado automaticamente pelo base.py via django-environ)

Caso precise apontar para um .env diferente:
    ENV_FILE=.env.local python manage.py runserver
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ── Carrega o .env local explicitamente, garantindo que as variáveis
#    estejam disponíveis mesmo que o shell não as tenha exportado.
_BASE_DIR = Path(__file__).resolve().parent.parent
_env_file = _BASE_DIR / os.environ.get("ENV_FILE", ".env")

if _env_file.exists():
    load_dotenv(_env_file, override=True)

from .base import *  # noqa: E402, F403

# ============================================================
# SEGURANÇA
# ============================================================
DEBUG = True
ALLOWED_HOSTS = ["*"]
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-nao-usar-em-producao")

# ============================================================
# BANCO DE DADOS
# Sobrescreve o base.py para garantir que usa o .env local.
# ============================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME":     os.environ.get("DB_NAME",     "ontime_db"),
        "USER":     os.environ.get("DB_USER",     "ontime_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST":     os.environ.get("DB_HOST",     "localhost"),
        "PORT":     os.environ.get("DB_PORT",     "5433"),
        "OPTIONS": {
            "options": "-c timezone=America/Sao_Paulo",
        },
        # Mantém conexões abertas entre requests para ganho de performance
        "CONN_MAX_AGE": 0,
    }
}

# ============================================================
# E-MAIL — imprime no console, sem servidor SMTP necessário
# ============================================================
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ============================================================
# CACHE — usa memória local, sem Redis obrigatório
# ============================================================
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ============================================================
# CELERY — aceita rodar sem Redis em dev (tasks executadas inline)
# ============================================================
CELERY_TASK_ALWAYS_EAGER = True        # Executa tasks de forma síncrona
CELERY_TASK_EAGER_PROPAGATES = True    # Propaga exceções para facilitar debug

# ============================================================
# SEGURANÇA — relaxada em dev
# ============================================================
CSRF_COOKIE_SECURE   = False
SESSION_COOKIE_SECURE = False

# ============================================================
# LOGGING — verboso em dev, mas organizado
# ============================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colorido": {
            "format": "\033[36m{asctime}\033[0m \033[1m{levelname:<8}\033[0m \033[33m{name}\033[0m {message}",
            "style": "{",
            "datefmt": "%H:%M:%S",
        },
        "simples": {
            "format": "{asctime} {levelname:<8} {name} {message}",
            "style": "{",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "colorido",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        # Queries SQL — ative apenas quando precisar debugar o banco
        "django.db.backends": {
            "handlers": ["console"],
            "level": os.environ.get("SQL_LOG_LEVEL", "WARNING"),
            "propagate": False,
        },
        # Apps do projeto — DEBUG completo
        "nucleo":       {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "jornada":      {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "usuarios":     {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "empresas":     {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "banco_horas":  {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "fechamentos":  {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "auditoria":    {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}