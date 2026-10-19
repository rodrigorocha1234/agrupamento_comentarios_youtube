# Persistência e dados
- Coleta uma vez ao dia por agendador existente ou execução externa parametrizada, não iniciar scheduler concorrente desnecessário.
- Não gravar dataset bruto, parquet, cache intermediário, modelos ou resultados da pipeline em disco local. Usar S3/MinIO para bronze/prata/ouro e MLflow para métricas/artefatos.
- Proibido instanciar Compose paralelo: primeiro ler o Compose na raiz do workspace, seus serviços e redes.
- Particionar todos os objetos S3 por camada/id_canal/id_video; nomes devem suportar snapshots/versionamento de comentário editado.
- Controlar idempotência pelo ID do comentário, ID do vídeo, `updatedAt`, `etag` quando aplicável e hash de conteúdo; distinguir resposta com `parentId`.
- Tratar quotas, paginação, backoff e perdas de permissões sem fabricar páginas ou dados.
- Preservar original no bronze, transformar no prata, publicar agregados validados no ouro.
- Não divulgar identificadores de autor desnecessários em API/observabilidade.
