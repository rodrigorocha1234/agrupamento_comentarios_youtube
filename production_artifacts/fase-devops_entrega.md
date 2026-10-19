# Handoff de Entrega — Fase 10: DevOps e Integração de Infraestrutura

**Persona Responsável:** `@devops`  
**Data:** 2026-10-13  
**Status:** ✅ **CONCLUÍDO COM SUCESSO**

---

## 1. Escopo Entregue e Auditoria de Infraestrutura
Conforme estritamente exigido em `rules/02-dados-e-persistencia.md` e `rules/04-governanca.md`, **nenhum compose paralelo foi criado** e nenhuma alteração destrutiva foi aplicada na infraestrutura existente.

### Serviços Inspecionados e Integrados:
1. **RustFS (S3 Gateway):**
   - Container: `storage` (`rustfs/rustfs:1.0.0-alpha.83`)
   - Portas: `9000` (API S3) e `9001` (Console)
   - Integração: Endpoint `http://127.0.0.1:9000`, credenciais `s3admin`/`s3admin`, `addressing_style: path`.
   - Provisionamento: Bucket `youtube-comentarios` verificado e garantido programaticamente.
2. **MLflow Server & PostgreSQL:**
   - Containers: `mlflow-server` e `mlflow-postgres`
   - Portas: `5000` (HTTP) e `5432` (DB)
   - Integração: Tracking URI `http://127.0.0.1:5000`. Testado com registro real de execuções, métricas e tags de manifesto S3.
3. **Observabilidade (Prometheus & Grafana):**
   - Containers: `prometheus` (porta `9090`) e `grafana` (porta `3000`).
   - Integração: Endpoint `/metrics` exposto na aplicação FastAPI (`app/coleta_metricas/middleware_prometheus.py`) pronto para ser raspado pelo Prometheus configurado em `config_ob/prometheus.yml`.

---

## 2. Instruções de Execução Operacional

### Subir a API FastAPI Localmente:
```bash
.venv/bin/uvicorn app.servico_api.aplicacao_fastapi:criar_aplicacao --factory --host 0.0.0.0 --port 8000
```

### Executar a Coleta e Pipeline Diário:
```bash
.venv/bin/python -c "
from app.configuracao_geral.provedor_configuracao import ProvedorConfiguracao
from app.coleta_youtube.cliente_youtube import ClienteYouTube
from app.coleta_youtube.extrator_comentarios import ExtratorComentarios
from app.gestao_dados.cliente_s3 import ClienteS3
from app.gestao_dados.camada_bronze import CamadaBronze
from app.gestao_dados.camada_prata import CamadaPrata
from app.gestao_dados.camada_ouro import CamadaOuro
from app.tratamento_texto.lematizador_spacy import LematizadorSpacy
from app.tratamento_texto.rotulador_topicos import RotuladorTopicos
from app.analise_tendencias.calculador_tendencias import CalculadorTendencias
from app.analise_tendencias.agregador_visoes import AgregadorVisoes
from app.integracao_mlflow.rastreador_experimentos import RastreadorExperimentos
from app.orquestracao_pipeline.executor_ciclo import ExecutorCiclo
import os

config = ProvedorConfiguracao('config/entradas.yaml').carregar()
chave_api = os.getenv(config.coleta.chave_api_env, 'CHAVE_MOCK')
cliente_yt = ClienteYouTube(chave_api=chave_api)
extrator = ExtratorComentarios(cliente_yt)
s3 = ClienteS3(endpoint_url='http://127.0.0.1:9000')
bronze = CamadaBronze(s3, bucket=config.persistencia.bucket)
prata = CamadaPrata(s3, bucket=config.persistencia.bucket)
ouro = CamadaOuro(s3, bucket=config.persistencia.bucket)
lematizador = LematizadorSpacy()
rotulador = RotuladorTopicos()
calc_tend = CalculadorTendencias(janela_dias=config.tendencias.janela_dias)
agregador = AgregadorVisoes()
rastreador = RastreadorExperimentos()

executor = ExecutorCiclo(
    config=config,
    extrator=extrator,
    bronze=bronze,
    prata=prata,
    ouro=ouro,
    lematizador=lematizador,
    rotulador=rotulador,
    calculador_tendencias=calc_tend,
    agregador_visoes=agregador,
    rastreador_mlflow=rastreador,
)
print('Executor instanciado e pronto para o ciclo diário.')
"
```

---

## 3. Execução da API FastAPI via Docker Compose

O serviço `api` foi integrado ao [docker-compose.yaml](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/docker-compose.yaml) sem duplicação de compose, atendendo estritamente aos requisitos de infraestrutura e governança.

### Configuração do Serviço (`api`):
- **Container:** `api-fastapi`
- **Imagem base:** `python:3.12-slim` (pré-existente e em cache local)
- **Porta:** `8000:8000`
- **Rede:** `mlflow-network` (`172.20.0.34`)
- **Perfis:** `servico_ml`, `api`
- **Dependências:** `storage` (RustFS S3) e `mlflow` (MLflow Server)
- **Healthcheck:** Verificação via Python urllib em `http://localhost:8000/health` (intervalo 10s, timeout 5s, retries 10, start_period 40s)

### Comando de Inicialização:
```bash
docker compose --profile servico_ml up -d api
```

### Status e Validação de Saúde:
- `docker compose ps api`: **Up (healthy)**
- Endpoint `/health`: `200 OK` → `{"status": "saudavel", "versao": "0.1.0"}`
- Endpoint `/metrics`: `200 OK` → Métricas expostas para coleta pelo Prometheus
- Endpoint `/docs`: `200 OK` → Swagger UI interativo disponível em `http://127.0.0.1:8000/docs`

