---
name: fase-qa
description: Executa auditoria testes e validação estrita. Use quando o usuário solicitar esta fase do pipeline multiagente YouTube.
---
# Skill fase-qa

1. Leia `AGENTS.md`, `.agents/agents.md`, `rules/`, `specs/`, `config/entradas.yaml` e handoffs pertinentes.
2. **Gate:** exceto para `planejar` e etapa de planejamento de `startcycle`, verifique aprovação **explícita** em `production_artifacts/Plano_Implementacao.md` ou na conversa corrente; se ausente, pare sem implementar.
3. Atue como @qa; rode testes existentes, pyright strict e avaliações de aceites; documente comandos realmente executados e falhas sem inventar.
4. Implementações em `app/`, testes em `tests/`, handoff em `production_artifacts/fase-qa_entrega.md`. Não guardar dados locais nem criar Compose.
5. Informe arquivos criados/alterados, testes executados, riscos e critérios de aceite cumpridos.
