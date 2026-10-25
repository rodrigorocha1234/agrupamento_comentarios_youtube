#!/usr/bin/env bash
# ==============================================================================
# Steam Reviews Clustering v4.1 — Script Oficial de Execução do Projeto
# ==============================================================================
set -eo pipefail

DIRETORIO_PROJETO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${DIRETORIO_PROJETO}"

# Paleta de Cores ANSI
COR_RESET="\033[0m"
COR_NEGRITO="\033[1m"
COR_VERDE="\033[38;5;48m"
COR_AZUL="\033[38;5;75m"
COR_CIANO="\033[38;5;81m"
COR_AMARELO="\033[38;5;220m"
COR_VERMELHO="\033[38;5;196m"
COR_ROXO="\033[38;5;141m"
COR_CINZA="\033[38;5;244m"

# Banners e Funções de Log
log_info() {
    echo -e "${COR_AZUL}ℹ [INFO]${COR_RESET} $1"
}

log_sucesso() {
    echo -e "${COR_VERDE}✔ [SUCESSO]${COR_RESET} $1"
}

log_alerta() {
    echo -e "${COR_AMARELO}⚠ [ALERTA]${COR_RESET} $1"
}

log_erro() {
    echo -e "${COR_VERMELHO}✖ [ERRO]${COR_RESET} $1"
}

log_banner() {
    echo -e "${COR_ROXO}${COR_NEGRITO}"
    echo "========================================================================"
    echo "       STEAM REVIEWS CLUSTERING v4.1 — PIPELINE DE ENGENHARIA & ML      "
    echo "========================================================================"
    echo -e "${COR_RESET}"
}

# 1. Verificação e Ativação do Ambiente Virtual Python
PYTHON_BIN="${DIRETORIO_PROJETO}/.venv/bin/python"

