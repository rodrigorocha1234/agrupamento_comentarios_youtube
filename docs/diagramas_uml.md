# Diagramas UML e Arquitetura do Sistema

Este documento reúne a modelagem visual canônica do projeto **YouTube Comments NLP & Trends Multiagente**, documentando os padrões de projeto consolidados (**Adapter**, **Factory**, **Strategy**, **Null Object**, **Protocols estruturais**, **Generics** e **TypeVar**).

---

## 1. Diagrama de Classes UML (Class Diagram)

O diagrama abaixo detalha o desacoplamento arquitetural entre as camadas de **Ingestão**, **Processamento Tabular/NLP**, **Agrupamento de Modelos**, **Estratégias de Tendências**, **Persistência Lakehouse** e **Visualização Operacional**:

```mermaid
classDiagram
    %% =========================================================================
    %% 1. FONTES DE DADOS E INGESTÃO (Adapter & Factory Pattern)
    %% =========================================================================
    class ProtocoloExtratorComentarios {
        <<Protocol>>
        +extrair_canal_completo(id_canal, dias_retroativos, incluir_respostas, limite_videos, tamanho_pagina) tuple[list~MetadadosVideo~, list~ComentarioColetado~]
        +obter_detalhes_canal(id_canal) tuple[str, str]
    }

    class FabricaFontesDados {
        <<Factory>>
        +_registro_extratores: dict
        +registrar_fonte(tipo, construtor)$ void
        +criar_extrator(config)$ ProtocoloExtratorComentarios
    }

    class ExtratorComentarios {
        <<Adapter>>
        -_cliente: ClienteYouTube
        +extrair_canal_completo(...)
        +obter_detalhes_canal(...)
    }

    class ExtratorArquivoLocal {
        <<Adapter>>
        -_caminho_dados: Path
        -_motor: MotorProcessamento
        -_coluna_texto: str
        -_coluna_id: str
        -_coluna_temporal: str
        +extrair_canal_completo(...)
        +obter_detalhes_canal(...)
    }

    class ClienteYouTube {
        -_chave_api: str
        -_servico: Resource
        +buscar_videos_recentes(...)
        +listar_comentarios_video(...)
    }

    ProtocoloExtratorComentarios <|.. ExtratorComentarios : implements
    ProtocoloExtratorComentarios <|.. ExtratorArquivoLocal : implements
    ExtratorComentarios --> ClienteYouTube : usa
    FabricaFontesDados ..> ProtocoloExtratorComentarios : instancia

    %% =========================================================================
    %% 2. MOTOR DE CLUSTERIZAÇÃO (Strategy, Factory, Generics & TypeVar)
    %% =========================================================================
    class FabricaAgrupadores {
        <<Factory>>
        +criar_kmeans(n_clusters, random_state, k_automatico, ...)$ AgrupadorKMeans
        +criar_dbscan(eps, min_samples, metric, ...)$ AgrupadorDBSCAN
        +criar_hdbscan(min_cluster_size, min_samples, metric, ...)$ AgrupadorHDBSCAN
    }

    class AgrupadorKMeans {
        <<Strategy>>
        -_k_automatico: bool
        -_k_otimo: int
        -_modelo: KMeans
        -_rotulos: list~int~
        -_historico_k: dict~int, float~
        +labels_: np.ndarray
        +ajustar_e_agrupar(matriz) tuple[list~int~, MetricasAgrupamento]
        +obter_rotulos() list~int~
        +obter_centroides() np.ndarray
        +obter_modelo() KMeans
    }

    class AgrupadorDBSCAN {
        <<Strategy>>
        -_eps: float
        -_min_samples: int
        -_metric: str
        -_modelo: DBSCAN
        +ajustar_e_agrupar(matriz) tuple[list~int~, MetricasAgrupamento]
        +obter_modelo() DBSCAN
    }

    class AgrupadorHDBSCAN {
        <<Strategy>>
        -_min_cluster_size: int
        -_min_samples: int
        -_modelo: HDBSCAN
        +ajustar_e_agrupar(matriz) tuple[list~int~, MetricasAgrupamento]
        +obter_probabilidades() np.ndarray
        +obter_modelo() HDBSCAN
    }

    class AgrupadorTabular~TModelo~ {
        <<Generic Class>>
        -_agrupadores: dict~str, Any~
        -_estrategia: EstrategiaAnaliseClusters
        +ajustar(matriz_ou_df) ResultadoAgrupamentoTabular~TModelo~
        +analisar_distribuicao_clusters(...) list~ResultadoAnaliseCluster~
    }

    FabricaAgrupadores ..> AgrupadorKMeans : cria
    FabricaAgrupadores ..> AgrupadorDBSCAN : cria
    FabricaAgrupadores ..> AgrupadorHDBSCAN : cria
    AgrupadorTabular o-- AgrupadorKMeans : compõe
    AgrupadorTabular o-- AgrupadorDBSCAN : compõe
    AgrupadorTabular o-- AgrupadorHDBSCAN : compõe

    %% =========================================================================
    %% 3. ESTRATÉGIAS DE ANÁLISE DE TENDÊNCIAS (Strategy & Generics)
    %% =========================================================================
    class EstrategiaAnaliseClusters~TId~ {
        <<Protocol Generic>>
        +eh_temporal() bool
        +analisar_grupos(grupos_atuais, grupos_anteriores) list~ResultadoAnaliseCluster~TId~~
    }

    class EstrategiaAnaliseTemporal {
        <<Strategy>>
        -_detector: DetectorVariacao
        +eh_temporal() bool
        +analisar_grupos(...) list~ResultadoAnaliseCluster~str~~
    }

    class EstrategiaAnaliseEstatica {
        <<Strategy>>
        -_minimo_amostras: int
        +eh_temporal() bool
        +analisar_grupos(...) list~ResultadoAnaliseCluster~str~~
    }

    EstrategiaAnaliseClusters <|.. EstrategiaAnaliseTemporal : implements
    EstrategiaAnaliseClusters <|.. EstrategiaAnaliseEstatica : implements
    AgrupadorTabular --> EstrategiaAnaliseClusters : delega

    %% =========================================================================
    %% 4. CAMADAS DO DATA LAKEHOUSE (Repository / Persistence Pattern)
    %% =========================================================================
    class ProtocoloCamadaBronze {
        <<Protocol>>
        +gravar_lote_comentarios(id_canal, id_video, comentarios) str
    }

    class ProtocoloCamadaPrata {
        <<Protocol>>
        +gravar_snapshot_comentarios(id_canal, id_video, novos_comentarios) str
        +ler_comentarios_video(id_canal, id_video) list~ComentarioColetado~
    }

    class ProtocoloCamadaOuro {
        <<Protocol>>
        +gravar_topicos_ouro(id_canal, id_video, tecnica, data_referencia, registros) str
        +ler_topicos_ouro(id_canal, id_video, tecnica, data_referencia) list~RegistroTopicoOuro~
    }

    class CamadaBronze {
        -_storage: ClienteStorageS3
        +gravar_lote_comentarios(...)
    }

    class CamadaPrata {
        -_storage: ClienteStorageS3
        +gravar_snapshot_comentarios(...)
        +ler_comentarios_video(...)
    }

    class CamadaOuro {
        -_storage: ClienteStorageS3
        +gravar_topicos_ouro(...)
        +ler_topicos_ouro(...)
    }

    class ClienteStorageS3 {
        -_cliente_s3: boto3.client
        -_bucket: str
        +enviar_bytes(chave, dados, content_type)
        +baixar_bytes(chave) bytes
        +listar_chaves(prefixo) list~str~
    }

    ProtocoloCamadaBronze <|.. CamadaBronze : implements
    ProtocoloCamadaPrata <|.. CamadaPrata : implements
    ProtocoloCamadaOuro <|.. CamadaOuro : implements
    CamadaBronze --> ClienteStorageS3 : usa
    CamadaPrata --> ClienteStorageS3 : usa
    CamadaOuro --> ClienteStorageS3 : usa

    %% =========================================================================
    %% 5. PROVEDORES DE VISUALIZAÇÃO & OBSERVABILIDADE (Adapter, Factory & Null Object)
    %% =========================================================================
    class ProtocoloProvedorVisualizacao {
        <<Protocol>>
        +tipo_provedor: TipoProvedorVisualizacao
        +url_base: str
        +verificar_disponibilidade(timeout_segundos) bool
        +obter_url_dashboard(identificador) str
        +listar_dashboards() list~dict~
        +obter_metadados_painel(identificador) dict
    }

    class FabricaProvedorVisualizacao {
        <<Factory>>
        +_registro_provedores: dict
        +registrar_provedor(tipo, fabrica)$ void
        +criar_provedor(config)$ ProtocoloProvedorVisualizacao
    }

    class ProvedorVisualizacaoGrafana {
        <<Adapter>>
        +DASHBOARDS_CONHECIDOS: dict
        -_url_base: str
        +verificar_disponibilidade(...) bool
        +obter_url_dashboard(...) str
        +listar_dashboards(...) list~dict~
    }

    class ProvedorVisualizacaoNulo {
        <<NullObject>>
        -_url_base: str
        +verificar_disponibilidade(...) bool
        +obter_url_dashboard(...) str
        +listar_dashboards(...) list~dict~
    }

    ProtocoloProvedorVisualizacao <|.. ProvedorVisualizacaoGrafana : implements
    ProtocoloProvedorVisualizacao <|.. ProvedorVisualizacaoNulo : implements
    FabricaProvedorVisualizacao ..> ProtocoloProvedorVisualizacao : instancia

    %% =========================================================================
    %% 6. ORQUESTRAÇÃO CENTRAL (Mediator / Facade Pattern)
    %% =========================================================================
    class ExecutorCiclo {
        <<Facade>>
        -_extrator: ProtocoloExtratorComentarios
        -_bronze: ProtocoloCamadaBronze
        -_prata: ProtocoloCamadaPrata
        -_ouro: ProtocoloCamadaOuro
        -_vetorizador: VetorizadorTfidf
        -_agrupador_kmeans: AgrupadorKMeans
        -_calculador_tendencias: CalculadorTendencias
        -_integrador_mlflow: IntegradorMLflow
        +executar_ciclo_canal(id_canal) dict~str, int~
    }

    ExecutorCiclo --> ProtocoloExtratorComentarios : extrai
    ExecutorCiclo --> ProtocoloCamadaBronze : persiste
    ExecutorCiclo --> ProtocoloCamadaPrata : deduplica
    ExecutorCiclo --> ProtocoloCamadaOuro : consolida
    ExecutorCiclo --> AgrupadorKMeans : executa
```

