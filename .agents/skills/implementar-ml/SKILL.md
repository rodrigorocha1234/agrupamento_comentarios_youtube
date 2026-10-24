---
name: implementar-ml
description: Constrói features, pré-processamento, clustering e avaliação configurados em YAML.
---
# Skill: implementar-ml

## Referências obrigatórias
- `AGENTS.md` e `documentacao/especificacao_original_v4_1.md`.
- `.agents/agents.md` e persona correspondente em `.agents/agents/<papel>/agent.md`.

## Procedimento
1. Validar datasets Gold, IDs, granularidade e distinção de métricas observadas na coleta vs. na review.
2. Registrar estratégias Pandas/Polars e sklearn/PyCaret; YAML governando filtros, transformações, combinações e algoritmos.
3. Implementar pipelines de imputação/scaling/redução sem leakage nem duplicação PyCaret.
4. Treinar KMeans/DBSCAN/HDBSCAN com capability registry; buscar hiperparâmetros quando aplicável.
5. Avaliar silhouette, DBI, CH, ruído, estabilidade e trade-offs; registrar casos indefinidos e artefatos MLflow.
6. Testar reproducibilidade, invariância de IDs e contratos.

## Saída padrão
Entregar mudanças versionáveis e um resumo em `production_artifacts/`, com itens concluídos, decisões, comandos realmente executados, validações e pendências. Respeitar gates humanos.
