---
trigger: model_decision
description: Ingestão e staging do Steam Reviews Clustering v4.1.
---
# Ingestão e staging
- Consultar quando modificar Steam API, staging, outbox ou lake.
- Cursor é estado transitório; identidade da review é `(appid,recommendationid)`.
- Implementar transação de lote + checkpoint coerente, retry com jitter e consumidor incremental.
- Outbox fornece consistência eventual entre SQLite e S3; nunca afirmar atomicidade distribuída.
Fonte de verdade: `documentacao/especificacao_original_v4_1.md`.
