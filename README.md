# Steam Reviews Clustering — Google Antigravity Scaffold

Scaffold inicial para um projeto extensível de agrupamento não supervisionado de avaliações da Steam, sem PLN por padrão.

## Como usar
1. Extraia o ZIP em uma pasta de workspace.
2. Abra a pasta no Google Antigravity.
3. Leia `AGENTS.md`, `.agents/rules/` e `specs/`.
4. Comece pela Skill `planejar-steam` e revise a especificação antes de implementar.
5. Confira o `docker-compose.yml` existente antes de adicionar ou alterar infraestrutura.

## Princípios
- Python 3.12+; tipagem estrita; não usar `Any` nem `typing.Any`.
- Configuração variável em YAML.
- Não executar expressões Python arbitrárias vindas do YAML com `eval`/`exec`; usar catálogo de transformações validadas.
- PLN desativado por padrão; o texto da avaliação fica disponível para consulta humana, não como atributo de modelagem.
- Separar identificadores, atributos de treino e atributos de avaliação.
- Abstrair algoritmos, motores de processamento e fontes com contratos/Protocol e padrões Strategy, Factory, Adapter, Repository, Observer e Facade quando apropriado.
- Inspecionar primeiro os arquivos e a infraestrutura existentes. Não sobrescrever decisões aprovadas silenciosamente.

## Estrutura
- `.agents/agents/`: agentes especializados.
- `.agents/rules/`: restrições persistentes.
- `.agents/skills/`: procedimentos acionáveis com `SKILL.md`.
- `specs/`: especificações técnicas.
- `config/`: configuração de exemplo por responsabilidade.
- `app/`: ponto de partida do código da aplicação.
- `tests/`: ponto de partida dos testes.

Este ZIP é um scaffold documental/configuracional; não é uma implementação funcional completa do pipeline.
