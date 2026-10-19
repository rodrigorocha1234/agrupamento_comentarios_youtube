# NLP e clustering
- spaCy para pt-BR (modelo selecionável em YAML): normalização, lemas, POS, stopwords internas+adicionais, preservar negações configuráveis, remover URLs/links sem apagar texto original.
- Representações TF-IDF (baseline), opcional CountVectorizer/Hashing com Strategy via YAML; MinDF/MaxDF/ngram parametrizados; reduzir com TruncatedSVD opcional.
- Técnicas KMeans, DBSCAN, HDBSCAN configuráveis por YAML; tuning com avaliação criteriosa, armazenar ruído separado (-1).
- Métricas: silhouette quando válida e >1 cluster efetivo, Davies-Bouldin, Calinski-Harabasz; estabilidade ARI/NMI quando aplicável, nº de clusters, fração de ruído, tempo/memória.
- Não ranquear técnicas apenas por silhouette quando ruído/densidade e distribuição tornam resultados incomparáveis; usar decisão documentada.
- Tópico: escolher lema de conteúdo (uma palavra) por grupo com POS permitido, frequência, TF-IDF e penalização de generalidade; garantir não stopword; se não houver rótulo elegível, sinalizar `sem_topico` em vez de inventar.
- Manter `id_comentario`, `id_video`, `id_canal`, `tecnica`, `cluster_id`, `topico`, `texto`/referência e versão de execução para drill-down.
