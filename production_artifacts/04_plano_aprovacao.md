# Plano de Aprovação — Incremento 4 (Fase 4): Camada Gold Analítica, Dashboards Grafana, Regras de Negócio e EDA

- **Versão:** 1.0
- **Data:** 24/10/2026
- **Responsável:** @pm / @arquiteto
- **Referência Oficial:** [`documentacao/especificacao_original_v4_1.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/documentacao/especificacao_original_v4_1.md) (Capítulo 21, Seções 10, 13, 14 e 16)
- **Especificação Técnica do Incremento:** [`production_artifacts/Technical_Specification_Fase4.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/production_artifacts/Technical_Specification_Fase4.md)

---

## 1. Ordem de Execução Proposta

### Etapa 1: Persistência da Camada Gold Analítica no Lakehouse
- Criar classe `EscritorCamadaOuro` em [`app/gestao_datalake/escritor_ouro.py`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/app/gestao_datalake/escritor_ouro.py):
  - Compatibilidade total com a interface `ArmazenamentoLake` e o cliente RustFS S3 local.
  - Gravação de dados de clusters particionados por `appid` em formato Parquet colunar Snappy: `gold/clusters/appid={appid}/ano={ano}/mes={mes}/modelo_{nome}_{versao}.parquet`.
  - Gravação de métricas estatísticas e tabela de perfis de negócio em `gold/metricas/appid={appid}/metricas_{versao}.parquet` e `resumo_executivo_{versao}.json`.
  - Geração de manifesto analítico idempotente com hash SHA-256 da execução.
- Testes unitários e de integração: `tests/teste_ouro.py`.

### Etapa 2: Telemetria Analítica de Clustering no Prometheus
- Criar classe `TelemetriaAnalitica` em [`app/observabilidade_metricas/telemetria_analitica.py`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/app/observabilidade_metricas/telemetria_analitica.py):
  - Instrumentação de métricas oficiais Prometheus:
    - `steam_clusters_total` (Gauge): número de clusters gerados.
    - `steam_clusters_ruido_proporcao` (Gauge): taxa de ruído (-1).
    - `steam_clusters_silhouette_score` (Gauge): coeficiente de silhueta.
    - `steam_clusters_davies_bouldin` (Gauge): índice Davies-Bouldin.
    - `steam_clusters_calinski_harabasz` (Gauge): índice Calinski-Harabasz.
    - `steam_gold_gravacoes_total` (Counter): contagem de gravações realizadas na camada Gold.
  - Baixa cardinalidade estrita: apenas labels `appid` e `algoritmo` (sem `steamid` ou `recommendationid`).
- Testes unitários: `tests/teste_telemetria_analitica.py`.

### Etapa 3: Provisionamento dos Dashboards Oficiais do Grafana
- Criar os painéis JSON oficiais em [`config_ob/dashboards/`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/config_ob/dashboards/):
  - `dashboard_steam_clusters.json`: volumetria de clusters, evolução de silhueta, métricas de coesão, distribuição de horas e percentual de avaliações positivas vs negativas por persona de negócio.
  - `dashboard_steam_lakehouse.json`: contagem de partições Bronze (JSON), Silver (Parquet) e Gold (Parquet), eventos da outbox e taxa de transferência.
  - `dashboard_steam_operacional.json`: requisições por segundo, respostas HTTP 429, latência de páginas e tempo de processamento dos lotes.
- Testes automatizados de validação de schemas JSON e targets Prometheus: `tests/teste_dashboards_grafana.py`.

### Etapa 4: Catálogo Rico de Regras Declarativas de Negócio
- Atualizar [`configuracoes/analises/negocio.yaml`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/configuracoes/analises/negocio.yaml) com catálogo representativo de personas reais de jogos:
  - `veteranos_criticos`: alta mediana de horas jogadas (>= 100h) e alto percentual de avaliações negativas (>= 50%).
  - `veteranos_leais`: alta mediana de horas jogadas (>= 100h) e alto percentual de avaliações positivas (>= 70%).
  - `novatos_satisfeitos`: baixa mediana de horas jogadas (< 30h) e alto percentual de avaliações positivas (>= 60%).
  - `novatos_frustrados`: baixa mediana de horas jogadas (< 20h) e alto percentual de avaliações negativas (>= 50%).
  - `formadores_opiniao`: mediana elevada de votos úteis (`votes_up` >= 5).
- Garantir compatibilidade com o padrão GoF Specification + Composite de `RotuladorClusters`.

### Etapa 5: Orquestrador Integrado de Exportação Gold e Relatórios EDA
- Criar classe `ExportadorOuro` em [`app/treinamento_pipeline/exportador_ouro.py`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/app/treinamento_pipeline/exportador_ouro.py):
  - Coordena a gravação do DataFrame enriquecido no RustFS S3 via `EscritorCamadaOuro`.
  - Atualiza as métricas analíticas no Prometheus via `TelemetriaAnalitica`.
  - Dispara a compilação do relatório executivo em HTML autônomo e Markdown via `PainelExecutivo`.
- Teste integrado de ponta a ponta: `tests/teste_integracao_fase4.py`.

### Etapa 6: Quality Gates e Handoff
- Execução de `ruff check . --fix && ruff format .`.
- Verificação `pyright` no modo `strict` em 100% dos novos módulos e suíte de testes (0 errors, 0 warnings, zero `Any`).
- Execução do `pytest` com validação de 100% dos testes passando.
- Emissão de `production_artifacts/qa_relatorio.md` e `production_artifacts/handoff_final.md`.

---

## 2. Invariantes Arquiteturais Mantidos

1. **Python 3.12+ Strict:** Proibição absoluta de `Any` ou `typing.Any`.
2. **Nomenclatura Canônica:** Nomes próprios em português; pacotes e módulos com exatamente duas palavras separadas por `_`.
3. **Padrões GoF sem Condicionais de Tecnologia:** Uso de Factory/Registry, Strategy, Specification, Composite, Adapter e Observer.
4. **Sem PLN ou Treinamento Textual:** Texto original mantido exclusivamente para consulta humana por analistas.
5. **Infraestrutura Única:** Reuso integral do Docker Compose root (`compose.yaml`), com S3 RustFS (:9000), MLflow (:5000), Prometheus (:9090) e Grafana (:3000).

---

## 3. Decisão de Aprovação Humana Requerida

Antes de dar início à criação dos arquivos de código e testes, solicitamos a aprovação formal do usuário para a execução do plano da **Fase 4**.
