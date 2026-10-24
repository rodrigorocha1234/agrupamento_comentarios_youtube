---
trigger: always_on
description: Infraestrutura única do Steam Reviews Clustering v4.1.
---
# Infraestrutura única
- Antes de editar infra, inspecionar `docker-compose.yml`, `compose.yaml` e arquivos equivalentes existentes.
- Reusar redes, serviços, volumes e stack de observabilidade e MLflow. Nunca criar Compose duplicado.
- Solicitar aprovação para migrações irreversíveis, deploy, exposição de portas ou alteração destrutiva.
Fonte de verdade: `documentacao/especificacao_original_v4_1.md`.
