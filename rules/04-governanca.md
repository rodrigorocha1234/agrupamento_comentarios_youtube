# Governança multiagente
- @pm e @arquiteto documentam escopo e decisões; gerar `production_artifacts/Plano_Implementacao.md` antes de qualquer código.
- Aprovação humana explícita é requisito de avanço. Comentários no plano devem ser relidos e corrigidos antes de nova solicitação de aprovação.
- Skills são instruções de execução, não processos paralelos garantidos.
- Cada fase escreve handoff verificável, problemas em aberto, artefatos entregues e resultados de teste realmente executados.
- @qa deve bloquear passagem se contratos, testes, dados sensíveis ou regras de Python forem violados.
- @devops não iniciar nem alterar infraestrutura sem examinar o Compose e obter autorização quando envolver alteração destrutiva.
