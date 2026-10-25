---
name: auditar-steam
description: Audita código, YAML e arquitetura contra as regras do projeto Steam clustering.
---

# Auditar

- Compare implementação com `AGENTS.md`, regras e especificação aprovada.
- Procure `Any`, `eval`/`exec`, segredos em logs, IDs na matriz de treino e configurações hardcoded.
- Verifique idempotência, paginação, qualidade, rastreabilidade e tratamento de erros.
- Verifique se métricas e gráficos são adequados ao algoritmo.
- Execute testes disponíveis e relate achados por severidade com evidências.
