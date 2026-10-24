# Inventário do Projeto — Steam Reviews Clustering v4.1

- **Data da Auditoria:** 24/10/2026
- **Agentes Responsáveis:** Equipe Multiagente (Coordenação: `@pm` / `@devops`)
- **Referência Oficial:** [`documentacao/especificacao_original_v4_1.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/documentacao/especificacao_original_v4_1.md)
- **Status Geral:** Ambiente em transição da base legada (YouTube NLP) para a arquitetura Steam Reviews Clustering v4.1. Infraestrutura base de apoio ativa e saudável no Docker; módulos de domínio, configuração e testes pendentes de implementação.

---

## 1. Infraestrutura e Serviços Docker Compose

A auditoria inspecionou o arquivo raiz [`docker-compose.yaml`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/docker-compose.yaml) e verificou o estado dos contêineres via `docker ps`.

### 1.1. Serviços Definidos vs. Serviços em Execução Real

| Serviço (`docker-compose.yaml`) | Imagem | Perfil | Portas Expostas | Status Real (`docker ps`) | Diagnóstico / Observação |
|---|---|---|---|---|---|
| `postgres` (`mlflow-postgres`) | `postgres:15` | `servico_ml` | `5432:5432` | **Up 4 hours (healthy)** | Banco de metadados do MLflow ativo e funcional. |
| `storage` (`storage`) | `rustfs/rustfs:1.0.0-alpha.83` | `servico_ml` | `9000:9000`, `9001:9001` | **Up 4 hours (healthy)** | S3 gateway/console ativo e saudável para Data Lake / artefatos. |
| `create-bucket` (`mlflow-create-bucket`) | `amazon/aws-cli:2.33.25` | `servico_ml` | - | **Finalizado (exit 0)** | Cria buckets iniciais (`mlflow-bucket` e `youtube-comentarios`). |
| `mlflow` (`mlflow-server`) | `ghcr.io/mlflow/mlflow:latest` | `servico_ml` | `5000:5000` | **Up 4 hours (healthy)** | Servidor de rastreamento do MLflow ativo e saudável. |
| `grafana` (`grafana`) | `grafana/grafana` | `dashboard` | `3000:3000` | **Up 4 hours (healthy)** | Painel Grafana ativo, provisionado com datasources/dashboards. |
| `loki` (`loki`) | `grafana/loki:latest` | `dashboard` | `3100:3100` | **Up 4 hours** | Centralizador de logs estruturados ativo na porta 3100. |
| `alloy` (`alloy`) | `grafana/alloy:latest` | `dashboard` | `12345:12345` | **Up 4 hours** | Coletor de telemetria e logs de contêineres ativo. |
| `prometheus` (`prometheus`) | `prom/prometheus:latest` | `dashboard` | `9090:9090` | **Up 4 hours (healthy)** | Coletor de métricas de séries temporais ativo e saudável. |
| `mlflow-serving` (`mlflow-serving`) | `ghcr.io/mlflow/mlflow:latest` | `serving` | `8080:8080` | **Restarting (crashloop)** | Falha ao iniciar: módulo `app_build.observabilidade_metricas.servidor_inferencia` ainda não existe. |
| `api` (`api-fastapi`) | `python:3.12-slim` | `servico_ml`, `api` | `8000:8000` | **Restarting (crashloop)** | Falha ao iniciar: módulo `app.servico_api.aplicacao_fastapi` ainda não existe. |

### 1.2. Redes e Volumes Persistentes
- **Rede única:** `mlflow-network` (bridge, sub-rede `172.20.0.0/16`).
- **Volumes locais mapeados:**
  - `./pgdata` (dados do PostgreSQL)
  - `./storage-data` (dados do RustFS / S3)
  - `./grafana_data` (metadados e dashboards locais do Grafana)
  - `./prometheus_data` (séries temporais do Prometheus)
  - `./config_ob` (arquivos de configuração de observabilidade montados em modo somente leitura)

---

## 2. Arquivos de Configuração, Ambiente e Segredos

### 2.1. Arquivo `.env` e Gestão de Segredos
- **Arquivo existente:** `.env` presente na raiz do workspace.
- **Variáveis configuradas:** timezone (`America/Sao_Paulo`), credenciais e portas para PostgreSQL, RustFS S3, MLflow e Grafana.
- **Incompatibilidades detectadas:**
  - Presença de resquícios do projeto anterior: `YOUTUBE_API_KEY` e `DATA_BUCKET=youtube-comentarios`.
  - Ausência de variáveis necessárias para a especificação v4.1: `STEAM_API_KEY`, `STAGING_SQLITE_PATH`, `STAGING_POSTGRES_DSN` e bucket dedicado do Steam (ex: `steam-lake` ou `steam-reviews`).
- **Arquivo `.env.example`:** Atualmente **ausente** (marcado como deletado no histórico git). Deve ser recriado com placeholders seguros, sem expor credenciais reais.

### 2.2. Diretório `configuracoes/`
- O diretório [`configuracoes/`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/configuracoes) existe no sistema de arquivos, porém está **completamente vazio** (pertence a `root:root` decorrente de montagem de volume).
- De acordo com a seção 4 da especificação v4.1, são necessários 21 arquivos YAML tipados e versionados, organizados sob responsabilidades estritas (`projeto.yaml`, `fontes/steam_api.yaml`, `infraestrutura/staging.yaml`, `machine_learning/algoritmos.yaml`, etc.).

### 2.3. Diretório `config_ob/`
- Arquivos de configuração de observabilidade presentes e em uso pelos contêineres:
  - `config.alloy`
  - `grafana_datasources.yaml`
  - `grafana_dashboards_provider.yaml`
  - `loki-config.yaml`
  - `prometheus.yml`
  - `dashboards/`: 4 dashboards JSON herdados da fase preliminar (`dashboard_api_fastapi.json`, `dashboard_datalake_lakehouse.json`, `dashboard_modelos_clusters.json`, `dashboard_operacional_pipeline.json`).

---

## 3. Ambiente Python e Dependências

### 3.1. Interpretador e Runtime
- **Versão do Python:** `Python 3.12.3` (em conformidade com a exigência `>=3.12`).
- **Ambiente virtual:** `.venv` ativo na raiz.

### 3.2. Análise do `pyproject.toml` vs. v4.1

| Dependência no `pyproject.toml` | Versão Solicitada | Situação na v4.1 | Diagnóstico |
|---|---|---|---|
| `pandas` | `>=2.2` (instalado `3.0.6`) | Conforme | Motor tabular padrão da especificação. |
| `scikit-learn` | `>=1.5` (instalado `1.9.1`) | Conforme | Framework de clustering (KMeans, DBSCAN, HDBSCAN). |
| `boto3` / `botocore` | `>=1.35` (instalado `1.43.113`) | Conforme | Cliente para S3/RustFS (Bronze, Silver, Gold). |
| `PyYAML` | `>=6.0` (instalado `6.0.3`) | Conforme | Leitura de configurações externas. |
| `pydantic` | Instalado `2.14.1` | Conforme | Base essencial para a fachada `ConfYAML`. |
| `mlflow` | `>=2.16` (instalado `3.17.1`) | Conforme | Rastreamento e registro de modelos. |
| `prometheus-client` | `>=0.20` (instalado `0.26.0`) | Conforme | Métricas de telemetria da aplicação. |
| `pyarrow` | `>=17` (instalado `25.0.1`) | Conforme | Armazenamento colunar Parquet. |
| `polars` | **Não listado / Não instalado** | Necessário (opcional) | Requisito de motor alternativo via Strategy na v4.1. |
| `spacy` | `>=3.7` (instalado `3.8.16`) | **CONFLITO GRAVE** | **Proibido pela v4.1**: "sem PLN, LLM, embeddings ou treinamento textual". |
| `sentence-transformers` | `>=3.0` (instalado `6.1.0`) | **CONFLITO GRAVE** | **Proibido pela v4.1**: texto original apenas para consulta humana. |
| `torch` | `>=2.2` (instalado `2.14.1+cpu`) | **CONFLITO GRAVE** | **Proibido pela v4.1**: sobrecarga pesada e desnecessária sem PLN. |

---

## 4. Estado da Árvore de Código e Versionamento (Git)

- **Ramo Git:** `main` (rastreando `origin/main`).
- **Código de Aplicação (`app/` e `src/`):** Diretórios vazios no disco; classes legadas de NLP do YouTube foram removidas da árvore de trabalho.
- **Testes (`tests/`):** O diretório `tests/` não existe no disco (os testes legados foram removidos da árvore de trabalho).
- **Documentação de Referência:**
  - [`documentacao/especificacao_original_v4_1.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/documentacao/especificacao_original_v4_1.md) (71.209 bytes, fonte de verdade consolidada).
  - [`documentacao/roteiro_implementacao.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/documentacao/roteiro_implementacao.md) (Roteiro em fases com gates humanos).
  - [`docs/diagramas_uml.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/docs/diagramas_uml.md) e [`docs/index.html`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/docs/index.html).
