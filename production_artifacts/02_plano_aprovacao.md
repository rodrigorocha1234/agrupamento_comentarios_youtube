# Plano de Aprovação do Incremento 2 — Steam Reviews Clustering v4.1

- **Incremento:** Fase 2 — Motores Tabulares (Pandas e Polars), DSL Declarativa, Engenharia de Atributos, Pré-processamento e Modelagem de Clustering
- **Especificação Técnica:** [`production_artifacts/Technical_Specification_Fase2.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/production_artifacts/Technical_Specification_Fase2.md)
- **Status do Gate Humano:** **APROVADO**
- **Data da Proposta:** 24/10/2026
- **Data da Aprovação:** 24/10/2026 15:11:44-03:00
- **Autor da Aprovação:** Usuário
- **Responsável pela Proposta:** `@pm` (com parecer de `@ml_architect`, `@ml_engineer`, `@qa` e `@devops`)

---

## 1. Ordem de Execução Passo a Passo do Incremento 2

A implementação será executada de forma estritamente modular e incremental:

1. **Passo 1: Motores Tabulares (Pandas e Polars) e Interpretador de DSL**
   - Criação do protocolo `MotorTabular[T]` em `app/processamento_dados/`.
   - Implementação de `MotorPandas` e `MotorPolars` com operações vetorizadas.
   - Implementação de `InterpretadorDsl` executando filtros e operações declarativas sem `eval`/`exec`.
   - Criação de `FabricaMotores` (Registry/Factory sem `if/elif` de domínio).
   - *Validação:* Testes de paridade semântica comprovando que filtros e transformações geram o mesmo resultado em Pandas e Polars.

2. **Passo 2: Engenharia de Atributos e Seleção de Colunas**
   - Implementação de `app/engenharia_atributos/gerador_atributos.py` gerando `horas_ate_review`, `dias_desde_ultima_atividade`, `proporcao_jogo_recente`.
   - Implementação de `seletor_colunas.py` segregando a matriz de treino $X$ (numérica) dos metadados $Y_{meta}$ a partir de `atributos_modelo.yaml`.
   - *Validação:* Teste garantindo que identificadores (`steamid`, `recommendationid`) e texto de review nunca entrem na matriz $X$.

3. **Passo 3: Pipeline de Pré-processamento Componível**
   - Implementação de `app/preprocessamento_ml/` com transformadores:
     - `TransformadorImputador`: imputação com mediana/média.
     - `TransformadorEscalonador`: escalonamento com `StandardScaler` / `RobustScaler`.
     - `RedutorDimensionalidade`: redução opcional com `PCA` ou `TruncatedSVD`.
   - Criação do `PipelineComposto` (Composite GoF) com métodos `ajustar(X)` e `transformar(X)`.
   - Implementação de `FabricaPreprocessamento` a partir de `preprocessamento.yaml`.
   - *Validação:* Teste verificando que a etapa `ajustar()` ocorre estritamente nos dados de treino.

4. **Passo 4: Adaptadores de Clustering e Catálogo de Capacidades**
   - Implementação do modelo `CapacidadesAlgoritmo` em `app/agrupamento_modelos/capacidades_algoritmo.py`.
   - Implementação dos adaptadores scikit-learn:
     - `AgrupadorKMeans`: centroides ativos, predição fora da amostra habilitada.
     - `AgrupadorDbscan`: sem centroides, ruído rotulado como `-1`, predição fora da amostra desabilitada.
     - `AgrupadorHdbscan`: densidade hierárquica e ruído rotulado como `-1`.
   - Criação de `FabricaAgrupadores` a partir de `algoritmos.yaml`.
   - *Validação:* Teste de ajuste dos 3 algoritmos com verificação das capacidades declaradas.

5. **Passo 5: Avaliação Estatística de Clusters**
   - Implementação de `app/avaliacao_modelos/avaliador_clusters.py` calculando:
     - Silhouette Score (tratando ruído apropriadamente sem retorno de zeros fictícios).
     - Davies-Bouldin Index e Calinski-Harabasz.
     - Proporção de ruído e distribuição de registros por cluster.
   - *Validação:* Teste com clusters sintéticos bem separados e dados com ruído deliberado.

6. **Passo 6: Orquestrador de Treinamento, Testes Automatizados e QA**
   - Implementação de `app/treinamento_pipeline/executor_treinamento.py` orquestrando leitura da Silver, engenharia de atributos, pré-processamento, clustering e avaliação.
   - Execução completa da suíte de testes em `tests/`, checagem com `pyright --strict` e `ruff`.
   - Emissão do relatório de QA e handoff do Incremento 2.

---

## 2. Decisões Abertas para Alinhamento com o Usuário

1. **Motor Padrão de Execução:**
   - A configuração padrão define `pandas`. Ambos os motores (`pandas` e `polars`) serão implementados e testados para equivalência estrita.
   - *Proposta:* Manter `pandas` como padrão no `projeto.yaml` e permitir alternância declarativa para `polars`.
2. **Tratamento do Ruído no Cálculo da Silhouette:**
   - Em algoritmos de densidade (`DBSCAN` e `HDBSCAN`), pontos marcados com `-1` (ruído) podem distorcer severamente a silhueta ou levantar erro se houver apenas 1 cluster válido.
   - *Proposta:* A avaliação calculará a Silhouette desconsiderando os pontos de ruído (quando houver $\ge 2$ clusters além do ruído) e reportará a métrica com a flag `silhueta_sem_ruido: float | None`, além de explicitar a `taxa_ruido` em campo separado.

---

## 3. Registro do Gate de Aprovação Humana

| Campo | Valor / Status |
|---|---|
| **Incremento Proposto:** | Fase 2 — Motores Tabulares (Pandas/Polars), DSL Declarativa, Engenharia de Atributos, Pré-processamento e Modelagem de Clustering |
| **Especificação Rastreável:** | [`production_artifacts/Technical_Specification_Fase2.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/production_artifacts/Technical_Specification_Fase2.md) |
| **Status da Aprovação:** | **APROVADO** |
| **Autor da Decisão:** | Usuário |
| **Data da Decisão:** | 24/10/2026 15:11:44-03:00 |
| **Limites da Autorização:** | Somente implementação da Fase 2; nenhuma alteração destrutiva em contêineres ou serviços existentes. |
| **Condições Prévias:** | Autorização concedida para iniciar a criação dos módulos analíticos e de ML em `app/`. |
