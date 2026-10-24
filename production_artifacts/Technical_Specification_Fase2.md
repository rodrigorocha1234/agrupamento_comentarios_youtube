# Especificação Técnica — Steam Reviews Clustering v4.1
## Incremento 2: Motores Tabulares (Pandas/Polars), DSL Declarativa, Engenharia de Atributos, Pré-processamento e Modelagem de Clustering

- **Status:** Proposta Técnica para Aprovação Humana (Approval Gate)
- **Autor / Persona:** `@pm` em conjunto com `@ml_architect`, `@ml_engineer`, `@qa` e `@devops`
- **Data:** 24/10/2026
- **Fonte de Verdade:** [`documentacao/especificacao_original_v4_1.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/documentacao/especificacao_original_v4_1.md) (Capítulos 8 a 11)
- **Incremento Anterior Homologado:** [`production_artifacts/handoff_final.md`](file:///home/rodrigo/PycharmProjects/agrupamento_comentarios_youtube/production_artifacts/handoff_final.md)

---

## 1. Visão Geral e Objetivos do Incremento 2

Com a camada de ingestão, staging transacional SQLite e Data Lake (Bronze/Silver) entregues e validadas no Incremento 1, este documento formaliza o **Incremento 2 (Fase 2)** com foco no processamento analítico e no núcleo de Machine Learning:

1. **Motores Tabulares com Abstração Formal (Pandas e Polars):** Implementar o contrato `MotorTabular[T]` suportando Pandas (padrão vetorizado) e Polars (vetorizado nativo), configuráveis via YAML sem acoplamento no domínio.
2. **DSL/AST Declarativa Segura:** Executar seleções, filtros (`WHERE`) e transformações de colunas a partir das especificações declarativas do YAML (`filtros_dados.yaml`, `criacao_atributos.yaml`, `transformacao_atributos.yaml`), proibindo expressamente o uso de `eval`, `exec` ou compilação dinâmica de Python.
3. **Engenharia de Atributos Tabulares sem PLN:** Gerar atributos analíticos exclusivamente numéricos e temporais (`horas_ate_review`, `dias_desde_ultima_atividade`, `proporcao_jogo_recente`), isolando a matriz de treinamento $X$ dos metadados de auditoria e texto de reviews.
4. **Pipeline de Pré-processamento Componível (GoF Composite/Strategy):** Montar cadeias de transformação ordenadas (imputação com mediana/média, escalonamento com `StandardScaler`/`RobustScaler`, redução opcional com `PCA`/`TruncatedSVD`) com isolamento estrito contra *data leakage* (ajuste exclusivo nos dados de treino).
5. **Algoritmos de Clustering e Catálogo de Capacidades:** Implementar adaptadores scikit-learn para `KMeans`, `DBSCAN` e `HDBSCAN`, guiados por um catálogo tipado de capacidades (`CapacidadesAlgoritmo`) que explicita se o algoritmo suporta predição fora da amostra, centroides ou rotulagem de ruído.
6. **Avaliação Estatística de Qualidade:** Calcular Silhouette Score, índice Davies-Bouldin, Calinski-Harabasz e métricas de distribuição/ruído com tratamento estatístico transparente (sem retorno de zeros fictícios em caso de ruído).

---

## 2. Escopo do Incremento 2

### 2.1. No Escopo (Fase 2)
- **Motor Tabular e DSL (`app/processamento_dados/`):**
  - Protocolo `MotorTabular[T]` definindo operações vetorizadas e filtros.
  - Implementação `MotorPandas` e `MotorPolars` com paridade semântica testada.
  - Interpretador seguro de DSL declarativa (`InterpretadorDsl`) com operadores registrados:
    - Comparações: `igual`, `maior`, `maior_igual`, `menor`, `menor_igual`, `entre`, `pertence`.
    - Transformações: `dividir_constante`, `multiplicar_constante`, `soma`, `subtrai`, `log1p`, `converter_dias_desde_referencia`.
  - `FabricaMotores` com padrão Registry/Factory para seleção por chave ("pandas", "polars") sem `if/elif`.
- **Engenharia de Atributos (`app/engenharia_atributos/`):**
  - Seletor de colunas a partir de `atributos_modelo.yaml`.
  - Gerador de atributos derivados a partir dos campos brutos da camada Silver.
  - Separação formal de matriz de treino $X$ (numérica) e metadados $Y_{meta}$ (`appid`, `recommendationid`, `voted_up`, etc.).
- **Pré-processamento Componível (`app/preprocessamento_ml/`):**
  - `TransformadorImputador`: imputação com mediana ou média.
  - `TransformadorEscalonador`: escalonamento com `StandardScaler` ou `RobustScaler`.
  - `RedutorDimensionalidade`: redução opcional com `PCA` ou `TruncatedSVD`.
  - `PipelineComposto`: padrão GoF Composite encadeando transformações com métodos `ajustar(X)` e `transformar(X)`.
  - `FabricaPreprocessamento`: Factory/Registry para montagem do pipeline a partir de `preprocessamento.yaml`.
- **Algoritmos de Clustering (`app/agrupamento_modelos/`):**
  - Modelo imutável `CapacidadesAlgoritmo`:
    - `suporta_predicao_fora_da_amostra: bool`
    - `possui_centroides: bool`
    - `gera_ruido: bool`
    - `rotulo_ruido: int = -1`
  - Adaptadores: `AgrupadorKMeans`, `AgrupadorDbscan`, `AgrupadorHdbscan`.
  - `FabricaAgrupadores`: Registry/Factory para instanciar algoritmos a partir de `algoritmos.yaml`.
- **Avaliação de Modelos (`app/avaliacao_modelos/`):**
  - Avaliador calculando Silhouette Score (desconsiderando ruído para amostras válidas), Davies-Bouldin Index e Calinski-Harabasz.
  - Contagem de clusters, proporção de ruído e distribuição de registros.
  - Modelo imutável `ResultadoAvaliacao`.
- **Orquestrador de Treinamento (`app/treinamento_pipeline/`):**
  - `ExecutorTreinamento`: carrega dataset da Silver, executa DSL e engenharia de atributos, ajusta o pré-processamento, treina o agrupador, avalia os clusters e persiste resultados na camada Gold (`gold/clusters/`).

### 2.2. Fora de Escopo Deste Incremento (Fases Subsequentes)
- **Fase 3:** Tuning avançado de hiperparâmetros (GridSearch / Optuna), Observer de tracking do MLflow e serving REST de inferência.
- **Fase 4:** Motor de regras de negócio pós-treino (Specification/Composite) para rotulagem sem retreino e geração de relatórios no Grafana.
- **Fase 5:** Análise temporal comparativa entre treinos com alinhamento de IDs de clusters permutados.

---

## 3. Diretrizes Arquiteturais e Padrões GoF Obrigatórios

1. **Nomenclatura Estrita:** Todos os módulos e pacotes com exatamente 2 palavras separadas por `_` (`processamento_dados`, `engenharia_atributos`, `preprocessamento_ml`, `agrupamento_modelos`, `avaliacao_modelos`, `treinamento_pipeline`). Classes e métodos exclusivamente em português.
2. **Tipagem Strict sem `Any`:** Conformidade de 100% no `pyright --strict`, utilizando `Generic[T]`, `Protocol`, `TypeVar`, `override` e `final`.
3. **Padrão No-If no Domínio:** Nenhum `if motor == "pandas"` ou `if algoritmo == "kmeans"`. As fábricas operam via dicionários de registro (`dict[str, Callable]`), levantando exceções tipadas para chaves desconhecidas.
4. **Isolamento de Texto e Ausência de PLN:** Reviews textuais não entram na matriz de treino $X$. São retidas apenas na tabela Silver e metadados Gold para auditoria humana.
5. **Prevenção de Data Leakage:** O método `ajustar(X)` (fit) de qualquer transformador é invocado estritamente na etapa de treino.

---

## 4. Estrutura Física Planejada para a Fase 2

```text
app/
├── processamento_dados/
│   ├── __init__.py
│   ├── motor_pandas.py              # Implementação vetorizada com Pandas
│   ├── motor_polars.py              # Implementação vetorizada com Polars
│   ├── interpretador_dsl.py         # Avaliador seguro de AST/DSL para filtros e criação
│   └── fabrica_motores.py           # Registry/Factory para resolução do motor tabular
├── engenharia_atributos/
│   ├── __init__.py
│   ├── gerador_atributos.py         # Cálculo de colunas derivadas (horas, dias desde ref)
│   └── seletor_colunas.py           # Segregação de X de treino e metadados analíticos
├── preprocessamento_ml/
│   ├── __init__.py
│   ├── transformador_imputador.py    # Imputação com SimpleImputer (mediana/média)
│   ├── transformador_escalonador.py  # Escalonamento StandardScaler / RobustScaler
│   ├── redutor_dimensionalidade.py  # Redução opcional PCA / TruncatedSVD
│   ├── pipeline_composto.py         # Composite GoF encadeando etapas de transformação
│   └── fabrica_preprocessamento.py  # Registry/Factory de etapas a partir do YAML
├── agrupamento_modelos/
│   ├── __init__.py
│   ├── capacidades_algoritmo.py     # Catálogo tipado de capacidades (predict, centroides, ruído)
│   ├── agrupador_kmeans.py          # Adaptador scikit-learn para KMeans
│   ├── agrupador_dbscan.py          # Adaptador scikit-learn para DBSCAN
│   ├── agrupador_hdbscan.py         # Adaptador scikit-learn para HDBSCAN
│   └── fabrica_agrupadores.py       # Registry/Factory para instanciar algoritmos
├── avaliacao_modelos/
│   ├── __init__.py
│   ├── avaliador_clusters.py        # Silhouette, Davies-Bouldin, Calinski-Harabasz e ruído
│   └── metricas_estatisticas.py     # Distribuições, tamanhos de grupos e percentis
└── treinamento_pipeline/
    ├── __init__.py
    └── executor_treinamento.py      # Orquestrador do pipeline de treino e avaliação Gold
```

---

## 5. Critérios Mensuráveis de Aceite (Definition of Done)

1. **Paridade entre Motores:** A execução da mesma DSL de filtros e criação de atributos sobre o mesmo dataset produz resultados estatisticamente idênticos em Pandas e Polars.
2. **Segurança da DSL:** A DSL não utiliza `eval` ou `exec`. Operadores desconhecidos produzem erro de configuração tipado.
3. **Conformidade do Catálogo de Capacidades:** Cada algoritmo reporta suas capacidades reais (`KMeans.possui_centroides=True`, `DBSCAN.gera_ruido=True`, `DBSCAN.suporta_predicao_fora_da_amostra=False`).
4. **Isolamento de Matriz de Treino:** A matriz $X$ fornecida aos algoritmos não contém IDs (`steamid`, `recommendationid`), timestamps absolutos brutos ou texto de reviews.
5. **Qualidade do Código:** `pyright` executado em modo `strict` com **0 erros**, `ruff` sem violações e cobertura completa de testes unitários e de integração em `tests/`.