- **Estrutura Antigravity (.agents):**
  - Regras ativas em `.agents/rules/` (`01` a `07`).
  - Personas definidas em `.agents/agents/` (9 papéis especializados).
  - Procedimentos prontos em `.agents/skills/` (10 skills disponíveis).

---

## 5. Matriz de Aderência aos Requisitos da v4.1

| Componente / Módulo v4.1 | Situação Atual | Componentes Existentes | Componentes Ausentes | Conflitos a Tratar |
|---|---|---|---|---|
| **1. Coleta Steam API** | Ausente | Estratégia descrita na spec v4.1 | Adaptador HTTP Steam, gerador paginado lazy (`Iterator[PaginaReviews]`), backpressure, retry/backoff, controle 429 | Resquício de variáveis do YouTube no `.env` |
| **2. Staging Transacional** | Ausente | Driver SQLite nativo no Python; Postgres no Docker | Repositório `RepositorioStaging`, Unit of Work, esquemas migráveis, tabela outbox de publicação | Nenhum código ou migração no workspace |
| **3. Data Lake (Bronze/Silver/Gold)** | Parcial | S3/RustFS ativo e saudável (`storage:9000`) | Estrutura de particionamento, classes de persistência Bronze imutável, Silver histórico/qualidade, Gold Parquet | Bucket padrão configurado como `youtube-comentarios` |
| **4. Configuração Declarativa** | Ausente | PyYAML e Pydantic no `.venv` | Fachada exclusiva `ConfYAML`, schemas com tipagem strict, catálogo de 21 arquivos YAML em `configuracoes/` | Diretório `configuracoes/` vazio e de posse do root |
| **5. Motor Tabular & DSL** | Ausente | Pandas instalado no `.venv` | Adaptador do motor, DSL declarativa para seleção, filtros e transformações sem `eval`/`exec`, suporte Polars | Polars ausente do ambiente |
| **6. Engenharia de Atributos** | Ausente | Regras claras na especificação v4.1 | Normalização de colunas tabulares (`playtime_forever`, `playtime_at_review`, etc.), sem PLN | Pacotes de PLN (`spacy`, `torch`, `sentence-transformers`) no `pyproject.toml` |
| **7. Pré-processamento** | Ausente | scikit-learn instalado | Pipeline composable (Imputer, Scaler, PCA opcional, Outliers) via GoF Composite/Strategy | Nenhum |
| **8. Algoritmos de Clustering** | Ausente | scikit-learn instalado | Adaptadores KMeans, DBSCAN e HDBSCAN; catálogo de capacidades; avaliadores de qualidade de clusters | Nenhum |
| **9. Rastreamento MLflow** | Parcial | Servidor MLflow e Postgres saudáveis | Observer de execução para logging de artefatos, datasets e métricas; adaptador de inferência | `mlflow-serving` em crashloop por falta do módulo Python |
| **10. Regras de Negócio Pós-Treino** | Ausente | Conceito formalizado na spec | Motor de regras declarativas (Specification/Composite), rotulagem sem retreino | Nenhum |
| **11. EDA e Visualizações** | Parcial | Grafana funcional na porta 3000 | Renderizadores de dispersão 2D/3D, distribuições e perfis; geração de dashboards específicos | Dashboards atuais são legados |
| **12. Observabilidade & SLIs** | Parcial | Stack Prometheus, Loki, Alloy e Grafana UP | Métricas instrumentadas no código da aplicação (`steam_pages_consumed_total`, latências, buffers) | `api-fastapi` em crashloop |
| **13. Testes & CI Strict** | Ausente | `pytest`, `pyright`, `ruff` instalados | Testes unitários, de integração, de contrato e suites completas de validação | Diretório `tests/` ausente |

