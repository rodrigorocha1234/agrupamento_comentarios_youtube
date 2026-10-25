# Configuração

- Toda opção variável do projeto deve ser configurável em YAML, com defaults documentados.
- Centralizar leitura e validação YAML em `ConfYAML` (módulo sugerido: `conf_yaml.py`).
- Validar estrutura, tipos, enums, limites e referências entre configurações antes de executar o pipeline.
- Colunas, filtros, transformações, engenharia de atributos e regras de negócio devem poder ser ativados/desativados por configuração.
- Transformações devem apontar para operações registradas e validadas; não executar código arbitrário do YAML.
- Manter arquivos YAML separados por responsabilidade.
