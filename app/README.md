# Aplicação

Implementar aqui o pipeline em módulos com responsabilidades claras. Sugestão inicial:

- `conf_yaml.py`: leitura e validação centralizada das configurações.
- `fonte_dados.py`: contratos de fonte.
- `coletor_steam.py`: adaptador de coleta da Steam.
- `repositorio_dados.py`: persistência e acesso às camadas.
- `preparador_dados.py`: validação, limpeza e preparação.
- `engenheiro_atributos.py`: seleção e criação segura de atributos.
- `motor_clustering.py`: contrato/Strategy de clustering.
- `fabrica_clustering.py`: resolução do algoritmo.
- `avaliador_clusters.py`: métricas compatíveis.
- `rastreador_mlflow.py`: integração de tracking/Observer.
- `analisador_clusters.py`: análises de negócio.
- `fachada_pipeline.py`: orquestração.
- `api_clusters.py`: camada API, se aprovada.

Os nomes são sugestões iniciais e devem ser ajustados para cumprir as convenções já existentes no repositório.
