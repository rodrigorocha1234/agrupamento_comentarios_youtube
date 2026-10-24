# Equipe multiagente — matriz de atribuições

Este documento é o catálogo humano da equipe, inspirado no ciclo PM → engenharia → QA → DevOps do artigo de Peterson Pereira. **Não confundir com o registro executável de agentes personalizados**: na CLI os agentes estão em `.agents/agents/<nome>/agent.md`.

| Persona | Entrega | Limite |
|---|---|---|
| @pm | Escopo, critérios de aceite, aprovação | Não implementa antes do aceite |
| @ml_architect | Contratos, SOLID/GoF, compatibilidade | Não inventa APIs universais |
| @data_engineer | Steam, staging, outbox, Bronze/Silver/Gold | Não reimplementa infra existente |
| @ml_engineer | Features, Pandas/Polars, sklearn/PyCaret, tuning | Sem PLN e sem leakage |
| @business_analyst | Métricas e regras YAML pós-modelo | Não confunde rótulo com algoritmo |
| @visualization | EDA, clusters, relatórios, Grafana | Não apresenta PCA como distância original |
| @observability | métricas, logs, SLOs, MLflow | Sem segredo ou ID pessoal como label |
| @qa | Unit/integration/contract/e2e e gates | Evidência verificável |
| @devops | Compose, segurança e execução | Aprovação para mudanças invasivas |

As fronteiras são disciplina de trabalho; execução concorrente e invocação nominal dependem da superfície/versão do Antigravity. Selecione agentes pela CLI com `/agents` ou descreva a persona na tarefa do IDE.
