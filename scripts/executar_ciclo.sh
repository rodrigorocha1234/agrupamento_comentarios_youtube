#!/usr/bin/env bash
# ==============================================================================
# Script de disparo do ExecutorCiclo (Pipeline Diário YouTube -> S3 Lakehouse -> MLflow)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
DIRETORIO_RAIZ="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$DIRETORIO_RAIZ"

# Carrega variáveis de ambiente se o arquivo .env existir
if [ -f "$DIRETORIO_RAIZ/.env" ]; then
    echo ">> Carregando variáveis de ambiente de .env..."
    set -a
    # shellcheck disable=SC1091
    source "$DIRETORIO_RAIZ/.env"
    set +a
fi

# Detecta modo Docker caso informado via flag --docker
USAR_DOCKER=false
ARGUMENTOS=()

for arg in "$@"; do
    if [ "$arg" == "--docker" ]; then
        USAR_DOCKER=true
    else
        ARGUMENTOS+=("$arg")
    fi
done

# Se o usuário passou um ID de canal como primeiro argumento posicional sem flag
if [ ${#ARGUMENTOS[@]} -gt 0 ]; then
    PRIMEIRO_ARG="${ARGUMENTOS[0]}"
    if [[ ! "$PRIMEIRO_ARG" =~ ^- ]]; then
        ARGUMENTOS=("--canal" "$PRIMEIRO_ARG" "${ARGUMENTOS[@]:1}")
    fi
fi

if [ "$USAR_DOCKER" = true ]; then
    echo ">> Executando ExecutorCiclo dentro do container 'api' (Docker Compose)..."
    docker compose exec api python -m app.orquestracao_pipeline "${ARGUMENTOS[@]}"
else
    # Detecta interpretador Python local
    if [ -x "$DIRETORIO_RAIZ/.venv/bin/python" ]; then
        PYTHON_BIN="$DIRETORIO_RAIZ/.venv/bin/python"
    elif command -v python3 &> /dev/null; then
        PYTHON_BIN="python3"
    elif command -v python &> /dev/null; then
        PYTHON_BIN="python"
    else
        echo ">> [ERRO] Interpretador Python não encontrado localmente (.venv/bin/python ou python3)."
        echo ">> Dica: utilize a flag --docker para rodar dentro do container Docker Compose."
        exit 1
    fi

    echo ">> Executando ExecutorCiclo via $PYTHON_BIN..."
    PYTHONPATH="$DIRETORIO_RAIZ" "$PYTHON_BIN" -m app.orquestracao_pipeline "${ARGUMENTOS[@]}"
fi
