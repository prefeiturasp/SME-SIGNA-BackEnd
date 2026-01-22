#########################################
# STAGE 1 — BUILD (instala dependências)
#########################################
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia apenas requirements para cache eficiente
COPY requirements ./requirements

# Instala dependências em uma pasta isolada
RUN pip install --upgrade pip && \
    pip install --prefix=/install -r requirements/production.txt


#########################################
# STAGE 2 — FINAL IMAGE (produção)
#########################################
FROM python:3.11-slim AS final

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependências essenciais para Postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia dependências já instaladas
COPY --from=builder /install /usr/local

# Copia o projeto inteiro
COPY . .

# Criar pastas obrigatórias de produção
RUN mkdir -p /app/staticfiles


# ENTRYPOINT 
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# Expor porta da aplicação
EXPOSE 8000

#########################################
# Comando final — Gunicorn em modo produção
#########################################
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120"]
