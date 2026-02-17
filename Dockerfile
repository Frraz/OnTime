FROM python:3.12-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    gettext \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copiar código
COPY . .

# Criar diretórios para arquivos estáticos e media
RUN mkdir -p staticfiles media

# Criar usuário não-root
RUN useradd -m -u 1000 ontime && chown -R ontime:ontime /app
USER ontime

# Expor porta
EXPOSE 8000

# Script de entrada
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "configuracoes.wsgi:application"]