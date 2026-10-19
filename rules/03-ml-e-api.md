# Clusterização, trends e serving
- Comparar KMeans, DBSCAN e HDBSCAN separadamente; não forçar número idêntico de clusters; label -1 é ruído quando aplicável.
- Não usar LLM para nomear ou agrupar tópicos; nome = 1 lema, não stopword, com POS/frequência/TF-IDF e critérios auditáveis.
- Tendência comparável: considerar baseline anterior, suporte mínimo, crescimento e decrescimento e janelas temporais iguais; divisões por zero explícitas.
- Resultados duplos obrigatórios: visão por canal e visão por vídeo, segmentadas por técnica de agrupamento.
- Registrar parâmetros, métricas, versões e artefatos no MLflow; FastAPI chama serving de MLflow internamente por Adapter HTTP, sem prometer MLflow genérico para consultas analíticas (consultas de tendências vêm do ouro S3).
- Monitorar latências e erros da API, coleta, volumes, ruído, qualidade de clusters e variação dos tópicos.
