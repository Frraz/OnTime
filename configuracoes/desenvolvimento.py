"""Configurações para ambiente de desenvolvimento."""
from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Barra de debug (opcional, instalar django-debug-toolbar)
# INSTALLED_APPS += ["debug_toolbar"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Logs mais verbosos em desenvolvimento
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}