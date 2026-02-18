"""
Configurações de produção do OnTime.

Requer as seguintes variáveis no .env do servidor:
    SECRET_KEY, ALLOWED_HOSTS, DB_NAME, DB_USER, DB_PASSWORD,
    DB_HOST, DB_PORT, REDIS_URL (opcional: EMAIL_*)
"""
from .base import *  # noqa: F403
from .base import env, BASE_DIR

# ============================================================
# SEGURANÇA
# ============================================================
DEBUG = False
SECRET_KEY   = env("SECRET_KEY")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# ============================================================
# CSRF E HTTPS
# ============================================================
CSRF_TRUSTED_ORIGINS = [
    "https://ontime.ferzion.com.br",
    "https://www.ontime.ferzion.com.br",
]

SECURE_BROWSER_XSS_FILTER   = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS          = 31536000   # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD          = True
SECURE_SSL_REDIRECT          = True
SESSION_COOKIE_SECURE        = True
CSRF_COOKIE_SECURE           = True
X_FRAME_OPTIONS              = "DENY"

# ============================================================
# BANCO DE DADOS
# Sobrescreve o base.py para garantir CONN_MAX_AGE em produção.
# ============================================================
DATABASES = {
    "default": {
        "ENGINE":   "django.db.backends.postgresql",
        "NAME":     env("DB_NAME",     default="ontime"),
        "USER":     env("DB_USER",     default="ontime_user"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST":     env("DB_HOST",     default="localhost"),
        "PORT":     env("DB_PORT",     default="5433"),
        "CONN_MAX_AGE": 60,  # Reutiliza conexões por 60s (performance)
        "OPTIONS": {
            "options": "-c timezone=America/Sao_Paulo",
        },
    }
}

# ============================================================
# CELERY
# ============================================================
CELERY_BROKER_URL     = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/0")

# ============================================================
# ARQUIVOS ESTÁTICOS E MÍDIA
# Mantém os mesmos caminhos do base.py — apenas confirma os valores.
# ============================================================
STATIC_URL  = "/estaticos/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL   = "/midia/"
MEDIA_ROOT  = BASE_DIR / "midia"

# ============================================================
# E-MAIL (SMTP — só ativo se EMAIL_HOST_USER estiver no .env)
# ============================================================
if env("EMAIL_HOST_USER", default=""):
    EMAIL_BACKEND       = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST          = env("EMAIL_HOST",     default="smtp.gmail.com")
    EMAIL_PORT          = env.int("EMAIL_PORT", default=587)
    EMAIL_USE_TLS       = env.bool("EMAIL_USE_TLS", default=True)
    EMAIL_HOST_USER     = env("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
    DEFAULT_FROM_EMAIL  = env("EMAIL_HOST_USER")

# ============================================================
# LOGGING — erros em arquivo + tudo no console (para systemd/gunicorn)
# ============================================================
_LOG_DIR = BASE_DIR / "logs"
_LOG_DIR.mkdir(exist_ok=True)  # Cria a pasta se não existir

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {message}",
            "style":  "{",
        },
        "simples": {
            "format": "{levelname} {asctime} {message}",
            "style":  "{",
        },
    },
    "handlers": {
        "console": {
            "class":     "logging.StreamHandler",
            "formatter": "simples",
            "level":     "INFO",
        },
        "arquivo_erros": {
            "class":     "logging.handlers.RotatingFileHandler",
            "filename":  _LOG_DIR / "django_errors.log",
            "maxBytes":  10 * 1024 * 1024,  # 10 MB por arquivo
            "backupCount": 5,               # mantém os últimos 5 arquivos
            "formatter": "verbose",
            "level":     "ERROR",
        },
        "arquivo_info": {
            "class":     "logging.handlers.RotatingFileHandler",
            "filename":  _LOG_DIR / "django_info.log",
            "maxBytes":  10 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "simples",
            "level":     "INFO",
        },
    },
    "root": {
        "handlers": ["console", "arquivo_erros", "arquivo_info"],
        "level":    "INFO",
    },
    "loggers": {
        # Silencia logs muito verbosos de libs de terceiros
        "django.security.DisallowedHost": {
            "handlers":  ["arquivo_erros"],
            "level":     "ERROR",
            "propagate": False,
        },
        "django.request": {
            "handlers":  ["arquivo_erros", "console"],
            "level":     "ERROR",
            "propagate": False,
        },
    },
}