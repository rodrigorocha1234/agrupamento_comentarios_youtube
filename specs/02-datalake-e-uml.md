# Data lake e modelagem UML
## Layout S3 (exemplo)
- `s3://<bucket>/bronze/id_canal=<id>/id_video=<id>/data_coleta=<YYYY-MM-DD>/lote=<uuid>.jsonl` (histórico bruto)
- `s3://<bucket>/prata/id_canal=<id>/id_video=<id>/versao=<stamp>/comentarios.parquet`
- `s3://<bucket>/ouro/id_canal=<id>/id_video=<id>/tecnica=<modelo>/janela=<periodo>/topicos.parquet`
- Visão agrupada por canal no ouro por agregação dos vídeos (não misturar canais silenciosamente).

## Entidades e relações
- Canal **agrega** Vídeos (existência do vídeo é independente do catálogo local).
- Vídeo **agrega** Comentários, e Comentário **associa-se** a Comentário pai (replies com `parentId`).
- Pipeline **compõe** fases e estratégias injetadas; etapa não gerencia ciclo de vida global de serviços externos.
- Serviço tipado `Protocol[TipoEntrada_contra, TipoSaida_co]` ou Protocol genérico compatível com variance, TypeVar e Generic, sem Any; adapters para API, MinIO, MLflow.
- Registry/Factory escolhe estratégias YAML e preserva princípio aberto/fechado.

## Consistência
- Hash determinístico, versionamento por chave de comentário+timestamp+hash, escrita idempotente, manifesto por lote e processamento reexecutável.
- Metadados de lote e checkpoint persistidos no S3/DB já existente, nunca em dataset local.