---

## 6. Comandos Realmente Executados Durante a Auditoria

1. `docker ps` — Verificação de contêineres e serviços em execução real.
2. `ls -la` — Inspeção física e detalhada de permissões de diretórios e arquivos da raiz.
3. `git status` — Auditoria do estado do repositório, histórico de modificações e arquivos não monitorados.
4. `ls -la tests` — Confirmação da ausência física da pasta de testes.
5. `./.venv/bin/python --version && ./.venv/bin/pip list` — Verificação da versão do runtime e pacotes instalados.
6. Leitura e análise dos arquivos essenciais (`docker-compose.yaml`, `.env`, `pyproject.toml`, `README.md`, `documentacao/especificacao_original_v4_1.md`).

---

## 7. Decisões Arquiteturais e Próximos Passos (Gates Humanos)

### 7.1. Decisões e Cuidados Técnicos Imediatos
1. **Preservação da Infraestrutura Docker Compose:** A infraestrutura existente (PostgreSQL, RustFS S3, MLflow, Prometheus, Grafana, Loki e Alloy) deve ser rigorosamente mantida e reaproveitada. Nenhuma alteração destrutiva ou remoção de contêineres foi ou será executada sem autorização expressa.
2. **Correção de Permissões de Pastas:** As pastas `app/`, `src/` e `configuracoes/` foram criadas com propriedade `root:root`. Ao iniciar a implementação, o usuário poderá ajustar permissões locais (`chown`) caso necessário.
3. **Limpeza de Dependências Incompatíveis:** Na especificação do incremento, recomendar o alinhamento de `pyproject.toml`, removendo pacotes proibidos de NLP (`spacy`, `torch`, `sentence-transformers`) e adicionando `polars` se aplicável.
4. **Alinhamento do Bucket S3:** O container `create-bucket` cria `youtube-comentarios`. O planejamento deve incluir a definição amigável do bucket na variável de ambiente (ex: `DATA_BUCKET=steam-reviews`).

### 7.2. Recomendação para o Usuário
O inventário foi concluído com sucesso e sem alterações destrutivas no workspace.
O próximo passo no fluxo de desenvolvimento é invocar a skill de planejamento:
👉 `/planejar-incremento` para elaborar a especificação detalhada da **Fase 1 (Contratos de Domínio, ConfYAML, Coleta Steam com Iterators e Staging Transacional)** e submeter ao gate de aprovação humana em [`production_artifacts/modelo_aprovacao.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/production_artifacts/modelo_aprovacao.md).
