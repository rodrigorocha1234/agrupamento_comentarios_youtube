# Especificação 02 — Coleta e Data Lake

## Fonte
Endpoint de reviews da Steam: `IUserReviewsService/GetAppReviews/v1/`.

## Requisitos
- Todos os parâmetros da API configuráveis em YAML; segredos por ambiente.
- Suportar paginação/cursor, retries, timeout, limites e coleta incremental.
- Registrar timestamp da coleta, `appid`, status, quantidade recebida e cursor/checkpoint.
- Deduplicar por identificador estável da review, mantendo histórico quando necessário.

## Camadas
- Bronze: payload bruto e metadados de coleta.
- Silver: schema normalizado, tipos consistentes, deduplicação e qualidade.
- Gold: tabelas/visões para atributos, treino, avaliação e relatórios.

## Campos relevantes
`recommendationid`, `appid`, `review`, `timestamp_created`, `timestamp_updated`, `voted_up`, `votes_up`, `votes_funny`, `weighted_vote_score`, `comment_count`, `steamid`, `num_reviews`, `playtime_forever`, `playtime_last_two_weeks`, `playtime_at_review`, `last_played`.

Os campos disponíveis podem variar; validar contra o payload real da API.
