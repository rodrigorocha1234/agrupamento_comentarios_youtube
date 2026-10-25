# Dados e API Steam

- Configurar parâmetros da API, paginação, idioma, filtro, período, tipo de review e limites em YAML.
- Não registrar API key, tokens ou segredos em logs; usar variável de ambiente/secret manager.
- Coletar de forma incremental e idempotente sempre que possível.
- Tratar cursores, limites, retries, timeout, erros transitórios e rate limits explicitamente.
- Separar dados brutos Bronze, dados normalizados Silver e tabelas/visões de análise Gold.
- Guardar identificadores para rastreabilidade, mas excluí-los da matriz de atributos de treino por padrão.
- Idioma da avaliação não prova nacionalidade ou residência do autor.
- O campo de texto da avaliação é apenas para consulta humana quando PLN estiver desativado.
