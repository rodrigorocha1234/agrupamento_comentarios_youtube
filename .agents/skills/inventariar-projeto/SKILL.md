---
name: inventariar-projeto
description: Audita repositório, Docker Compose, dependências e fontes de configuração existentes.
---
# Skill: inventariar-projeto

## Referências obrigatórias
- `AGENTS.md` e `documentacao/especificacao_original_v4_1.md`.
- `.agents/agents.md` e persona correspondente em `.agents/agents/<papel>/agent.md`.

## Procedimento
1. Localizar arquivos Compose da raiz, `.env.example`, dependências, migrations, tests e configuração.
2. Listar serviços ativos apenas quando comando de inspeção real puder ser executado; caso contrário diferenciar definido de executando.
3. Mapear requisitos da v4.1 para componentes existentes, ausentes e conflitantes.
4. Registrar `production_artifacts/inventario.md`. Não sobrescrever Compose, arquivos existentes ou segredos.

## Saída padrão
Entregar mudanças versionáveis e um resumo em `production_artifacts/`, com itens concluídos, decisões, comandos realmente executados, validações e pendências. Respeitar gates humanos.
