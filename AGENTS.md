# Steam Reviews Clustering — diretrizes permanentes

Este workspace implementa a **especificação v4.1** em `documentacao/especificacao_original_v4_1.md`, que prevalece sobre exemplos deste pacote. Leia o capítulo pertinente antes de alterar código. Consulte também `.agents/agents.md` (matriz de responsabilidades).

## Invariantes
- Python >=3.12, tipagem strict sem `Any`/`typing.Any`, nomes próprios em português, módulos e pacotes próprios com exatamente duas palavras separadas por `_` (exceto arquivos especiais exigidos por ferramentas), uma classe principal por arquivo.
- SOLID e GoF justificados: Strategy, Factory/Registry, Adapter, Repository, Unit of Work, Observer, Facade, Composite/Specification/Chain of Responsibility. Proibir seleção de tecnologia, fonte, modelo ou gráfico por cadeias de `if/elif` no domínio; condicionais de validação, segurança e fluxo são legítimas.
- Configuração por YAML tipado, validado e versionado, sem `eval` ou `exec`, sem segredos no Git. `ConfYAML` é a fachada exclusiva de carregamento.
- Revisões textuais preservadas para consulta humana; **sem PLN, LLM, embeddings, sentimento derivado de texto ou treinamento textual** nesta versão. Idioma `brazilian` não garante residência no Brasil.
- Steam API → staging transacional (SQLite padrão; Postgres via Adapter/Repository) → outbox → Bronze/Silver/Gold MinIO/S3 → processamento Pandas/Polars → sklearn/PyCaret → MLflow → análises e painéis.
- Coleta histórica/incremental/revisitação diária, cursor/checkpoint, retries, backpressure com Iterator/Generator em I/O e vetorização em DataFrames; garantir idempotência.
- Sem duplicar Docker Compose/serviços. Inspecionar root Compose, redes e volumes antes de alterar infraestrutura. Nenhuma mudança destrutiva automática.
- Observabilidade com Prometheus, Grafana, Loki, Alloy, MLflow; SLIs/SLOs; evitar cardinalidade por IDs pessoais. Testes e Quality Gates em cada entrega.
- Aprovação humana explícita após especificação e antes de mudanças invasivas, migrações destrutivas, deploy, alteração de infraestrutura ou uso de credenciais.

## Modo de trabalho
1. Inspecione árvore, Compose e arquivos de configuração reais. Registre fatos vs. hipóteses.
2. Gere plano rastreável à especificação; declare entregáveis, testes e riscos.
3. Faça mudança incremental mínima; nunca declare execução de testes que não ocorreu.
4. Produza handoff em `production_artifacts/` com decisões, evidências, comandos e pendências.
5. Utilize a skill `/ciclo-completo` ou skills especializadas. Agentes CLI em `.agents/agents/*/agent.md`.
