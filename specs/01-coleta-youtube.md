# Coleta incremental da YouTube Data API
- Resolver uploads dos canais via `channels.list(part=contentDetails)` -> playlist de uploads -> `playlistItems.list`, ou estratégia oficial equivalente, paginar e filtrar por `video.snippet.publishedAt` na janela N; alternativamente `search.list` ciente do custo de quota.
- `commentThreads.list(part=snippet,replies, videoId, maxResults=100, pageToken, order=time)` retorna comentários principais e subconjunto opcional de replies.
- Usar **`comments.list(parentId=..., maxResults=100, pageToken)` para obter todas as respostas**; não presumir que `part=replies` retorna todas.
- Para cada comentário armazenar `id`, `videoId`, `parentId` opcional, `etag`, `textOriginal`, `publishedAt`, `updatedAt`, `likeCount`, origem e instante de coleta; aplicar minimização de dados pessoais.
- Registro imutável de versão na bronze quando `updatedAt`, ETag ou hash mudarem; snapshot/estado atual na prata; idempotência em reprocessamentos; sem exclusão inferida de um resultado parcial.
- Tratar `commentsDisabled`, vídeos indisponíveis, paginação inconsistente, quotas 403/429, retry/backoff e paginação com token; não logar API key.
- Critérios: comentários com 0, 1 e >100 respostas; edição sem mudança de ID; paginação de vídeos/comentários; coleta vazia.
