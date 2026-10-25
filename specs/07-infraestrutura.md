# Especificação 07 — Infraestrutura

- Antes de modificar serviços, ler o `docker-compose.yml` e arquivos relacionados existentes.
- Não criar um segundo Compose sem justificativa técnica aprovada.
- Prometheus para métricas, Loki/Alloy para logs e Grafana para dashboards, quando presentes/aprovados.
- MLflow para tracking; armazenamento de artefatos configurável.
- Segredos via ambiente/secret manager.
- Documentar health checks, persistência, portas, redes, dependências e política de retenção.
