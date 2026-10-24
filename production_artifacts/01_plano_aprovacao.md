# Plano de Aprovação do Incremento 1 — Steam Reviews Clustering v4.1

- **Incremento:** Fase 1 — Fundação Arquitetural, `ConfYAML`, Ingestão Lazy Steam, Staging Transacional SQLite e Outbox Data Lake
- **Especificação Técnica:** [`production_artifacts/Technical_Specification.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/production_artifacts/Technical_Specification.md)
- **Status do Gate Humano:** **APROVADO**
- **Data da Proposta:** 24/10/2026
- **Data da Aprovação:** 24/10/2026 14:42:17-03:00
- **Autor da Aprovação:** Usuário
- **Responsável pela Proposta:** `@pm` (com parecer de `@ml_architect`, `@data_engineer` e `@devops`)

---

## 1. Ordem de Execução Passo a Passo do Incremento 1

A implementação será executada de forma estritamente incremental e rastreável, sem pular etapas ou realizar modificações destrutivas na infraestrutura:

1. **Passo 1: Alinhamento de Ambiente e Configuração Declarativa (`ConfYAML`)**
   - Criação do catálogo de 21 arquivos YAML em `configuracoes/` conforme a estrutura descrita na especificação v4.1.
   - Implementação de `ConfYAML` em `app/configuracao_geral/conf_yaml.py` e validação com Pydantic (`extra="forbid"`).
   - Criação de `.env.example` e atualização das variáveis no `.env` (`STEAM_API_KEY`, `STAGING_SQLITE_PATH`, `DATA_BUCKET=steam-reviews`).
   - *Validação:* Teste unitário garantindo carregamento, imutabilidade, tipagem e rejeição de campos desconhecidos.

2. **Passo 2: Contratos de Domínio e Entidades Imutáveis**
   - Criação dos módulos em `app/dominio_contratos/` definindo entidades (`ReviewSteam`, `AutorSteam`, `PaginaReviews`) como `dataclass(frozen=True, slots=True)`.
   - Definição dos protocolos de domínio (`ClienteSteam`, `GeradorPaginas`, `RepositorioStaging`, `UnidadeTrabalho`, `ArmazenamentoLake`).
   - *Validação:* Checagem com `pyright` strict garantindo zero uso de `Any`.

3. **Passo 3: Adaptador e Gerador Paginado da API Steam**
   - Implementação de `app/extracao_steam/` com chamadas ao serviço `IUserReviewsService/GetAppReviews/v1`.
   - Gerador lazy `iterar_paginas(appid, cursor)` baseado em `Iterator[PaginaReviews]`.
   - Tratamento de HTTP 429, detecção de repetição de cursor e backoff exponencial com jitter.
   - *Validação:* Testes com respostas mockadas verificando consumo sem retenção integral na memória e parada correta no cursor final.

4. **Passo 4: Staging Transacional com SQLite**
   - Implementação de `app/persistencia_staging/` com as 7 tabelas relacionais em SQLite (`journal_mode=WAL`).
   - Implementação de `RepositorioStaging` e `UnidadeTrabalho` para gravação atômica por lotes (`itertools.batched`).
   - Gestão de checkpoints na tabela `marcadores_coleta` e registro de eventos na `eventos_publicacao`.
   - *Validação:* Teste de inserção em lote, rollback em falha simulada e verificação de integridade referencial.

5. **Passo 5: Data Lake e Despachante da Outbox**
   - Implementação de `app/gestao_datalake/` com conector RustFS S3 via `boto3`.
   - Despachante de outbox para consumo de eventos e gravação assíncrona/desacoplada:
     - Bronze: JSON bruto imutável particionado por appid e data.
     - Silver: Dataset tabular normalizado em formato Parquet (`pyarrow`).
   - *Validação:* Teste de leitura da outbox, escrita no S3 local e marcação de status publicado.

6. **Passo 6: Telemetria, Quality Gate e Testes Automatizados**
   - Instrumentação de métricas Prometheus (`app/observabilidade_metricas/registro_telemetria.py`).
   - Implementação do validador de integridade e qualidade (`validador_qualidade.py`).
   - Execução completa da suíte de testes em `tests/` e verificação com `pyright --strict`.
   - Geração do handoff final de entrega em `production_artifacts/`.

---

## 2. Decisões Abertas para Alinhamento com o Usuário

1. **Nome do Bucket do Data Lake:**
   - O Docker Compose atual configura `DATA_BUCKET: youtube-comentarios`.
   - *Proposta:* Atualizar a variável de ambiente `.env` para `DATA_BUCKET=steam-reviews` para refletir o domínio da v4.1 sem quebrar o container `create-bucket` (ele cria ambos).
2. **Jogos Iniciais de Teste e Validação:**
   - *Proposta:* Utilizar os jogos recomendados no exemplo da especificação v4.1:
     - `appid: 427520` (*Factorio*)
     - `appid: 526870` (*Satisfactory*)
   - Esses jogos possuem alto volume de avaliações e perfil ideal para validação de paginação e clustering.
3. **Chave de API da Steam (`STEAM_API_KEY`):**
   - O endpoint público `IUserReviewsService/GetAppReviews/v1` permite execução anônima (sem chave), embora compartilhe um limite de requisições menor sujeito a HTTP 429.
   - *Proposta:* A arquitetura suportará tanto execução com chave (`key_env: STEAM_API_KEY`) quanto execução pública anônima (`key_env: null` ou chave ausente).

---

## 3. Registro do Gate de Aprovação Humana

| Campo | Valor / Status |
|---|---|
| **Incremento Proposto:** | Fase 1 — Fundação, ConfYAML, Coleta Lazy, Staging SQLite e Lakehouse |
| **Especificação Rastreável:** | [`production_artifacts/Technical_Specification.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/production_artifacts/Technical_Specification.md) |
| **Status da Aprovação:** | **APROVADO** |
| **Autor da Decisão:** | Usuário |
| **Data da Decisão:** | 24/10/2026 14:42:17-03:00 |
| **Limites da Autorização:** | Somente implementação da Fase 1; nenhuma alteração destrutiva em contêineres ou serviços existentes. |
| **Condições Prévias:** | Autorização concedida para criar os módulos em `app/` e arquivos em `configuracoes/`. |
