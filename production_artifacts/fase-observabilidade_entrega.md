# Relatório de Entrega — Fase de Observabilidade e Dashboards Grafana (@observabilidade)

**Data:** 2026-10-14  
**Responsável:** `@observabilidade` / `@devops`  
**Referência Contratual:** `AGENTS.md`, `specs/05-mlops-observabilidade.md`, `production_artifacts/Plano_Implementacao.md` (Adendo 11)

---

## 1. Resumo da Entrega

Foi implementada a suíte completa de dashboards declarativos em JSON para o Grafana, integrados nativamente ao provisionador automático do container (`/etc/grafana/provisioning/dashboards/json`), com recarregamento contínuo a cada 10 segundos. Além disso, o alvo de raspagem do Prometheus foi ajustado para conectar diretamente ao serviço `api:8000`, viabilizando o monitoramento operacional de requisições, latências, telemetria de coleta, qualidade de agrupamento de modelos e logs centralizados.

---

## 2. Dashboards Provisionados no Grafana

| Dashboard | Arquivo JSON | UID | Tags | Principais Painéis / Métricas |
| :--- | :--- | :--- | :--- | :--- |
| **Pipeline Operacional & Ingestão YouTube** | `config_ob/dashboards/dashboard_operacional_pipeline.json` | `yt-pipe-operacional` | `pipeline`, `youtube`, `observabilidade`, `ingestao` | Total de Comentários Ingeridos, Taxa de Ingestão (cpm), Erros por Tipo, Duração Média por Etapa do Pipeline, Tempo Acumulado e Stream de Logs Loki |
| **Qualidade de Agrupamento & Modelos de ML** | `config_ob/dashboards/dashboard_modelos_clusters.json` | `yt-clusters-modelos` | `mlops`, `clusters`, `kmeans`, `dbscan`, `hdbscan`, `modelos` | Gauges de Silhouette Score por técnica (KMeans, DBSCAN, HDBSCAN), Taxa de Ruído/Outliers (`-1`), Quantidade de Clusters e Tabela Comparativa |
| **API FastAPI & Serving Operacional** | `config_ob/dashboards/dashboard_api_fastapi.json` | `yt-api-fastapi` | `fastapi`, `api`, `http`, `latencia`, `serving` | Total de Requisições, RPS, Taxa de Sucesso (2xx %), Latência Média, Throughput por Rota/Método, Donut de Status HTTP, Percentis de Latência (p50/p95/p99), Memória RSS e CPU do processo |
| **Data Lakehouse & Armazenamento S3 (RustFS)** | `config_ob/dashboards/dashboard_datalake_lakehouse.json` | `yt-datalake-lakehouse` | `datalake`, `lakehouse`, `s3`, `rustfs`, `bronze`, `prata`, `ouro` | Volume Total Persistido (Bytes), Arquivos Salvos (JSONL/Parquet), Total de Registros Ingeridos por Camada, Latência de I/O S3 (p50/p95/p99), Erros de Storage e Logs RustFS |

---

## 3. Ajustes de Infraestrutura e Conectividade

1. **`config_ob/prometheus.yml`:**
   - Atualizado o target do job `ml_service` de `metricas-treino:8000` para `api:8000`.
   - Reiniciado o container `prometheus` via `docker compose restart prometheus`.
   - Validação via endpoint `http://localhost:9090/api/v1/targets` confirmando target `api:8000` em estado `HEALTH: UP`.

2. **Indexação no Grafana:**
   - Validação via `GET http://localhost:3000/api/search?type=dash-db` confirmando os 4 dashboards indexados e acessíveis imediatamente sem necessidade de login manual (autenticação anônima com papel Admin ativada no compose).

---

## 4. Evidências de Validação e Qualidade

- **Grafana API Search:**
  ```json
  [
    {"uid": "yt-api-fastapi", "title": "API FastAPI & Serving Operacional", "url": "/d/yt-api-fastapi/api-fastapi-and-serving-operacional"},
    {"uid": "yt-datalake-lakehouse", "title": "Data Lakehouse & Armazenamento S3 (RustFS)", "url": "/d/yt-datalake-lakehouse/data-lakehouse-and-armazenamento-s3-rustfs"},
    {"uid": "yt-pipe-operacional", "title": "Pipeline Operacional & Ingestão YouTube", "url": "/d/yt-pipe-operacional/pipeline-operacional-and-ingestao-youtube"},
    {"uid": "yt-clusters-modelos", "title": "Qualidade de Agrupamento & Modelos de ML", "url": "/d/yt-clusters-modelos/qualidade-de-agrupamento-and-modelos-de-ml"}
  ]
  ```
- **Prometheus Targets:** `('ml_service', 'up', '')`
- **Pyright Strict:** `0 errors, 0 warnings, 0 informations`
- **Pytest:** `48 passed, 12 warnings in 12.86s`