---

## 2. Diagrama de Atividades com Raias (Swimlane Activity Diagram)

O diagrama abaixo detalha o fluxo completo de atividades do sistema, organizado em **7 raias (swimlanes)** que delimitam com precisão as responsabilidades de cada subsistema:

```mermaid
flowchart TD
    %% =========================================================================
    %% DIAGRAMA DE ATIVIDADES COM RAIAS (SWIMLANES)
    %% =========================================================================
    
    subgraph Raia1["1. Agendador / CLI (Disparo & Configuração)"]
        node_start([● Início do Ciclo])
        node_conf["Carregar configurações (entradas.yaml)"]
        node_disp["Disparar execução do canal (./executar_ciclo.sh)"]
        node_fim([◉ Fim do Ciclo])
    end

    subgraph Raia2["2. Orquestrador (ExecutorCiclo)"]
        node_init["Instanciar componentes via Injeção de Dependências"]
        node_coord_ing["Solicitar extração de dados à fábrica"]
        node_coord_bro["Enviar lote bruto para gravação"]
        node_coord_pra["Comandar deduplicação e snapshot colunar"]
        node_coord_nlp["Acionar pipeline de tratamento e vetorização"]
        node_coord_clu["Disparar busca e ajuste de agrupamento"]
        node_coord_ten["Solicitar apuração de tendências temporais"]
        node_coord_our["Publicar partição analítica diária"]
        node_coord_mlf["Registrar parâmetros, métricas e artefatos"]
        node_coord_obs["Atualizar contadores e verificar telemetria"]
    end

    subgraph Raia3["3. Ingestão de Dados (FabricaFontes & Extratores)"]
        node_res_fonte{"Tipo de Fonte?"}
        node_col_yt["Coletar vídeos e comentários recursivos (YouTube API v3)"]
        node_col_loc["Ler e normalizar arquivo local (CSV / Parquet / JSONL)"]
        node_ret_ext["Retornar MetadadosVideo e ComentarioColetado"]
    end

    subgraph Raia4["4. Data Lakehouse S3/RustFS (Armazenamento em Camadas)"]
        node_s3_bro["Camada Bronze: Gravar lote bruto particionado (.jsonl)"]
        node_s3_pra["Camada Prata: Deduplicar por id_comentario e gravar (.parquet)"]
        node_s3_our["Camada Ouro: Gravar topicos analiticos particionados data=AAAA-MM-DD (.parquet)"]
    end

    subgraph Raia5["5. Motor de NLP & Vetorização (spaCy & TF-IDF)"]
        node_nlp_limp["Limpar texto preservando termos de negação"]
        node_nlp_lema["Lematizar com POS Tagging (NOUN, ADJ, PROPN)"]
        node_nlp_vet["Gerar matriz esparsa TF-IDF normalizada L2"]
    end

    subgraph Raia6["6. Motor de Agrupamento & Tendências (ML & Métricas)"]
        node_clu_busca["Varrer k_min a k_max ajustando KMeans / DBSCAN / HDBSCAN"]
        node_clu_eval["Avaliar Silhouette Score, Davies-Bouldin e Calinski-Harabasz"]
        node_clu_best["Selecionar k ótimo e extrair rótulos e centróides"]
        node_ten_rot["Rotular tópicos com lema canônico (c-TF-IDF)"]
        node_ten_delta["Calcular variação percentual Δ% vs dia anterior (T-1)"]
        node_ten_class{"Classificar Status"}
        node_ten_novo["Status: Novo (+100.0%)"]
        node_ten_cresc["Status: Crescendo (Δ% > 0)"]
        node_ten_decresc["Status: Decrescendo (Δ% < 0)"]
        node_ten_estavel["Status: Estável (Δ% = 0)"]
    end

    subgraph Raia7["7. Serving & Observabilidade (FastAPI, MLflow, Prometheus & Grafana)"]
        node_mlf_reg["MLflow: Log de experimento, hiperparâmetros e modelo serializado"]
        node_prom_exp["Prometheus: Incrementar contadores e atualizar gauges de latência e storage"]
        node_graf_dash["Grafana: Atualizar painéis declarativos (Lakehouse, API, Pipelines)"]
        node_api_serv["FastAPI: Disponibilizar tópicos e séries temporais em rotas REST"]
    end

    %% Transições entre raias
    node_start --> node_conf --> node_disp --> node_init
    node_init --> node_coord_ing --> node_res_fonte
    node_res_fonte -->|youtube| node_col_yt --> node_ret_ext
    node_res_fonte -->|csv / parquet / jsonl| node_col_loc --> node_ret_ext
    node_ret_ext --> node_coord_bro --> node_s3_bro
    node_s3_bro --> node_coord_pra --> node_s3_pra
    node_s3_pra --> node_coord_nlp --> node_nlp_limp --> node_nlp_lema --> node_nlp_vet
    node_nlp_vet --> node_coord_clu --> node_clu_busca --> node_clu_eval --> node_clu_best
    node_clu_best --> node_coord_ten --> node_ten_rot --> node_ten_delta --> node_ten_class
    node_ten_class -->|Sem histórico| node_ten_novo
    node_ten_class -->|Volume subiu| node_ten_cresc
    node_ten_class -->|Volume caiu| node_ten_decresc
    node_ten_class -->|Volume igual| node_ten_estavel
    node_ten_novo & node_ten_cresc & node_ten_decresc & node_ten_estavel --> node_coord_our
    node_coord_our --> node_s3_our
    node_s3_our --> node_coord_mlf --> node_mlf_reg
    node_s3_our --> node_coord_obs --> node_prom_exp --> node_graf_dash
    node_s3_our --> node_api_serv
    node_mlf_reg & node_graf_dash & node_api_serv --> node_fim
```

