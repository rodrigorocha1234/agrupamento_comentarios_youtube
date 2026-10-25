# Especificação Técnica — Incremento 5 (Fase 5): Adaptador PostgreSQL, Análise Temporal, API FastAPI e AutoML

- **Versão:** 1.0 (Rastreável à Especificação v4.1)
- **Data:** 24/10/2026
- **Autor / Papel:** @pm & @arquiteto
- **Status:** Proposta Técnica para Homologação Humana
- **Referência Oficial:** [`documentacao/especificacao_original_v4_1.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/documentacao/especificacao_original_v4_1.md) (Capítulo 21, Linha 1774, Seções 8, 11, 15, 17)

---

## 1. Visão Geral e Alinhamento à Especificação v4.1

Este incremento implementa a **Fase 5** da especificação v4.1:
> *"Fase 5: adaptador PostgreSQL, novas fontes, PyCaret/AutoML, análise temporal, módulos opcionais de PLN (desativados por invariante), visualização interativa avançada."*

O objetivo é expandir a maturidade e interoperabilidade do ecossistema:
1. **Adaptador PostgreSQL para Staging:** Permitir alternância transparente entre SQLite (padrão local) e PostgreSQL (banco corporativo/staging compartilhado) via GoF Repository, Unit of Work e Factory/Registry sem alterar linhas de negócio ou pipelines.
2. **Análise Temporal de Clusters:** Alinhamento de rótulos entre janelas temporais de coleta para solucionar a permutação aleatória de IDs de cluster (drift vs permutação) e rastreamento da evolução de sentimento e personas.
3. **Serviço de API FastAPI:** Exposição REST padronizada (conforme especificado no container `api-fastapi` do Docker Compose) para auditoria de negócio, recuperação de reviews textuais para consulta humana e inferência controlada (`/health`, `/metrics`, `/api/v1/jogos/{appid}/clusters`, `/api/v1/jogos/{appid}/reviews`, `/api/v1/jogos/{appid}/predizer`).
4. **AutoML e Seleção Avançada de Modelos:** Integrador automatizado que avalia múltiplos algoritmos (`KMeans`, `DBSCAN`, `HDBSCAN`) e seleciona o campeão segundo restrições de negócio e capacidade.

---

## 2. Escopo do Incremento 5

### 2.1. Itens no Escopo
1. **Persistência de Staging PostgreSQL (`app/persistencia_staging/`):**
   - `esquema_postgres.py` (`EsquemaTabelasPostgres`): DDL idempotente com tipos PostgreSQL (`BIGINT`, `BOOLEAN`, `TIMESTAMP WITH TIME ZONE`, `JSONB`).
   - `repositorio_postgres.py` (`RepositorioStagingPostgres`): repositório com upsert atômico `ON CONFLICT (appid, recommendationid) DO UPDATE ...`.
   - `unidade_postgres.py` (`UnidadeTrabalhoPostgres`): Unit of Work transacional com commit/rollback em conexões `psycopg 3`.
   - Integração na `FabricaStaging` (`fabrica_staging.py`): registro da tecnologia `"postgres"`.
2. **Análise Temporal e Alinhamento de Clusters (`app/analise_temporal/`):**
   - `alinhador_clusters.py` (`AlinhadorClustersTemporal`): algoritmo de similaridade para mapear clusters de $t_1$ em $t_0$ evitando permutações de identificador.
   - `rastreador_evolucao.py` (`RastreadorEvolucaoTemporal`): série temporal de distribuição de clusters, proporção de ruído e tendência de votos.
3. **Serviço de API REST FastAPI (`app/servico_api/`):**
   - `aplicacao_fastapi.py` (`criar_aplicacao`): aplicação FastAPI factory pronta para Uvicorn, com rotas de saúde, telemetria Prometheus, consulta Gold de clusters, visualização e recuperação paginada de texto para analistas humanos.
   - Modelos Pydantic v2 estritos para request e response sem `Any`.
4. **AutoML e Seleção de Modelos (`app/agrupamento_modelos/`):**
   - `selecionador_automl.py` (`SelecionadorModelosAutoML`): orquestra avaliação concorrente ou sequencial de múltiplos estimadores respeitando o catálogo de capacidades.

### 2.2. Fora de Escopo
- Processamento de Linguagem Natural (PLN), LLMs ou embeddings textuais (invariante do projeto: texto reservado para consulta humana).
- Criação de novos serviços no Docker Compose (o serviço `api` já existe e está configurado no compose root).
- Modificação destrutiva de esquemas existentes.

---

## 3. Arquitetura de Módulos (Regra das 2 Palavras)

Todos os pacotes e módulos seguem rigorosamente a regra de **duas palavras** separadas por `_`:

```text
app/
├── persistencia_staging/
│   ├── esquema_postgres.py       # DDL idempotente PostgreSQL
│   ├── repositorio_postgres.py   # Repositório Staging com psycopg 3
│   └── unidade_postgres.py       # Unit of Work PostgreSQL
├── analise_temporal/
│   ├── alinhador_clusters.py     # Alinhamento e estabilidade de clusters no tempo
│   └── rastreador_evolucao.py    # Cálculo de métricas e drift temporal
├── servico_api/
│   └── aplicacao_fastapi.py      # Aplicação FastAPI factory com endpoints REST
└── agrupamento_modelos/
    └── selecionador_automl.py    # Seleção automatizada de modelos via capacidades
```

---

## 4. Critérios Mensuráveis de Aceite

1. **Strict Type Checking:** `pyright` no modo `strict` em 100% dos novos módulos e testes com **0 errors, 0 warnings** e zero `Any`.
2. **Lint e Formatação:** `ruff check .` e `ruff format --check .` sem violações.
3. **Paridade Funcional de Staging:** Testes demonstrando paridade de comportamento entre `RepositorioStagingSqlite` e `RepositorioStagingPostgres` (upsert, histórico, outbox).
4. **Alinhamento Temporal Correto:** Teste comprovando que clusters permutados sinteticamente são mapeados para seus rótulos semânticos originais com alta correlação.
5. **API FastAPI Operacional:** Testes com `TestClient` cobrindo `/health`, `/metrics`, consulta de clusters e paginação de reviews textuais brutas.
6. **Suíte Pytest Totalmente Aprovada:** 100% dos testes anteriores (56 testes) mais os novos testes da Fase 5 passando sem falhas.

---

## 5. Riscos e Mitigações

| Risco | Impacto | Mitigação Arquitetural |
|---|---|---|
| PostgreSQL indisponível no ambiente local de testes unitários | Médio | Testes unitários de repositório Postgres com isolamento e suporte a mocks / conexões ativas do Docker Compose (`localhost:5432`). |
| Permutação ambígua de centróides temporais | Médio | Uso de distância Euclidiana entre perfis normalizados com fallback para dissimilaridade de membros. |
| Dependência de bibliotecas pesadas de AutoML | Baixo | Implementação orientada ao catálogo de capacidades (`CapacidadesAlgoritmo`) e aos adaptadores nativos existentes (`KMeans`, `DBSCAN`, `HDBSCAN`). |
