---
name: criar-dashboards
description: Entrega EDA, visualizações de clusters e dashboards executivos configuráveis.
---
# Skill: criar-dashboards

## Referências obrigatórias
- `AGENTS.md` e `documentacao/especificacao_original_v4_1.md`.
- `.agents/agents.md` e persona correspondente em `.agents/agents/<papel>/agent.md`.

## Procedimento
1. Consultar `configuracoes/analises/*.yaml` e registrar renderizadores Plotly/Altair por Adapter.
2. Separar Gold semântica da renderização e dos destinos (arquivo/dashboard/Grafana).
3. Entregar dispersão 2D/3D, distribuição, perfil, resumo, boxplot, violin, correlação, silhouette e comparações pertinentes.
4. Respeitar capability registry e disponibilidade de métrica; PCA é projeção, não distância original.
5. Testar filtros por jogo, modelo, técnicas e versões; incluir legendas e interpretação clara.

## Saída padrão
Entregar mudanças versionáveis e um resumo em `production_artifacts/`, com itens concluídos, decisões, comandos realmente executados, validações e pendências. Respeitar gates humanos.
