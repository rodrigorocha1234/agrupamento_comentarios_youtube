---
trigger: always_on
description: Configuração declarativa do Steam Reviews Clustering v4.1.
---
# Configuração declarativa
- Toda mudança de comportamento parametrizável por YAML validado, com versão/hash e `ConfYAML` como ponto único de leitura.
- Não usar `eval`/`exec` ou expressões Python arbitrárias do YAML. DSL declarativa por operadores registrados.
- Segredos somente por variáveis de ambiente ou cofre; `extra=forbid` e validação cruzada entre arquivos.
Fonte de verdade: `documentacao/especificacao_original_v4_1.md`.
