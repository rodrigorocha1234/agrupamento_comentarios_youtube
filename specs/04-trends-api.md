# Tendências e API
- Janela atual e anterior de mesmo tamanho, com suporte mínimo e crescimento absoluto/relativo; denominar `novo` quando baseline=0 e atual>0; `estavel`, `crescendo`, `decrescendo` ou `sem_dados` com regras em YAML.
- Distinguir crescimento real da base de comentários de crescimento relativo proporcional: calcular contagem e participação por janela, filtrar ruído e registrar viés de amostragem.
- Ranking ouro por `id_canal`, `id_video`, `tecnica`; tópico com uma palavra, contagens atual/anterior, taxa e comentários associados/paginados.
- `GET /v1/canais/{id_canal}/tendencias?tecnica=...` (agregado dos vídeos).
- `GET /v1/canais/{id_canal}/videos/{id_video}/tendencias?tecnica=...`.
- `GET /v1/canais/{id_canal}/videos/{id_video}/clusters?tecnica=...`.
- `GET /v1/canais/{id_canal}/videos/{id_video}/topicos/{topico}/comentarios?tecnica=...&pagina=...`.
- `POST /v1/inferencias` -> adapter interno cliente HTTP de MLflow `/invocations` (schema do modelo registrado), autenticado no ambiente, com timeout/retry.
- Respostas têm `versao_execucao`, timestamp, técnica, escopo canal/vídeo, qualidade e origem. Validar request/response em testes de contrato.
