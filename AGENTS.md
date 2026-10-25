# Instruções do workspace

## Objetivo
Construir uma plataforma reutilizável de clustering de avaliações Steam, configurada por YAML, com PLN desativado por padrão.

## Ordem de trabalho obrigatória
1. Inspecionar o repositório, arquivos, dependências e `docker-compose.yml` existentes.
2. Ler as regras e especificações aplicáveis.
3. Elaborar ou atualizar o plano e a especificação técnica.
4. Solicitar aprovação antes de mudanças arquiteturais ou destrutivas.
5. Implementar em incrementos pequenos.
6. Executar testes, validações de configuração e verificações de tipagem disponíveis.
7. Documentar decisões, limitações e próximos passos.

## Arquitetura esperada
- Fonte Steam desacoplada de fontes futuras por contrato.
- Ingestão diária e processamento Bronze/Silver/Gold configuráveis.
- Pandas como padrão; Polars opcional por Strategy/Factory.
- Scikit-learn como motor padrão; PyCaret opcional por Strategy/Adapter.
- Algoritmos selecionáveis por YAML, inicialmente KMeans, DBSCAN e HDBSCAN.
- MLflow para rastreamento de experimentos.
- API e observabilidade separadas da lógica de domínio.
- Grafana, Prometheus, Loki e Alloy quando compatíveis com a infraestrutura existente.

## Restrições
- Não habilitar PLN implicitamente.
- Não usar `eval` ou `exec` para executar expressões arbitrárias do YAML.
- Não incluir identificadores como `steamid` e `recommendationid` como atributos de treino.
- Não presumir que todos os algoritmos possuem centroides ou atribuem todos os pontos a clusters.
- Não criar um segundo Compose sem necessidade comprovada.
- Não salvar artefatos locais se a configuração aprovada definir tracking/armazenamento remoto.
