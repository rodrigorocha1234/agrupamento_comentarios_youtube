---
trigger: always_on
description: Python e arquitetura do Steam Reviews Clustering v4.1.
---
# Python e arquitetura
- Python 3.12+, tipagem forte strict, proibir `Any`, usar `@override` onde sobrescrever, `@final` com justificativa e uma classe principal por módulo.
- Código próprio em português; módulos e pacotes Python com exatamente duas palavras separadas por `_`, ressalvadas exceções de tooling.
- Vetorização pandas/Polars; generators para páginas e lotes, nunca para substituir operações tabulares nativas.
- Sem seleção `if/elif` de tecnologia no domínio; Strategy/Registry/Factory e contratos estáveis. `if` para validação/fluxo é permitido.
- Preferir bibliotecas nativas e composição sobre abstrações ornamentais.
Fonte de verdade: `documentacao/especificacao_original_v4_1.md`.
