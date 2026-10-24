# Pacote de agentes Google Antigravity — Steam Reviews Clustering v4.1

Configuração de **agentes personalizados**, **regras persistentes** e **skills** pronta para incorporar à raiz de um repositório Antigravity; **não é um aplicativo implementado** e não inicia serviços.

## Instalação
1. Faça backup/commit da raiz do seu projeto.
2. Extraia o conteúdo **na raiz do repositório** (sem aninhar outra pasta). Mescle arquivos com cuidado se já existirem `.agents/` e `AGENTS.md`.
3. Abra a raiz como workspace Antigravity e confira reconhecimento das skills.
4. Experimente `/inventariar-projeto`, depois `/planejar-incremento`. Após aprovação explícita, `/ciclo-completo` ou skills específicas.
5. No Antigravity CLI, `/agents` permite escolher as personas instaladas em `.agents/agents/<nome>/agent.md`; suporte de delegação muda conforme a superfície.

## Notas de compatibilidade (consulta em 24/10/2026)
- A documentação oficial reconhece regras em `.agents/rules/*.md` com frontmatter `trigger` e skills em `.agents/skills/<nome>/SKILL.md`.
- A documentação informa descontinuação dos **workflows legados** em outubro de 2026; por isso **não** foi criado `.agents/workflows/`.
- O artigo de Peterson Pereira orienta ciclo com @pm, @engineer, @qa, @devops e Approval Gate; este pacote expande as especialidades ao domínio de ML/engenharia de dados.
- `.agents/agents.md` é catálogo de papéis para humanos/IDE; os arquivos `agent.md` individuais são custom agents da **CLI** documentados oficialmente. A existência dos arquivos não garante execução autônoma paralela no IDE.

## Conteúdo
- `AGENTS.md`: regras de escopo geral.
- `.agents/rules/`: regras ativas e condicionais.
- `.agents/agents/`: 9 personas customizadas.
- `.agents/skills/`: 10 procedimentos reutilizáveis por slash command.
- `documentacao/especificacao_original_v4_1.md`: anexo integral como fonte de verdade.
- `documentacao/roteiro_implementacao.md`: sequência incremental.
- `production_artifacts/`: modelos para handoff e aprovação.

## Fontes verificadas
- Artigo: https://pt.linkedin.com/pulse/google-antigravity-na-pr%C3%A1tica-criando-um-pipeline-com-peterson-alves-nm7of
- Regras oficiais: https://antigravity.google/docs/rules/
- Skills oficiais: https://antigravity.google/docs/skills/
- Migração workflows → skills: https://antigravity.google/docs/migration/workflows-to-skills/
- Custom agents na CLI: https://antigravity.google/docs/cli/commands/agents/

## Limite
Não foi fornecido repositório completo nem Compose existente nesta solicitação; o pacote determina que o primeiro agente faça o inventário real **antes** de propor alterações. Nenhum serviço ou teste de implementação foi executado.
