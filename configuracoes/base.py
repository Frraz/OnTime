"""
Configurações base do OnTime.
Compartilhadas entre todos os ambientes (desenvolvimento, produção, testes).

Variáveis de ambiente são lidas do arquivo .env na raiz do projeto.
"""
import os
from pathlib import Path

import environ

# ============================================================
# DIRETÓRIO BASE E VARIÁVEIS DE AMBIENTE
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

# ============================================================
# SEGURANÇA (valores padrão seguros — sobrescreva nos ambientes)
# ============================================================
SECRET_KEY = env("SECRET_KEY", default="chave-insegura-apenas-para-desenvolvimento")
DEBUG = False
ALLOWED_HOSTS = []

# ============================================================
# APLICAÇÕES
# ============================================================
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

TERCEIROS_APPS = [
    "django_htmx",
]

PROJETO_APPS = [
    "nucleo.apps.NucleoConfig",
    "empresas.apps.EmpresasConfig",
    "usuarios.apps.UsuariosConfig",
    "jornada.apps.JornadaConfig",
    "banco_horas.apps.BancoHorasConfig",
    "fechamentos.apps.FechamentosConfig",
    "auditoria.apps.AuditoriaConfig",
]

INSTALLED_APPS = DJANGO_APPS + TERCEIROS_APPS + PROJETO_APPS

# ============================================================
# MIDDLEWARE
# ============================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "nucleo.middleware.EmpresaAtivaMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "configuracoes.urls"
WSGI_APPLICATION = "configuracoes.wsgi.application"

# ============================================================
# TEMPLATES
# ============================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "nucleo.context_processors.empresa_ativa",
            ],
        },
    },
]

# ============================================================
# BANCO DE DADOS
# ============================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME":     env("DB_NAME",     default="ontime_db"),
        "USER":     env("DB_USER",     default="ontime_user"),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST":     env("DB_HOST",     default="localhost"),
        "PORT":     env("DB_PORT",     default="5433"),
        "OPTIONS": {
            "options": "-c timezone=America/Sao_Paulo",
        },
    }
}

# ============================================================
# AUTENTICAÇÃO
# ============================================================
AUTH_USER_MODEL = "usuarios.Usuario"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL          = "/usuarios/login/"
LOGIN_REDIRECT_URL = "/jornada/painel/"
LOGOUT_REDIRECT_URL = "/usuarios/login/"

# ============================================================
# INTERNACIONALIZAÇÃO
# ============================================================
LANGUAGE_CODE = "pt-br"
TIME_ZONE     = "America/Sao_Paulo"
USE_I18N      = True
USE_TZ        = True

# ============================================================
# ARQUIVOS ESTÁTICOS E MÍDIA
# ============================================================
STATIC_URL       = "/estaticos/"
STATICFILES_DIRS = [BASE_DIR / "estaticos"]
STATIC_ROOT      = BASE_DIR / "staticfiles"

MEDIA_URL  = "/midia/"
MEDIA_ROOT = BASE_DIR / "midia"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ============================================================
# SESSÃO
# ============================================================
SESSION_ENGINE        = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE    = 28800   # 8 horas
SESSION_COOKIE_HTTPONLY = True

# ============================================================
# CELERY
# ============================================================
CELERY_BROKER_URL      = env("CELERY_BROKER_URL",      default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND  = env("CELERY_RESULT_BACKEND",  default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT  = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE          = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT    = 30 * 60  # 30 minutos