---

## 3. Diagrama de Sequência UML (Sequence Diagram)

O diagrama abaixo ilustra a execução síncrona e orquestrada de uma rodada completa de ingestão e processamento analítico disparada por `ExecutorCiclo.executar_ciclo_canal(id_canal)`:

```mermaid
sequenceDiagram
    autonumber
    actor Scheduler as Agendador / CLI
    participant Exec as ExecutorCiclo
    participant FabFonte as FabricaFontesDados
    participant Extrator as Extrator (YouTube / Local)
    participant Bronze as Camada Bronze S3
    participant Prata as Camada Prata S3
    participant Vetor as VetorizadorTfidf / spaCy
    participant Cluster as Agrupador (KMeans / DBSCAN)
    participant Tend as CalculadorTendencias
    participant Ouro as Camada Ouro S3
    participant MLflow as IntegradorMLflow
    participant Obs as FabricaProvedorVisualizacao

    Scheduler->>Exec: executar_ciclo_canal(id_canal)
    
    %% Ingestão
    Exec->>FabFonte: criar_extrator(config)
    FabFonte-->>Exec: extrator: ProtocoloExtratorComentarios
    Exec->>Extrator: extrair_canal_completo(id_canal, dias_retroativos)
    Extrator-->>Exec: videos: list[MetadadosVideo], comentarios: list[ComentarioColetado]
    
    %% Camada Bronze
    loop Para cada vídeo coletado
        Exec->>Bronze: gravar_lote_comentarios(id_canal, id_video, comentarios)
        Bronze-->>Exec: chave_s3_bronze_jsonl
    end
    
    %% Camada Prata (Deduplicação & Snapshot Parquet)
    loop Para cada vídeo coletado
        Exec->>Prata: gravar_snapshot_comentarios(id_canal, id_video, novos_comentarios)
        Prata-->>Exec: chave_s3_prata_parquet
        Exec->>Prata: ler_comentarios_video(id_canal, id_video)
        Prata-->>Exec: todos_comentarios: list[ComentarioColetado]
        
        %% Vetorização & NLP
        Exec->>Vetor: transformar(textos_lematizados)
        Vetor-->>Exec: matriz_esparsa_csr (normalizada L2)
        
        %% Clusterização Comparativa
        Exec->>Cluster: ajustar_e_agrupar(matriz_esparsa_csr)
        Note over Cluster: Busca autônoma de k ótimo<br/>maximizando Silhouette Score
        Cluster-->>Exec: rotulos: list[int], metricas: MetricasAgrupamento
        
        %% Tendências Temporais e Ouro
        Exec->>Tend: calcular_tendencias_video(comentarios, rotulos, data_referencia)
        Tend-->>Exec: registros_ouro: list[RegistroTopicoOuro]
        Exec->>Ouro: gravar_topicos_ouro(id_canal, id_video, tecnica, data, registros_ouro)
        Ouro-->>Exec: chave_s3_ouro_parquet
    end
    
    %% MLOps Tracking & Observabilidade
    Exec->>MLflow: registrar_execucao(metricas, parametros, modelo_kmeans)
    MLflow-->>Exec: run_id_mlflow
    
    Exec->>Obs: criar_provedor(config)
    Obs-->>Exec: provedor: ProtocoloProvedorVisualizacao
    Exec->>Obs: verificar_disponibilidade()
    
    Exec-->>Scheduler: resumo_execucao: dict[str, int]
```

