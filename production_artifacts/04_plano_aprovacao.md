# Plano de Aprovação — Incremento 4 (Fase 4): Camada Gold Analítica, Dashboards de Negócio e Observabilidade

- **Versão:** 1.0
- **Data:** 24/10/2026
- **Responsável:** @pm / @arquiteto
- **Referência:** [`documentacao/especificacao_original_v4_1.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/documentacao/especificacao_original_v4_1.md)
- **Especificação Técnica:** [`production_artifacts/Technical_Specification_Fase4.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/production_artifacts/Technical_Specification_Fase4.md)

---

## 1. Ordem de Execução Proposta

### Etapa 1: Persistência da Camada Gold no Lakehouse
- Criar `app/gestao_datalake/escritor_ouro.py`:
  - `EscritorCamadaOuro`: serializa o dataset completo de clusters e a tabela analítica de resumo por jogo e persona em formato Parquet Snappy no S3/RustFS.
- Atualizar `app/gestao_datalake/__init__.py`.
- Teste unitário e de integração: `tests/teste_ouro.py`.

### Etapa 2: Catálogo Declarativo de Personas e Regras de Negócio
- Atualizar [`configuracoes/analises/negocio.yaml`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/configuracoes/analises/negocio.yaml) com catálogo completo de regras de segmentação comportamental para reviews da Steam (`ativado: true`).
- Teste de validação semântica com `ConfYAML`: `tests/teste_configuracao_negocio.py`.

### Etapa 3: Observabilidade Analítica e Dashboards Grafana
- Criar `app/observabilidade_metricas/medidor_negocio.py`:
  - `MedidorNegocio`: expõe métricas Prometheus de volumetria e engajamento por persona de cluster.
- Atualizar e validar templates JSON em `config_ob/dashboards/`:
  - `dashboard_modelos_clusters.json`
  - `dashboard_datalake_lakehouse.json`
- Testes: `tests/teste_observabilidade_negocio.py`.

### Etapa 4: Exportador de Relatórios Executivos
- Criar `app/visualizacao_dados/exportador_relatorios.py`:
  - `ExportadorRelatorios`: salva relatórios HTML e Markdown no diretório de artefatos e/ou Lakehouse.
- Atualizar `app/visualizacao_dados/__init__.py`.

### Etapa 5: Quality Gate e Homologação
- Executar `ruff check .` e `ruff format --check .`.
- Executar `pyright` no modo estrito (zero erros, zero `Any`).
- Executar `pytest -v` garantindo 100% de aprovação.
- Atualizar `production_artifacts/qa_relatorio.md` e `production_artifacts/handoff_final.md`.

---

## 2. Invariantes Mantidos

1. Python 3.12+, `pyright` strict sem qualquer uso de `Any`.
2. Módulos e pacotes com exatamente **duas palavras** separadas por `_`.
3. Padrões GoF sem `if/elif` no domínio.
4. Sem PLN, LLM ou embeddings: o texto das reviews é preservado estritamente para consulta e auditoria humana.
5. Reuso da infraestrutura Docker Compose única e contêineres ativos.

---

## 3. Decisão de Aprovação Humana Requerida

Conforme as regras do repositório (`AGENTS.md`) e a skill `/planejar-incremento`:
- **Pergunta ao Usuário:** "Você aprova o plano técnico da Fase 4 (Camada Gold Analítica no Lakehouse, Catálogo Completo de Personas de Negócio em YAML, Observabilidade Prometheus de Negócio, Alinhamento de Dashboards Grafana e Exportador de Relatórios Executivos) para iniciarmos a implementação incremental?"
