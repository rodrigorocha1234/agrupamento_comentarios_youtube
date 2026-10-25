# Especificação 06 — Observabilidade e QA

## Observabilidade operacional
- Latência p50/p95/p99.
- Throughput e quantidade de reviews recebidas.
- Erros, retries, timeouts, rate limits e falhas por etapa.
- Freshness, atraso de coleta, deduplicação e qualidade dos dados.
- Duração e status de cada etapa do pipeline.
- Tempo de treino, algoritmo, métricas e ID do experimento MLflow.
- Saúde da API e infraestrutura.

## Dashboards
- Operação/coleta.
- Qualidade e camadas de dados.
- Engenharia de atributos.
- Experimentos e desempenho de clustering.
- Perfil e distribuição dos clusters.
- API e infraestrutura.

## QA
Testar configuração inválida, resposta vazia, dados duplicados, missing values, atributos constantes, cluster único, ruído, ausência de centroides e algoritmo sem suporte a novos pontos.
