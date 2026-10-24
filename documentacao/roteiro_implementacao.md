# Roteiro incremental proposto

1. Inventário dos serviços e código existentes (nenhuma alteração).
2. YAMLs estritos e contratos de domínio + arquitetura SOLID/GoF.
3. Steam HTTP → Iterator páginas → SQLite staging transacional → checkpoint/outbox.
4. Publicação Bronze imutável → Silver histórico/qualidade → Gold versionado.
5. Motores Pandas/Polars, DSL segura e geração de atributos.
6. Pré-processamento e clustering sklearn/PyCaret, tuning e avaliação.
7. MLflow e capacidade real de atribuição/serving.
8. Regras de negócio pós-treino, tabelas, gráficos e dashboards.
9. Observabilidade, SLOs, testes de contrato/integração, segurança.
10. Análise temporal opcional, após alinhar IDs entre treinamentos.

**Gates:** aprovação da especificação → protótipo ingestão/staging → Quality Gate de dados → avaliação ML → QA end-to-end → autorização DevOps para deploy.
