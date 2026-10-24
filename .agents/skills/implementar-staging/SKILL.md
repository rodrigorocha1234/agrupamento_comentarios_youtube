---
name: implementar-staging
description: Implementa staging SQLite/Postgres com Repository, Unit of Work e outbox.
---
# Skill: implementar-staging

## Referências obrigatórias
- `AGENTS.md` e `documentacao/especificacao_original_v4_1.md`.
- `.agents/agents.md` e persona correspondente em `.agents/agents/<papel>/agent.md`.

## Procedimento
1. Definir `RepositorioStaging[T]`, `UnidadeTrabalho`, registry de adapters e política de upsert versionado.
2. SQLite padrão com WAL, busy_timeout, migrações, índices, lotes e transações; Postgres alternável via YAML sem alteração de domínio.
3. Persistir execuções, páginas recebidas, reviews atuais/históricas, autores observados, checkpoints e outbox.
4. Publicar payload original imutável Bronze e derivados Silver com idempotência e replay de outbox.
5. Testar rollback, checkpoint e replay; não alegar transação distribuída.

## Saída padrão
Entregar mudanças versionáveis e um resumo em `production_artifacts/`, com itens concluídos, decisões, comandos realmente executados, validações e pendências. Respeitar gates humanos.
