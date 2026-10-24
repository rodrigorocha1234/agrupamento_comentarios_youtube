---
name: ciclo-completo
description: Orquestra planejamento, aprovação humana, implementação incremental, QA e handoff do projeto Steam.
---
# Skill: ciclo-completo

## Referências obrigatórias
- `AGENTS.md` e `documentacao/especificacao_original_v4_1.md`.
- `.agents/agents.md` e persona correspondente em `.agents/agents/<papel>/agent.md`.

## Procedimento
1. Ler `AGENTS.md`, especificação v4.1, inventário real e `.agents/agents.md`.
2. Atuar como @pm e executar o protocolo de `/planejar-incremento`: produzir especificação e **parar para aprovação explícita**.
3. Depois de aprovado, decidir um incremento vertical e chamar especialistas pertinentes (agentes CLI, quando disponíveis, ou aplicar seus arquivos de papel sequencialmente).
4. Delegar desenho ao @ml_architect, implementação a @data_engineer/@ml_engineer/@business_analyst/@visualization, telemetria ao @observability.
5. Rodar `/validar-qualidade` via @qa com evidências; solicitar correções e repetir validação até aceite.
6. @devops audita integração com Compose já existente; deployment/migrações destrutivas exigem nova aprovação.
7. Registrar `production_artifacts/handoff_final.md` com o que foi feito, testes reais, riscos e próximos passos. Não fingir que comandos foram executados.

## Saída padrão
Entregar mudanças versionáveis e um resumo em `production_artifacts/`, com itens concluídos, decisões, comandos realmente executados, validações e pendências. Respeitar gates humanos.
