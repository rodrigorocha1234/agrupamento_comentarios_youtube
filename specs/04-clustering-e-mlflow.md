# Especificação 04 — Clustering e MLflow

## Algoritmos iniciais
- KMeans
- DBSCAN
- HDBSCAN (dependência opcional, validar disponibilidade)

## Extensibilidade
- Contrato de algoritmo via `Protocol`.
- Strategy para implementação por algoritmo.
- Factory/registry para resolver algoritmo por chave de configuração.
- Adapter para motores sklearn e PyCaret, se ambos forem aprovados.
- Observer para publicar métricas/eventos ao MLflow.
- Não presumir centroides, probabilidades ou predição out-of-sample em todos os algoritmos.

## Avaliação
Configurar métricas adequadas aos dados e ao algoritmo: silhouette, Davies–Bouldin, Calinski–Harabasz, proporção de ruído, número/tamanho dos clusters e estabilidade. Explicar limitações de cada métrica.

## Tracking
Registrar parâmetros, métricas, versões de bibliotecas, assinatura quando aplicável e artefatos de avaliação no MLflow.
