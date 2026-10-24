---
name: analise-negocio
description: Cria análises e rotulagem de clusters pós-treino por regras YAML.
---
# Skill: analise-negocio

## Referências obrigatórias
- `AGENTS.md` e `documentacao/especificacao_original_v4_1.md`.
- `.agents/agents.md` e persona correspondente em `.agents/agents/<papel>/agent.md`.

## Procedimento
1. Definir catálogo Gold de métricas, chaves e amostras; não usar texto como feature.
2. Aplicar Specification/Composite para regras sobre medianas, horas, engajamento e avaliações por cluster.
3. Versionar regras, rótulos, justificativas e registros não classificados sem alterar atribuições ML.
4. Entregar tabela de perfis, distribuição, resumo executivo e exemplos de interpretação com ressalvas causais.

## Saída padrão
Entregar mudanças versionáveis e um resumo em `production_artifacts/`, com itens concluídos, decisões, comandos realmente executados, validações e pendências. Respeitar gates humanos.
