---
name: validar-qualidade
description: Executa revisão arquitetural, type checking, testes e relatório QA rastreável.
---
# Skill: validar-qualidade

## Referências obrigatórias
- `AGENTS.md` e `documentacao/especificacao_original_v4_1.md`.
- `.agents/agents.md` e persona correspondente em `.agents/agents/<papel>/agent.md`.

## Procedimento
1. Ler alterações e mapear critérios de aceite para testes.
2. Executar comandos presentes no repositório, conforme disponibilidade: formatter/linter, type checker strict, pytest unit/integration/contracts/e2e.
3. Examinar no-if de domínio, YAML extra-forbid, secrets, no-PLN e um Compose raiz.
4. Verificar idempotência, rollback, outbox, retry 429, paridade de motor e limites de memória.
5. Emitir `production_artifacts/qa_relatorio.md` distinguindo APROVADO/FALHOU/NÃO EXECUTADO e evidências.
6. Repetir após correções; bloquear promotion com falhas críticas.

## Saída padrão
Entregar mudanças versionáveis e um resumo em `production_artifacts/`, com itens concluídos, decisões, comandos realmente executados, validações e pendências. Respeitar gates humanos.
