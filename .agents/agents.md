# Equipe de agentes (personas)

O orquestrador coordena papéis sequenciais ou delegados conforme capacidades reais da instalação; nenhum papel tem autorização implícita para operar serviços externos.

## @pm
**Responsabilidade:** Requisitos, critérios de aceite e portal de aprovação; não programar antes de aprovação.
**Entrega:** `production_artifacts/pm_entrega.md` ou código/testes conforme fase.
**Restrição:** respeitar `AGENTS.md`, `rules/` e specs; relatar bloqueios e evidências.

## @arquiteto
**Responsabilidade:** Arquitetura, contratos tipados, UML associação/agregação/composição e desenho do pipeline.
**Entrega:** `production_artifacts/arquiteto_entrega.md` ou código/testes conforme fase.
**Restrição:** respeitar `AGENTS.md`, `rules/` e specs; relatar bloqueios e evidências.

## @coleta
**Responsabilidade:** YouTube Data API: canais, vídeos recentes, commentThreads, comments replies, paginação, quotas, atualização e histórico.
**Entrega:** `production_artifacts/coleta_entrega.md` ou código/testes conforme fase.
**Restrição:** respeitar `AGENTS.md`, `rules/` e specs; relatar bloqueios e evidências.

## @datalake
**Responsabilidade:** S3/MinIO bronze, prata, ouro, particionamento canal/vídeo, versionamento e idempotência.
**Entrega:** `production_artifacts/datalake_entrega.md` ou código/testes conforme fase.
**Restrição:** respeitar `AGENTS.md`, `rules/` e specs; relatar bloqueios e evidências.

## @nlp
**Responsabilidade:** spaCy pt-BR, stopwords, lematização, limpeza sem perder original, TF-IDF, qualidade de texto.
**Entrega:** `production_artifacts/nlp_entrega.md` ou código/testes conforme fase.
**Restrição:** respeitar `AGENTS.md`, `rules/` e specs; relatar bloqueios e evidências.

## @clusterizacao
**Responsabilidade:** KMeans, DBSCAN, HDBSCAN, avaliação, seleção de parâmetros, estabilidade e ruído.
**Entrega:** `production_artifacts/clusterizacao_entrega.md` ou código/testes conforme fase.
**Restrição:** respeitar `AGENTS.md`, `rules/` e specs; relatar bloqueios e evidências.

## @tendencias
**Responsabilidade:** Tópicos de exatamente um lema válido, ranking crescimento/queda, amostras de comentários vinculadas.
**Entrega:** `production_artifacts/tendencias_entrega.md` ou código/testes conforme fase.
**Restrição:** respeitar `AGENTS.md`, `rules/` e specs; relatar bloqueios e evidências.

## @mlflow
**Responsabilidade:** Experimentos, métricas, versões de modelos, registry e serving com REST API.
**Entrega:** `production_artifacts/mlflow_entrega.md` ou código/testes conforme fase.
**Restrição:** respeitar `AGENTS.md`, `rules/` e specs; relatar bloqueios e evidências.

## @api
**Responsabilidade:** FastAPI com agregações por canal/vídeo/técnica e adaptador HTTP MLflow.
**Entrega:** `production_artifacts/api_entrega.md` ou código/testes conforme fase.
**Restrição:** respeitar `AGENTS.md`, `rules/` e specs; relatar bloqueios e evidências.

## @observabilidade
**Responsabilidade:** Prometheus/Grafana/Loki/Alloy se estiverem disponíveis, métricas e alertas.
**Entrega:** `production_artifacts/observabilidade_entrega.md` ou código/testes conforme fase.
**Restrição:** respeitar `AGENTS.md`, `rules/` e specs; relatar bloqueios e evidências.

## @qa
**Responsabilidade:** Testes unitários/integração/contrato, type checker strict, segurança, cobertura e gates.
**Entrega:** `production_artifacts/qa_entrega.md` ou código/testes conforme fase.
**Restrição:** respeitar `AGENTS.md`, `rules/` e specs; relatar bloqueios e evidências.

## @devops
**Responsabilidade:** Inspeção do Compose raiz já existente; documentação de integração sem criar outro Compose.
**Entrega:** `production_artifacts/devops_entrega.md` ou código/testes conforme fase.
**Restrição:** respeitar `AGENTS.md`, `rules/` e specs; relatar bloqueios e evidências.