---

## 3. Diagrama de Componentes UML (Component Diagram)

O diagrama abaixo apresenta os componentes estruturais do sistema, detalhando a comunicação entre containers, portas de rede e protocolos de comunicação:

```mermaid
flowchart TD
    subgraph IngestaoComponent["Componente de Ingestão de Dados"]
        ConfigYAML["config/entradas.yaml"] --> ProvedorConfig["ProvedorConfiguracao"]
        ProvedorConfig --> FabricaFontes["FabricaFontesDados"]
        FabricaFontes -->|fonte: youtube| ExtratorYT["ExtratorComentarios (YouTube API v3)"]
        FabricaFontes -->|fonte: csv/parquet/jsonl| ExtratorLocal["ExtratorArquivoLocal (Adapter)"]
    end

    subgraph LakehouseComponent["Componente Data Lakehouse S3 (RustFS :9000)"]
        Bronze["Camada Bronze (JSONL Bruto)"]
        Prata["Camada Prata (Deduplicação Parquet)"]
        Ouro["Camada Ouro (Série Temporal Diária Parquet)"]
        Bronze -->|Deduplicação| Prata
        Prata -->|Enriquecimento Analítico| Ouro
    end

    subgraph NLPMLComponent["Componente NLP & Machine Learning"]
        Limpador["LimpadorTexto (pt-BR)"]
        Vetorizador["VetorizadorTfidf / BERTimbau"]
        Redutor["RedutorUmap (768d -> 5d)"]
        KMeansComp["KMeans (Auto-k por Silhueta)"]
        DBSCANComp["DBSCAN (Métrica Cosseno)"]
        HDBSCANComp["HDBSCAN (Probabilidades)"]
        TendenciasComp["DetectorVariacao (Δ% Temporal)"]
        Limpador --> Vetorizador --> Redutor --> KMeansComp & DBSCANComp & HDBSCANComp --> TendenciasComp
    end

    subgraph ServingComponent["Componente Serving & Consumo"]
        FastAPI["FastAPI App (:8000)"]
        MLflowServer["MLflow Tracking & Registry (:5000)"]
    end

    subgraph ObservabilidadeComponent["Componente de Observabilidade & Telemetria"]
        Prometheus["Prometheus Server (:9090)"]
        Grafana["Grafana Dashboards (:3000)"]
        Loki["Grafana Loki (:3100)"]
        Alloy["Grafana Alloy (:12345)"]
        ProvedorGrafana["ProvedorVisualizacaoGrafana (Adapter)"]
    end

    IngestaoComponent -->|Gravação Streaming| Bronze
    Prata --> NLPMLComponent
    TendenciasComp -->|Persistência Diária| Ouro
    KMeansComp -->|Registro de Modelo| MLflowServer
    Ouro -->|Consumo Analítico| FastAPI
    FastAPI -->|Métricas HTTP| Prometheus
    LakehouseComponent -->|Métricas de I/O e Storage| Prometheus
    Prometheus --> Grafana
    Alloy -->|Logs Estruturados| Loki
    ProvedorGrafana -->|Consulta de Health & UIDs| Grafana
```

