#!/usr/bin/env bash
# ==============================================================================
# Script de Execução e Orquestração da Plataforma de Clustering de Avaliações
# ==============================================================================

set -euo pipefail

DIRETORIO_PROJETO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${DIRETORIO_PROJETO}"

# Cores para saída amigável no terminal
VERDE="\033[0;32m"
AZUL="\033[0;34m"
AMARELO="\033[1;33m"
VERMELHO="\033[0;31m"
RESET="\033[0m"

log_info() {
    echo -e "${AZUL}[INFO]${RESET} $1"
}

log_sucesso() {
    echo -e "${VERDE}[SUCESSO]${RESET} $1"
}

log_aviso() {
    echo -e "${AMARELO}[AVISO]${RESET} $1"
}

log_erro() {
    echo -e "${VERMELHO}[ERRO]${RESET} $1"
}

# 1. Carrega variáveis de ambiente do .env se existir
if [[ -f "${DIRETORIO_PROJETO}/.env" ]]; then
    log_info "Carregando variáveis de ambiente de .env..."
    set -a
    source "${DIRETORIO_PROJETO}/.env"
    set +a
fi

# 2. Localiza e ativa o ambiente virtual Python
PYTHON_BIN="${DIRETORIO_PROJETO}/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
    log_erro "Ambiente virtual Python não encontrado em .venv/bin/python."
    log_erro "Por favor, crie o ambiente virtual com 'python3 -m venv .venv' e instale as dependências."
    exit 1
fi

exibir_ajuda() {
    echo -e "
${VERDE}Uso: ./executar.sh [COMANDO] [OPÇÕES]${RESET}

${AZUL}Comandos disponíveis:${RESET}
  ${AMARELO}pipeline [ID] [--coletar]${RESET}  Executa o pipeline completo (leitura Bronze -> Silver -> Gold -> Clustering -> Relatório).
                                  Exemplo: ./executar.sh pipeline 730 --coletar
  ${AMARELO}api [--docker] [-p P]${RESET}    Inicia o servidor REST FastAPI (local ou no Docker Compose com --docker).
                                  Exemplo: ./executar.sh api --docker
  ${AMARELO}api-docker${RESET}                 Inicia a API FastAPI diretamente no Docker Compose com build.
  ${AMARELO}api-down${RESET}                   Encerra o contêiner da API FastAPI no Docker Compose.
  ${AMARELO}infra${RESET}                      Inicia os serviços de infraestrutura (RustFS S3, MLflow, Postgres, Grafana).
  ${AMARELO}infra-down${RESET}                 Encerra os serviços de infraestrutura em execução.
  ${AMARELO}testes${RESET} (ou test)            Executa a suíte de validação: ruff, pytest e checagem de tipos estrita (pyright).
  ${AMARELO}status${RESET}                     Verifica o status dos contêineres Docker e conectividade dos serviços.
  ${AMARELO}ajuda${RESET}                      Exibe esta mensagem de ajuda.
"
}

COMANDO="${1:-ajuda}"

case "${COMANDO}" in
    pipeline)
        shift || true
        IDENTIFICADOR="730"
        FLAGS=()

        while [[ $# -gt 0 ]]; do
            case "$1" in
                --coletar|-c)
                    FLAGS+=("--coletar")
                    shift
                    ;;
                --relatorio|-r)
                    FLAGS+=("--relatorio" "$2")
                    shift 2
                    ;;
                -*)
                    FLAGS+=("$1")
                    shift
                    ;;
                *)
                    IDENTIFICADOR="$1"
                    shift
                    ;;
            esac
        done

        log_info "Iniciando execução do pipeline para o jogo/identificador '${IDENTIFICADOR}'..."
        "${PYTHON_BIN}" "${DIRETORIO_PROJETO}/main.py" pipeline --identificador "${IDENTIFICADOR}" "${FLAGS[@]}"
        log_sucesso "Execução do pipeline finalizada!"
        ;;

    api)
        shift || true
        MODO_DOCKER=false
        ARGS=()
        for arg in "$@"; do
            if [[ "$arg" == "--docker" || "$arg" == "-d" ]]; then
                MODO_DOCKER=true
            else
                ARGS+=("$arg")
            fi
        done

        if [[ "${MODO_DOCKER}" == "true" ]]; then
            log_info "Subindo a API FastAPI via Docker Compose..."
            docker compose --profile servico_ml --profile api up -d --build api
            log_sucesso "API FastAPI em execução no Docker Compose (http://localhost:8000)!"
        else
            log_info "Iniciando servidor de API FastAPI localmente..."
            "${PYTHON_BIN}" "${DIRETORIO_PROJETO}/main.py" api "${ARGS[@]}"
        fi
        ;;

    api-docker)
        shift || true
        log_info "Subindo a API FastAPI via Docker Compose com build..."
        docker compose --profile servico_ml --profile api up -d --build api
        log_sucesso "API FastAPI em execução no Docker Compose (http://localhost:8000)!"
        ;;

    api-down)
        log_info "Parando o contêiner da API FastAPI no Docker Compose..."
        docker compose stop api
        log_sucesso "Contêiner da API finalizado com sucesso."
        ;;

    infra)
        log_info "Subindo contêineres do Docker Compose (RustFS, Postgres, MLflow, Prometheus, Grafana)..."
        docker compose --profile servico_ml --profile observabilidade up -d
        log_sucesso "Serviços de infraestrutura iniciados com sucesso!"
        ;;

    infra-down)
        log_info "Parando serviços de infraestrutura do Docker Compose..."
        docker compose --profile servico_ml --profile observabilidade down
        log_sucesso "Serviços de infraestrutura encerrados."
        ;;

    testes|test)
        log_info "1/3. Executando linter e formatação (ruff)..."
        "${DIRETORIO_PROJETO}/.venv/bin/ruff" check app tests main.py
        log_sucesso "Ruff aprovado com sucesso!"

        log_info "2/3. Executando suíte de testes unitários (pytest)..."
        "${DIRETORIO_PROJETO}/.venv/bin/pytest"
        log_sucesso "Pytest aprovado com sucesso!"

        log_info "3/3. Executando checagem estrita de tipos estáticos (pyright)..."
        "${DIRETORIO_PROJETO}/.venv/bin/pyright"
        log_sucesso "Pyright: 0 erros, 0 avisos!"
        ;;

    status)
        log_info "Verificando status dos contêineres Docker..."
        docker compose ps
        ;;

    ajuda|help|-h|--help)
        exibir_ajuda
        ;;

    *)
        log_erro "Comando desconhecido: '${COMANDO}'"
        exibir_ajuda
        exit 1
        ;;
esac
