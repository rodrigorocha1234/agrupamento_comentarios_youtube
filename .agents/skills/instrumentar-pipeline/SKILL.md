---
name: instrumentar-pipeline
description: Define telemetria de ponta a ponta, SLIs/SLOs e alertas do projeto Steam.
---
# Skill: instrumentar-pipeline

## Referências obrigatórias
- `AGENTS.md` e `documentacao/especificacao_original_v4_1.md`.
- `.agents/agents.md` e persona correspondente em `.agents/agents/<papel>/agent.md`.

## Procedimento
1. Mapear coleta, streaming, staging/outbox, lake, qualidade, Pandas/Polars, treino, avaliação e serving.
2. Instrumentar histogramas de duração, counters de erro/retry/429 e gauges de buffer/freshness, sem IDs pessoais como labels.
3. Reusar Prometheus/Grafana/Loki/Alloy existentes; registrar MLflow via Observer.
4. Garantir métricas `steam_pages_consumed_total`, `staging_batches_committed_total`, `staging_batch_duration_seconds`, `stream_buffer_records`.
5. Criar painel técnico, comparativo de motores e SLOs com alertas testados.

## Saída padrão
Entregar mudanças versionáveis e um resumo em `production_artifacts/`, com itens concluídos, decisões, comandos realmente executados, validações e pendências. Respeitar gates humanos.
