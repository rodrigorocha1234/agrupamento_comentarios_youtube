# Clustering e avaliação

- Algoritmos, parâmetros, pré-processamento, seleção de atributos, redução dimensional e métricas devem vir do YAML.
- Começar com KMeans, DBSCAN e HDBSCAN por Strategy/Factory; não assumir equivalência entre suas capacidades.
- Separar atributos de treino, identificadores e atributos reservados para análise posterior.
- Registrar parâmetros, versões, métricas, diagnósticos e artefatos no MLflow.
- Não escolher o melhor modelo apenas por inspeção visual; usar métricas compatíveis com o algoritmo e o objetivo de negócio.
- Tratar ruído/outliers explicitamente, especialmente no DBSCAN/HDBSCAN.
- Não presumir centroides para algoritmos que não os definem.
- PLN e análises temporais devem permanecer opcionais e desativados por padrão.