---

## 4. Diagrama de Estados UML (State Machine Diagram)

### 4.1 Ciclo de Vida do Comentário no Lakehouse

```mermaid
stateDiagram-v2
    [*] --> IngestaoPendente: Recebido da Fonte (YouTube / Arquivo Local)
    IngestaoPendente --> GravadoBronze: Validado e Gravado no S3 (.jsonl)
    GravadoBronze --> DeduplicadoPrata: Normalizado e Deduplicado por id_comentario (.parquet)
    DeduplicadoPrata --> Vetorizado: Limpeza textual + Lematização spaCy + TF-IDF/BERTimbau
    Vetorizado --> Clusterizado: Associado a um Cluster (KMeans / DBSCAN / HDBSCAN)
    Clusterizado --> PublicadoOuro: Atribuído a Lema de Tópico Canônico e Série Temporal Diária (.parquet)
    PublicadoOuro --> ServidoAPI: Disponível para Consulta no Endpoint FastAPI
    ServidoAPI --> [*]
```

### 4.2 Máquina de Estados de Classificação de Tendências Temporais

```mermaid
stateDiagram-v2
    [*] --> SemDadosAnteriores: Tópico sem ocorrências no dia anterior (T-1)
    SemDadosAnteriores --> Novo: Volume atual >= 1 no dia de referência (T0) [+100.0%]
    
    [*] --> ComDadosAnteriores: Tópico com baseline histórico apurado em T-1
    ComDadosAnteriores --> Crescendo: Volume em T0 > Volume em T-1 (Δ% positivo)
    ComDadosAnteriores --> Decrescendo: Volume em T0 < Volume em T-1 (Δ% negativo)
    ComDadosAnteriores --> Estavel: Volume em T0 == Volume em T-1 (Δ% = 0.0%)
    ComDadosAnteriores --> SemDados: Volume zerado em ambas as janelas
    
    Novo --> [*]
    Crescendo --> [*]
    Decrescendo --> [*]
    Estavel --> [*]
    SemDados --> [*]
```

