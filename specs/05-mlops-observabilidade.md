# MLOps e operação
- MLflow: experiências por técnica, tracking de parâmetros, versões, datasets referenciados no S3, métricas de clusters, artifacts manifestos, promoção de modelos somente após gates; endpoints de serving conforme disponibilidade no Compose.
- Prometheus: contadores de coleta, tempo da etapa, páginas API, retries/erros, volume por camada, volume de ruído, tempo de inferência FastAPI->MLflow, HTTP requests, p50/p95/p99; cardinalidade controlada (não rotular métricas com IDs de vídeos/comentários).
- Grafana: painéis por técnica e estado da ingestão; alertas para falha da coleta diária, quota, latência e ausência de dados esperados.
- Logs sem token/API key e sem texto de comentário em traces; usar Loki/Alloy se disponíveis.
- Inspecionar `docker-compose.yml`, `compose.yaml` e serviços já em execução; não criar nem iniciar novo stack automaticamente.
- Critérios de QA: testes offline com fixtures sintéticas; integração S3/MLflow/YouTube apenas se credenciais e ambiente aprovados; sem declarar sucesso fictício.
