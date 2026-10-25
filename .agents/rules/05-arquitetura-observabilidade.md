# Arquitetura e observabilidade

- Usar Strategy/Factory para algoritmos e motores intercambiáveis; Adapter para integrações externas; Repository para persistência; Observer para eventos de experimento; Facade para orquestração.
- Preferir composição a herança rígida.
- Inspecionar `docker-compose.yml` e serviços existentes antes de alterá-los.
- Separar dashboards analíticos (perfil e qualidade dos clusters) de dashboards operacionais (latência, throughput, erros, retries, freshness e saúde dos serviços).
- Quando habilitados, integrar métricas com Prometheus, logs com Loki/Alloy e visualização com Grafana.
- Não duplicar serviços nem criar uma segunda stack de infraestrutura sem justificativa aprovada.
