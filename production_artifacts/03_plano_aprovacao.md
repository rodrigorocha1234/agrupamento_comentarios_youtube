# Plano de Aprovação — Incremento 3 (Fase 3): MLOps, MLflow Tracking, Regras de Negócio e Visualização Executiva

- **Versão:** 1.0
- **Data:** 24/10/2026
- **Responsável:** @pm / @arquiteto
- **Referência:** [`documentacao/especificacao_original_v4_1.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/documentacao/especificacao_original_v4_1.md)
- **Especificação Técnica:** [`production_artifacts/Technical_Specification_Fase3.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/production_artifacts/Technical_Specification_Fase3.md)

---

## 1. Ordem de Execução Proposta

### Etapa 1: Infraestrutura de MLOps e Observer MLflow
- Criar pacote `app/integracao_mlflow/`:
  - `observador_treinamento.py`: protocolo base do Observer.
  - `observador_nulo.py`: implementação Null Object para execução sem tracking.
  - `observador_mlflow.py`: integração real com o servidor MLflow local (`http://localhost:5000`), logando parâmetros, hashes SHA-256 de configuração, métricas e artefatos.
  - `registro_modelos.py`: serialização de pipelines treinados e modelos compatíveis.
- Testes: `tests/teste_mlflow.py`.

### Etapa 2: Otimização de Hiperparâmetros
- Criar pacote `app/otimizacao_hiperparametros/`:
  - `avaliador_objetivo.py`: cálculo de score composto e balanceado (Silhouette sem ruído ponderado pela proporção de ruído e penalização de clusters unitários).
  - `buscador_parametros.py`: busca em grade / aleatória orientada pelas faixas declaradas em `configuracoes/machine_learning/otimizacao.yaml`.
- Testes: `tests/teste_otimizacao.py`.

### Etapa 3: Regras de Negócio Declarativas Pós-Treinamento
- Criar pacote `app/regras_negocio/`:
  - `especificacao_negocio.py`: GoF Specification e Composite para predicados lógicos sobre métricas de cluster e atributos de reviews.
  - `rotulador_clusters.py`: rotulagem semântica sem alteração dos clusters de treino e sem obrigar retreinamento.
- Testes: `tests/teste_negocio.py`.

### Etapa 4: Visualizações e Consulta Analítica para Auditoria Humana
- Criar pacote `app/visualizacao_dados/`:
  - `gerador_graficos.py`: gráficos 2D Plotly (dispersão, silhueta, perfis por cluster).
  - `painel_executivo.py`: gerador de relatório integrado (HTML autônomo e Markdown estruturado).
- Criar pacote `app/servico_consulta/`:
  - `recuperador_reviews.py`: consulta e amostragem de reviews originais textuais associadas a cada cluster para leitura e auditoria humana.
- Testes: `tests/teste_visualizacao.py` e `tests/teste_consulta.py`.

### Etapa 5: Orquestração Ponta a Ponta e Integração Final
- Atualizar `app/treinamento_pipeline/executor_treinamento.py` para injetar o `ObservadorTreinamento`, aplicar o rotulador de negócio opcional e exportar os artefatos de visualização.
- Teste de integração ponta a ponta: `tests/teste_integracao_fase3.py`.
- Quality Gate: `pyright` strict (zero `Any`), `ruff check`, `pytest` com 100% de aprovação.
- Emissão do Relatório de QA e Handoff Final do ciclo.

---

## 2. Invariantes Mantidos

1. Python 3.12+, `pyright` strict sem qualquer uso de `Any`.
2. Módulos e pacotes com exatamente **duas palavras** separadas por `_`.
3. Padrões GoF sem `if/elif` no domínio (Observer, Specification, Composite, Registry, Strategy).
4. Sem PLN, LLM ou embeddings: o texto das avaliações é exclusivamente consultado por humanos para auditoria de negócio.
5. Preservação do Docker Compose único e dos volumes existentes.

---

## 3. Decisão de Aprovação Humana Requerida

Conforme as regras do repositório (`AGENTS.md`) e a skill `/planejar-incremento`:
- **Pergunta ao Usuário:** "Você aprova o plano técnico da Fase 3 (MLOps, MLflow Tracking via Observer, Otimização de Hiperparâmetros, Regras de Negócio Specification+Composite, Visualização Plotly e Consulta de Reviews Textuais) para darmos início à implementação incremental?"
