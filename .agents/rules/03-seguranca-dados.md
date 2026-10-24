---
trigger: always_on
description: Segurança e semântica dos dados do Steam Reviews Clustering v4.1.
---
# Segurança e semântica dos dados
- Review em idioma `brazilian` não comprova residência no Brasil. Nunca fazer essa inferência.
- Sem PLN/LLM/embeddings ou texto como feature. Texto original somente consulta humana.
- Não logar chave de API, steamid, recommendationid ou conteúdo pessoal completo; exigir política de retenção e acesso.
Fonte de verdade: `documentacao/especificacao_original_v4_1.md`.
