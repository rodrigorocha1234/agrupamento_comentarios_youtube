# Plano de Aprovação — Incremento 5 (Fase 5): Adaptador PostgreSQL, Análise Temporal, API FastAPI e AutoML

- **Versão:** 1.0
- **Data:** 24/10/2026
- **Responsável:** @pm / @arquiteto
- **Referência Oficial:** [`documentacao/especificacao_original_v4_1.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/documentacao/especificacao_original_v4_1.md) (Capítulo 21, Linha 1774, Seções 8, 11, 15, 17)
- **Especificação Técnica do Incremento:** [`production_artifacts/Technical_Specification_Fase5.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/production_artifacts/Technical_Specification_Fase5.md)

---

## 1. Ordem de Execução Proposta

### Etapa 1: Adaptador PostgreSQL para Staging
- Criar componentes em [`app/persistencia_staging/`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/app/persistencia_staging/):
  - `esquema_postgres.py` (`EsquemaTabelasPostgres`): Criação idempotente de tabelas `steam_reviews`, `historico_reviews`, `metadados_execucao` e `outbox_eventos` em PostgreSQL com índices otimizados.
  - `unidade_postgres.py` (`UnidadeTrabalhoPostgres`): Implementação do protocolo `UnidadeTrabalho` para PostgreSQL com commit e rollback seguros via driver `psycopg 3`.
  - `repositorio_postgres.py` (`RepositorioStagingPostgres`): Implementação do contrato `RepositorioStaging` com upsert idempotente `ON CONFLICT (appid, recommendationid) DO UPDATE ...`.
  - Atualizar [`fabrica_staging.py`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/app/persistencia_staging/fabrica_staging.py) para registrar `"postgres"` no catálogo GoF Factory/Registry.
- Testes unitários e de paridade: `tests/teste_postgres.py`.

### Etapa 2: Análise Temporal e Alinhamento de Clusters
- Criar pacote [`app/analise_temporal/`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/app/analise_temporal/):
  - `alinhador_clusters.py` (`AlinhadorClustersTemporal`): Mapeamento de estabilidade temporal que relaciona identificadores de cluster em janelas sucessivas ($t_0 \to t_1$) usando matriz de similaridade de centróides / perfis medianos de jogadores, resolvendo o problema de permutação aleatória de rótulos entre treinamentos.
  - `rastreador_evolucao.py` (`RastreadorEvolucaoTemporal`): Rastreamento de métricas temporais (distribuição percentual de clusters por janela temporal, evolução de sentimento positivo/negativo e drift).
- Testes automatizados: `tests/teste_temporal.py`.

### Etapa 3: Serviço de API REST FastAPI
- Criar pacote [`app/servico_api/`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/app/servico_api/):
  - `aplicacao_fastapi.py` (`criar_aplicacao`): Factory que instancia a aplicação FastAPI conforme configurado no Docker Compose (`python -m uvicorn app.servico_api.aplicacao_fastapi:criar_aplicacao --factory --host 0.0.0.0 --port 8000`).
  - Endpoints REST com schemas Pydantic v2 estritos:
    - `GET /health`: Healthcheck oficial do container.
    - `GET /metrics`: Exposição de métricas Prometheus.
    - `GET /api/v1/jogos/{appid}/clusters`: Consulta dos resultados e personas da camada Gold.
    - `GET /api/v1/jogos/{appid}/reviews`: Recuperação de avaliações textuais originais filtradas por cluster/persona para consulta humana de auditoria (sem PLN).
    - `POST /api/v1/jogos/{appid}/predizer`: Atribuição de cluster para novos pontos com verificação de capacidades do estimador treinado.
- Testes com `TestClient`: `tests/teste_api.py`.

### Etapa 4: Seleção Automatizada de Modelos (AutoML)
- Criar módulo em [`app/agrupamento_modelos/`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/app/agrupamento_modelos/):
  - `selecionador_automl.py` (`SelecionadorModelosAutoML`): Orquestrador de AutoML que avalia múltiplos algoritmos (KMeans, DBSCAN, HDBSCAN) sob diferentes hiperparâmetros e elege o campeão multicritério sem cadeias de `if/elif`.
- Testes unitários: `tests/teste_automl.py`.

### Etapa 5: Teste de Integração Ponta a Ponta da Fase 5
- Criar `tests/teste_integracao_fase5.py` validando o fluxo unificado:
  - Alternância de Staging para PostgreSQL.
  - Análise temporal e alinhamento de clusters.
  - Endpoints da API FastAPI.
  - Seleção AutoML de clustering.

### Etapa 6: Quality Gates e Handoff Final
- Execução de `ruff check . --fix && ruff format .`.
- Verificação `pyright` no modo `strict` em 100% da base (zero `Any`, 0 erros, 0 warnings).
- Execução do `pytest` com validação de 100% dos testes passando.
- Atualização de `production_artifacts/qa_relatorio.md` e `production_artifacts/handoff_final.md`.

---

## 2. Invariantes Arquiteturais Mantidos

1. **Python 3.12+ Strict:** Proibição absoluta de `Any` ou `typing.Any`.
2. **Nomenclatura Canônica:** Nomes próprios em português; pacotes e módulos com exatamente duas palavras separadas por `_`.
3. **Padrões GoF sem Condicionais de Tecnologia:** Factory/Registry, Strategy, Adapter, Repository, Unit of Work e Specification.
4. **Sem PLN ou Inferência Textual:** Reviews textuais mantidas exclusivamente para visualização e consulta humana.
5. **Preservação de Infraestrutura:** Reuso estrito dos containers existentes do Docker Compose (PostgreSQL :5432, API :8000, S3 :9000, MLflow :5000, Prometheus :9090, Grafana :3000).

---

## 3. Decisão de Aprovação Humana Requerida

Antes de dar início às alterações de código, solicitamos a aprovação formal do usuário para a execução do plano da **Fase 5**.
