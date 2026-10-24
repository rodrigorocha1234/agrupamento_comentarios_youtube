---
name: implementar-coleta
description: Implementa coleta Steam paginada, incremental e com generators conforme v4.1.
---
# Skill: implementar-coleta

## Referências obrigatórias
- `AGENTS.md` e `documentacao/especificacao_original_v4_1.md`.
- `.agents/agents.md` e persona correspondente em `.agents/agents/<papel>/agent.md`.

## Procedimento
1. Conferir parâmetros documentados do `IUserReviewsService/GetAppReviews` antes de codificar, incluindo `input_json`, limites e permissão.
2. Implementar adapter Steam com `Iterator[PaginaReviews]`, cursor, estratégias histórica/recente/atualizada, retry 429, timeout e paginação.
3. Persistir checkpoints e lote idempotente no staging. Tratar cursores repetidos e backpressure.
4. Testar falhas intermediárias, exaustão, memória, dados ausentes e recuperabilidade.
5. Registrar métricas e handoff.

## Saída padrão
Entregar mudanças versionáveis e um resumo em `production_artifacts/`, com itens concluídos, decisões, comandos realmente executados, validações e pendências. Respeitar gates humanos.
