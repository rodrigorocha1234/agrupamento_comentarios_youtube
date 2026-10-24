---
trigger: model_decision
description: Clustering e ML do Steam Reviews Clustering v4.1.
---
# Clustering e ML
- Consultar quando modificar treinamento, avaliação, inferência ou visuais ML.
- KMeans, DBSCAN e HDBSCAN possuem capacidades diferentes. Nunca supor `predict()` universal nem centroides universais.
- Métricas indefinidas precisam ser relatadas como indisponíveis e nunca zero fictício.
- Evitar leakage em transformações, reamostragens e tuning. Não importar CV supervisionada como padrão de clustering.
Fonte de verdade: `documentacao/especificacao_original_v4_1.md`.