---

## 5. Resumo dos Padrões de Projeto Aplicados

| Padrão de Projeto | Tipo GoF | Classes Envolvidas | Propósito no Projeto |
| :--- | :--- | :--- | :--- |
| **Adapter** | Estrutural | `ExtratorArquivoLocal`, `ExtratorComentarios` | Adapta diferentes fontes de dados (YouTube API, CSV, Parquet, JSONL) ao contrato canônico `ProtocoloExtratorComentarios`. |
| **Adapter** | Estrutural | `ProvedorVisualizacaoGrafana` | Isola consultas, UIDs e rotas do Grafana sob o contrato `ProtocoloProvedorVisualizacao`. |
| **Factory** | Criacional | `FabricaFontesDados` | Instancia polimorficamente o extrator correto com base no YAML (`coleta.fonte`). |
| **Factory** | Criacional | `FabricaAgrupadores` | Centraliza a construção parametrizada dos modelos KMeans, DBSCAN e HDBSCAN. |
| **Factory** | Criacional | `FabricaProvedorVisualizacao` | Instancia o provedor de dashboards (`grafana`, `nenhum` ou `custom`) com suporte a registro dinâmico. |
| **Strategy** | Comportamental | `AgrupadorKMeans`, `AgrupadorDBSCAN`, `AgrupadorHDBSCAN` | Alterna algoritmos de agrupamento matematicamente distintos de forma intercambiável. |
| **Strategy** | Comportamental | `EstrategiaAnaliseTemporal`, `EstrategiaAnaliseEstatica` | Separa a lógica de detecção de tendências temporais ($\Delta\%$) de problemas cross-section tabulares puros. |
| **Null Object** | Comportamental | `ProvedorVisualizacaoNulo` | Evita checagens de `None` e falhas quando a visualização estiver desabilitada. |
| **Facade** | Estrutural | `ExecutorCiclo` | Simplifica a orquestração de coleta, Lakehouse S3, NLP, clusterização, tendências e MLflow em um único método. |