verificar_ambiente_python() {
    log_info "Verificando ambiente virtual Python..."
    if [ -x "${DIRETORIO_PROJETO}/.venv/bin/python" ]; then
        # shellcheck disable=SC1091
        source .venv/bin/activate
        PYTHON_BIN="${DIRETORIO_PROJETO}/.venv/bin/python"
        log_sucesso "Ambiente virtual ativado (.venv)"
    elif [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
        PYTHON_BIN="$VIRTUAL_ENV/bin/python"
        log_sucesso "Ambiente virtual já ativo: $VIRTUAL_ENV"
    else
        log_alerta "Ambiente virtual .venv não encontrado na raiz."
        log_info "Criando ambiente virtual com Python 3.12..."
        python3.12 -m venv .venv || python3 -m venv .venv
        # shellcheck disable=SC1091
        source .venv/bin/activate
        PYTHON_BIN="${DIRETORIO_PROJETO}/.venv/bin/python"
        log_info "Instalando dependências essenciais..."
        "${PYTHON_BIN}" -m pip install --upgrade pip
        if [ -f "requirements.txt" ]; then
            "${PYTHON_BIN}" -m pip install -r requirements.txt
        fi
        log_sucesso "Ambiente virtual criado e configurado com sucesso!"
    fi

    # Confirma versão do Python
    PYTHON_VERSAO=$("${PYTHON_BIN}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log_info "Python detectado: v${PYTHON_VERSAO}"
}

# 2. Gerenciamento de Infraestrutura Docker Compose
subir_infraestrutura() {
    log_info "Iniciando microsserviços via Docker Compose..."
    docker compose --profile servico_ml --profile dashboard --profile api up -d

    log_info "Aguardando prontidão dos serviços (Storage, PostgreSQL, MLflow, Prometheus)..."
    sleep 3
    docker compose ps
    log_sucesso "Infraestrutura Docker Compose operacional!"
}

parar_infraestrutura() {
    log_info "Parando todos os serviços do Docker Compose..."
    docker compose --profile servico_ml --profile dashboard --profile api down
    log_sucesso "Todos os containers foram finalizados com segurança."
}

status_infraestrutura() {
    log_info "Status dos containers do Docker Compose:"
    docker compose ps
    echo ""
    log_info "Verificação de conectividade nas portas locais:"
    for porta in 5432 9000 5000 9090 3000 8000; do
        if nc -z localhost "$porta" 2>/dev/null; then
            echo -e "  Porta ${COR_CIANO}${porta}${COR_RESET}: ${COR_VERDE}ABERTA (Conectada)${COR_RESET}"
        else
            echo -e "  Porta ${COR_CIANO}${porta}${COR_RESET}: ${COR_CINZA}FECHADA (Inativa)${COR_RESET}"
        fi
    done
}

# 3. Execução dos Quality Gates (Linters, Strict Typing e Testes)
executar_quality_gates() {
    log_info "Iniciando execução rigorosa dos Quality Gates..."
    
    echo -e "\n${COR_CIANO}--- [1/3] Quality Gate de Estilo & Linter (Ruff) ---${COR_RESET}"
    ./.venv/bin/ruff check .
    log_sucesso "Ruff: 0 violações encontradas."

    echo -e "\n${COR_CIANO}--- [2/3] Quality Gate de Tipagem Estrita (Pyright Strict) ---${COR_RESET}"
    ./.venv/bin/pyright
    log_sucesso "Pyright: 0 erros de tipagem estrita (Zero Any)."

    echo -e "\n${COR_CIANO}--- [3/3] Quality Gate de Testes Automatizados (Pytest) ---${COR_RESET}"
    ./.venv/bin/pytest -v
    log_sucesso "Pytest: Todos os testes unitários e de integração foram aprovados!"
}

# 4. Execução da Coleta e Ingestão
executar_coleta() {
    local APPID="${1:-427520}"
    local MAX_PAGINAS="${2:-2}"
    log_info "Executando coleta paginada da Steam para AppID: ${APPID} (Limite: ${MAX_PAGINAS} páginas)..."
    "${PYTHON_BIN}" -m app.orquestracao_pipeline.orquestrador_principal --acao coleta --appid "${APPID}" --max-paginas "${MAX_PAGINAS}"
    log_sucesso "Coleta finalizada e persistida no staging com outbox!"
}

# 5. Execução do Treinamento e Clustering AutoML
executar_treinamento() {
    local APPID="${1:-427520}"
    local ALGORITMO="${2:-automl}"
    log_info "Executando pipeline de clustering (${ALGORITMO}) para AppID: ${APPID}..."
    "${PYTHON_BIN}" -m app.orquestracao_pipeline.orquestrador_principal --acao treinar --appid "${APPID}" --algoritmo "${ALGORITMO}"
    log_sucesso "Treinamento concluído e Camada Gold exportada para o Lakehouse!"
}

# 6. Inicialização da API REST FastAPI no Host
executar_servidor_api() {
    log_info "Iniciando servidor de aplicação FastAPI na porta 8000..."
    "${PYTHON_BIN}" -m uvicorn app.servico_api.aplicacao_fastapi:criar_aplicacao --factory --host 0.0.0.0 --port 8000 --reload
}

# 7. Abertura da Documentação HTML
abrir_documentacao() {
    log_info "Abrindo a documentação oficial HTML no navegador..."
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open documentacao/index.html
    elif command -v open >/dev/null 2>&1; then
        open documentacao/index.html
    else
        log_info "Servindo documentação via servidor HTTP local na porta 8080..."
        "${PYTHON_BIN}" -m http.server 8080 --directory documentacao
    fi
}

# 8. Execução do Ciclo Completo (End-to-End)
executar_ciclo_completo() {
    local APPID="${1:-427520}"
    log_banner
    log_info "Iniciando execução do ciclo completo de ponta a ponta para o jogo AppID: ${APPID}"

    verificar_ambiente_python
    subir_infraestrutura
    
    echo ""
    log_info "Executando validação rápida da suíte de testes..."
    ./.venv/bin/pytest tests/teste_api.py tests/teste_automl.py -v
    
    echo ""
    executar_coleta "${APPID}" 2
    
    echo ""
    executar_treinamento "${APPID}" "automl"

    echo -e "\n${COR_VERDE}${COR_NEGRITO}========================================================================${COR_RESET}"
    echo -e "${COR_VERDE}${COR_NEGRITO}          EXECUÇÃO DO PROJETO CONCLUÍDA COM SUCESSO ABSOLUTO!          ${COR_RESET}"
    echo -e "${COR_VERDE}${COR_NEGRITO}========================================================================${COR_RESET}\n"

    echo -e "${COR_CIANO}Painéis e Endpoints Disponíveis para Acesso Local:${COR_RESET}"
    echo -e "  • ${COR_NEGRITO}Documentação Interativa HTML:${COR_RESET} file://${DIRETORIO_PROJETO}/documentacao/index.html"
    echo -e "  • ${COR_NEGRITO}API REST FastAPI:${COR_RESET}            http://localhost:8000/docs"
    echo -e "  • ${COR_NEGRITO}Métricas Prometheus:${COR_RESET}         http://localhost:8000/metrics"
    echo -e "  • ${COR_NEGRITO}Dashboards do Grafana:${COR_RESET}       http://localhost:3000 (admin / Admin@2026)"
    echo -e "  • ${COR_NEGRITO}MLflow Tracking UI:${COR_RESET}          http://localhost:5000"
    echo -e "  • ${COR_NEGRITO}Storage RustFS/MinIO:${COR_RESET}        http://localhost:9000 (admin / admin1234)"
    echo -e "  • ${COR_NEGRITO}Prometheus TSDB:${COR_RESET}             http://localhost:9090\n"
}

# 9. Menu de Ajuda
exibir_ajuda() {
    log_banner
    echo -e "Uso: ${COR_VERDE}./executar_projeto.sh${COR_RESET} [COMANDO] [OPÇÕES]\n"
    echo -e "${COR_NEGRITO}Comandos Disponíveis:${COR_RESET}"
    echo -e "  ${COR_CIANO}tudo${COR_RESET} [appid]          Executa o ciclo completo ponta a ponta (Padrão: AppID 427520)"
    echo -e "  ${COR_CIANO}infra${COR_RESET}                 Sobe os microsserviços via Docker Compose (Profiles: servico_ml, dashboard, api)"
    echo -e "  ${COR_CIANO}parar${COR_RESET}                 Finaliza todos os containers Docker com segurança"
    echo -e "  ${COR_CIANO}status${COR_RESET}                Verifica o estado dos containers e das portas de rede"
    echo -e "  ${COR_CIANO}coleta${COR_RESET} [appid] [pag]  Executa apenas a coleta da Steam API para o staging transacional"
    echo -e "  ${COR_CIANO}treinar${COR_RESET} [appid] [alg] Executa o pipeline de clustering AutoML e exporta a Camada Gold"
    echo -e "  ${COR_CIANO}api${COR_RESET}                   Inicia o servidor da API REST FastAPI no host local (Porta 8000)"
    echo -e "  ${COR_CIANO}qa${COR_RESET} | ${COR_CIANO}testes${COR_RESET}            Executa os 3 Quality Gates (Ruff, Pyright Strict e Pytest)"
    echo -e "  ${COR_CIANO}doc${COR_RESET}                   Abre a documentação técnica HTML interativa no navegador"
    echo -e "  ${COR_CIANO}ajuda${COR_RESET}                 Exibe este menu informativo de ajuda\n"
    echo -e "${COR_NEGRITO}Exemplos de Uso:${COR_RESET}"
    echo "  ./executar_projeto.sh                    # Executa o ciclo completo com AppID 427520"
    echo "  ./executar_projeto.sh tudo 427520        # Executa o ciclo completo para um jogo específico"
    echo "  ./executar_projeto.sh treinar 427520     # Executa seleção AutoML e exportação Gold"
    echo "  ./executar_projeto.sh qa                 # Roda os Quality Gates (linters, tipagem e testes)"
    echo "  ./executar_projeto.sh doc                # Abre o index.html de arquitetura e manual de uso"
    echo ""
}

# Roteador Principal de Comandos
COMANDO="${1:-tudo}"

case "$COMANDO" in
    tudo|executar)
        executar_ciclo_completo "$2"
        ;;
    infra|subir)
        verificar_ambiente_python
        subir_infraestrutura
        ;;
    parar|down)
        parar_infraestrutura
        ;;
    status)
        status_infraestrutura
        ;;
    coleta)
        verificar_ambiente_python
        executar_coleta "$2" "$3"
        ;;
    treinar|treinamento)
        verificar_ambiente_python
        executar_treinamento "$2" "$3"
        ;;
    api)
        verificar_ambiente_python
        executar_servidor_api
        ;;
    qa|testes|teste)
        verificar_ambiente_python
        executar_quality_gates
        ;;
    doc|documentacao)
        abrir_documentacao
        ;;
    ajuda|-h|--help)
        exibir_ajuda
        ;;
    *)
        log_erro "Comando desconhecido: '$COMANDO'"
        exibir_ajuda
        exit 1
        ;;
esac
