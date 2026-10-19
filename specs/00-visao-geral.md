# Visão de produto e critérios
Sistema não-LMM de agrupamento de comentários/respostas YouTube, identificação de assuntos em crescimento ou queda e API por canal/vídeo/algoritmo.

## Entradas
`config/entradas.yaml`: um ou muitos canais, retrospectiva em dias de publicação, coleta habilitada, idioma, parâmetros de NLP/clusterização/tendências, S3, serving e observabilidade. Segredo fora do YAML.

## Fluxo
YouTube API -> bronze S3 -> normalização/versionamento prata S3 -> representação/agrupamento -> tópicos/tendências ouro S3 -> MLflow e FastAPI -> métricas Grafana.

## Aceite
1. Dado um canal com vídeos publicados na janela N, enumerar vídeos elegíveis e buscar integralmente comentários e respostas paginados.
2. Reexecutar no dia seguinte sem duplicar conteúdo imutável, registrar versões alteradas.
3. Objetos S3 segregados em canal/vídeo em cada camada.
4. Executar três técnicas e consultar clusters, ruído, métricas e tendências separadas por técnica/canal/vídeo.
5. Cada tópico deve ser exatamente uma palavra não-stopword e trazer comentários associados, evidências e evolução temporal.
6. API integra MLflow serving internamente nas operações de inferência e consulta ouro nas operações analíticas.
7. Testes e validação de tipagem estrita; documentação da integração ao Compose existente.
