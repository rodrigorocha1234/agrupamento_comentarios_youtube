# ==============================================================================
# Dockerfile para o Serviço REST FastAPI de Clustering de Avaliações
# ==============================================================================

FROM python:3.12-slim AS base

# Evita geração de arquivos .pyc e força flush imediato de stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=America/Sao_Paulo

WORKDIR /app

# Instala ferramentas mínimas de sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivo de manifesto e instala dependências do projeto
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copia código da aplicação e arquivos base
COPY app/ ./app/
COPY config/ ./config/
COPY main.py .

# Porta padrão de escuta da FastAPI
EXPOSE 8000

# Verificação de integridade nativa do container
HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=15s \
    CMD curl -f http://localhost:8000/health || exit 1

# Ponto de entrada padrão: API REST via Uvicorn
CMD ["python", "main.py", "api", "--host", "0.0.0.0", "--porta", "8000"]
