---
name: startcycle
description: Orquestra o ciclo completo com gates humanos. Use quando o usuário solicitar esta fase do pipeline multiagente YouTube.
---
# Skill startcycle

1. Leia `AGENTS.md`, `.agents/agents.md`, `rules/`, `specs/`, `config/entradas.yaml` e handoffs pertinentes.
2. **Gate:** exceto para `planejar` e etapa de planejamento de `startcycle`, verifique aprovação **explícita** em `production_artifacts/Plano_Implementacao.md` ou na conversa corrente; se ausente, pare sem implementar.
3. @pm -> @arquiteto; ler fontes; atualizar plano; pedir aprovação explícita; só então chamar fases de engenharia; coletar evidências QA e registrar status final.
4. Implementações em `app/`, testes em `tests/`, handoff em `production_artifacts/startcycle_entrega.md`. Não guardar dados locais nem criar Compose.
5. Informe arquivos criados/alterados, testes executados, riscos e critérios de aceite cumpridos.
