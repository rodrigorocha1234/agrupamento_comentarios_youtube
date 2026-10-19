# Relatório de Entrega — Segregação Diária de Tendências e Métricas de Variação (@tendencias)

**Data:** 2026-10-14  
**Responsável:** `@tendencias` / `@arquiteto`  
**Referência Contratual:** `AGENTS.md`, `specs/04-tendencias-temporais.md`, `production_artifacts/Plano_Implementacao.md` (Adendo 13)

---

## 1. Resumo da Implementação

Foi implementada a **segregação temporal diária** na geração de tendências e tópicos da camada Ouro do Lakehouse, permitindo que cada dia de execução mantenha seu snapshot histórico isolado (`data=YYYY-MM-DD`). 

Além disso, foi incorporado o cálculo explícito e auditável do **percentual de crescimento e decrescimento** (`percentual_variacao`) de cada tópico em relação ao período anterior (tanto em nível de vídeo quanto consolidado por canal), com suporte a consultas parametrizadas por data na API REST (`?data=YYYY-MM-DD`).

---

## 2. Principais Funcionalidades Adicionadas

1. **Segregação Diária na Camada Ouro (S3):**
   - Chave por vídeo: `{prefixo}/id_canal={id_canal}/id_video={id_video}/tecnica={tecnica}/data={data_referencia}/topicos.parquet`
   - Chave consolidada: `{prefixo}/id_canal={id_canal}/consolidado/tecnica={tecnica}/data={data_referencia}/topicos.parquet`
   - As tendências calculadas hoje (`2026-10-14`) não sobrescrevem as de amanhã (`2026-10-15`), viabilizando a análise de evolução histórica contínua.

2. **Métricas Explícitas de Crescimento e Decrescimento:**
   - Adicionado o campo `percentual_variacao: float` em:
     - `ResultadoVariacao` (`DetectorVariacao`);
     - `RegistroTopicoOuro` (`CamadaOuro`);
     - `RespostaTopicoItem` (`FastAPI DTO`).
   - Lógica de cálculo:
     - Tópicos Novos: `+100.0%`
     - Tópicos em Crescimento: `round(((atual - anterior) / anterior) * 100, 2)` (taxa positiva)
     - Tópicos em Queda / Decrescimento: `round(((atual - anterior) / anterior) * 100, 2)` (taxa negativa, ex: `-60.0%`)
     - Sem dados ou estável: `0.0%` ou taxa proporcional medida.

3. **Filtro de Data na API REST:**
   - `GET /v1/canais/{id_canal}/tendencias?data=AAAA-MM-DD`: retorna as trends da data informada ou a mais recente caso omitido.
   - `GET /v1/canais/{id_canal}/videos/{id_video}/tendencias?data=AAAA-MM-DD`: idem para tendências a nível de vídeo individual.
   - Resposta inclui `data_referencia` e cada tópico inclui `percentual_variacao`.

---

## 3. Módulos e Componentes Atualizados

| Componente | Arquivo | Responsabilidade |
| :--- | :--- | :--- |
| **Detector de Variação** | `app/analise_tendencias/detector_variacao.py` | Cálculo do `percentual_variacao` explícito em `ResultadoVariacao`. |
| **Calculador de Tendências** | `app/analise_tendencias/calculador_tendencias.py` | Propagação de `data_referencia` e `percentual_variacao` para a Camada Ouro. |
| **Agregador de Visões** | `app/analise_tendencias/agregador_visoes.py` | Agregação consolidada por canal preservando a data de referência e recalculando o percentual de variação. |
| **Camada Ouro** | `app/gestao_dados/camada_ouro.py` | Suporte a particionamento por `data={data_referencia}`, métodos `listar_datas_tendencias` e `obter_chave_tendencias`. |
| **Configuração** | `config/entradas.yaml` | Padrões de chave atualizados com `data={data_referencia}`. |
| **Modelos & Provedor de Config** | `app/configuracao_geral/modelos_configuracao.py` e `provedor_configuracao.py` | Atualizados fallbacks com suporte a `data={data_referencia}`. |
| **Esquemas da API** | `app/servico_api/esquemas_respostas.py` | Inclusão de `data_referencia` e `percentual_variacao` nos modelos Pydantic. |
| **Rotas da API** | `app/servico_api/rotas_canais.py` e `app/servico_api/rotas_videos.py` | Adicionado parâmetro opcional de query `data` e retorno dos campos enriquecidos. |
| **Testes Unitários** | `tests/teste_tendencias.py` | Asserções de `percentual_variacao` e novo teste `test_segregacao_diaria_trends`. |

---

## 4. Evidências de Validação

- **Pyright Strict:** `0 errors, 0 warnings, 0 informations`
- **Pytest:** `47 passed, 12 warnings in 17.32s` (100% de sucesso)
