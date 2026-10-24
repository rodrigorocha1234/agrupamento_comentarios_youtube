---
name: planejar-incremento
description: Escreve especificação rastreável e solicita aprovação antes de implementar.
---
# Skill: planejar-incremento

## Referências obrigatórias
- `AGENTS.md` e `documentacao/especificacao_original_v4_1.md`.
- `.agents/agents.md` e persona correspondente em `.agents/agents/<papel>/agent.md`.

## Procedimento
1. @pm lê especificação original, inventário e pendências do projeto.
2. Produzir `production_artifacts/Technical_Specification.md`: requisitos, fora de escopo, fluxos, interfaces, dependências, critérios mensuráveis e riscos.
3. Produzir `production_artifacts/01_plano_aprovacao.md` com ordem de execução, gates e decisões abertas.
4. Solicitar ao usuário aprovação explícita da arquitetura e do incremento. Sem aprovação não iniciar implementação invasiva.

## Saída padrão
Entregar mudanças versionáveis e um resumo em `production_artifacts/`, com itens concluídos, decisões, comandos realmente executados, validações e pendências. Respeitar gates humanos.
