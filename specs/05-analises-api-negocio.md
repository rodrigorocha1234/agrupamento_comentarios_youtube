# Especificação 05 — Análises, API e negócio

## Análises configuráveis
- Dispersão de clusters 2D/3D.
- Distribuição e tamanho dos clusters.
- Perfil e resumo por cluster.
- Boxplot, violin plot, histogramas e matriz de correlação.
- PCA 2D/3D como projeção exploratória, não como verdade dos grupos.
- Análise de ruído/outliers.
- Distâncias a centroides apenas para algoritmos compatíveis.
- Relações entre votos, tempo de jogo e atributos estruturados.
- Comparação entre `appid` quando habilitada.
- Tabela interativa das reviews originais para consulta humana.
- Evolução temporal somente quando explicitamente habilitada.

## API
A API é opcional e deve seguir contratos aprovados. Candidatos:
`/health`, `/ready`, `/metrics`, `/api/v1/model`, `/api/v1/clusters`, `/api/v1/clusters/{cluster_id}`, `/api/v1/predict`, `/api/v1/predict-batch`.

Validar se o algoritmo selecionado suporta atribuição de novos pontos antes de expor endpoints de previsão.

## Regras de negócio
Regras ativáveis por YAML; documentar finalidade, entradas, saída e limites.
