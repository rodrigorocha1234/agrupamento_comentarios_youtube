"""Modelos tipados estritos para representação das configurações do sistema."""

from dataclasses import dataclass, field

from app.configuracao_geral.tipos_enumerados import (
    AlgoritmoVizinhos,
    DispositivoExecucao,
    GranularidadeTendencia,
    InicializacaoKMeans,
    MetricaDistancia,
    MetodoSelecaoCluster,
    MotorProcessamento,
    NormaVetorizacao,
    PeriodicidadeColeta,
    TecnicaReducao,
    TecnicaRepresentacao,
    TipoFonteDados,
    TipoPersistencia,
    TipoProvedorVisualizacao,
)


@dataclass(frozen=True, slots=True)
class ConfiguracaoProjeto:
    """Configurações de identificação do projeto."""

    nome: str
    idioma: str


@dataclass(frozen=True, slots=True)
class CanalConfigurado:
    """Definição de um canal monitorado."""

    id_canal: str
    ativo: bool


@dataclass(frozen=True, slots=True)
class ConfiguracaoColeta:
    """Parâmetros da coleta incremental ou ingestão de fontes de dados."""

    habilitada: bool = False
    fonte: TipoFonteDados = TipoFonteDados.YOUTUBE
    periodicidade: PeriodicidadeColeta = PeriodicidadeColeta.DIARIA
    canais: list[CanalConfigurado] = field(default_factory=list[CanalConfigurado])
    dias_publicacao_atras: int = 7
    incluir_respostas: bool = True
    tamanho_pagina: int = 100
    limite_videos_por_canal: int | None = None
    tentativas: int = 4
    atraso_base_segundos: float = 2.0
    chave_api_env: str = "YOUTUBE_API_KEY"
    caminho_dados: str | None = None
    coluna_texto: str = "texto"
    coluna_id: str = "id"
    coluna_temporal: str | None = None



@dataclass(frozen=True, slots=True)
class ConfiguracaoStopwords:
    """Parâmetros de controle de stopwords e negações."""

    usar_spacy: bool
    adicionais: list[str] = field(default_factory=list[str])
    preservar: list[str] = field(default_factory=list[str])
    filtro_centroides: list[str] = field(default_factory=list[str])


@dataclass(frozen=True, slots=True)
class ConfiguracaoRepresentacao:
    """Parâmetros da representação vetorial (TF-IDF, spaCy ou Sentence-Transformers/BERTimbau)."""

    tecnica: TecnicaRepresentacao
    min_df: int
    max_df: float
    ngram_range: tuple[int, int]
    sublinear_tf: bool = True
    norma: NormaVetorizacao = NormaVetorizacao.L2
    modelo_transformers: str = "neuralmind/bert-base-portuguese-cased"
    dispositivo_transformers: DispositivoExecucao = DispositivoExecucao.CPU
    batch_size_transformers: int = 32


@dataclass(frozen=True, slots=True)
class ConfiguracaoReducao:
    """Parâmetros da redução dimensionalidade."""

    ativa: bool
    tecnica: TecnicaReducao
    componentes: int
    n_vizinhos: int = 15
    distancia_minima: float = 0.0
    metrica: MetricaDistancia = MetricaDistancia.COSINE
    random_state: int = 42



@dataclass(frozen=True, slots=True)
class ParametrosKMeans:
    """Parâmetros do algoritmo KMeans com suporte a busca automática de k ótimo."""

    n_clusters: int
    random_state: int
    n_init: int
    init: InicializacaoKMeans = InicializacaoKMeans.KMEANS_PLUS_PLUS
    k_automatico: bool = True
    k_min: int = 2
    k_max: int = 10
    max_iter: int = 300


@dataclass(frozen=True, slots=True)
class ParametrosDBSCAN:
    """Parâmetros do algoritmo DBSCAN."""

    eps: float
    min_samples: int
    metric: MetricaDistancia
    algorithm: AlgoritmoVizinhos = AlgoritmoVizinhos.AUTO


@dataclass(frozen=True, slots=True)
class ParametrosHDBSCAN:
    """Parâmetros do algoritmo HDBSCAN."""

    min_cluster_size: int
    min_samples: int
    metric: MetricaDistancia
    cluster_selection_method: MetodoSelecaoCluster = MetodoSelecaoCluster.EOM



@dataclass(frozen=True, slots=True)
class ConfiguracaoTecnicas:
    """Parâmetros de cada técnica de clusterização suportada."""

    kmeans_ativo: bool
    kmeans_parametros: ParametrosKMeans
    dbscan_ativo: bool
    dbscan_parametros: ParametrosDBSCAN
    hdbscan_ativo: bool
    hdbscan_parametros: ParametrosHDBSCAN


@dataclass(frozen=True, slots=True)
class ConfiguracaoProcessamento:
    """Agrupamento de parâmetros de agrupamento, redução e NLP."""

    reducao: ConfiguracaoReducao
    tecnicas: ConfiguracaoTecnicas
    spacy_modelo: str = "pt_core_news_sm"
    stopwords: ConfiguracaoStopwords = field(default_factory=lambda: ConfiguracaoStopwords(usar_spacy=False))
    representacao: ConfiguracaoRepresentacao = field(
        default_factory=lambda: ConfiguracaoRepresentacao(
            tecnica=TecnicaRepresentacao.TFIDF,
            min_df=1,
            max_df=1.0,
            ngram_range=(1, 1),
        )
    )
    motor_dados: MotorProcessamento = MotorProcessamento.POLARS
    usar_nlp: bool = False
    eh_temporal: bool = True


@dataclass(frozen=True, slots=True)
class ConfiguracaoTopicos:
    """Critérios de extração e rotulagem de tópicos não-LLM."""

    pos_permitidas: list[str] = field(default_factory=lambda: ["NOUN", "PROPN", "ADJ"])
    comprimento_minimo: int = 3
    peso_tfidf: float = 0.7
    peso_frequencia: float = 0.3
    penalizacao_global: bool = True
    limiar_penalizacao_global: float = 0.75
    fator_penalidade: float = 0.2
    rotulo_ruido_padrao: str = "sem_topico"


@dataclass(frozen=True, slots=True)
class ConfiguracaoTendencias:
    """Critérios de cálculo de crescimento e decrescimento temporal."""

    ativa: bool = True
    minimo_comentarios: int = 5
    crescimento_minimo_proporcao: float = 0.10
    queda_minima_proporcao: float = 0.10
    janela_dias: int = 1
    max_amostras_video: int = 0
    max_amostras_canal: int = 0
    granularidade: GranularidadeTendencia = GranularidadeTendencia.DIARIA




@dataclass(frozen=True, slots=True)
class ConfiguracaoPersistencia:
    """Parâmetros de conexão com o lakehouse S3/MinIO e modelos de chave."""

    tipo: TipoPersistencia
    bucket: str
    prefixo_bronze: str
    prefixo_prata: str
    prefixo_ouro: str
    endpoint_env: str
    access_key_env: str
    secret_key_env: str
    caminho_bronze: str = ""
    caminho_prata: str = ""
    caminho_ouro: str = ""
    padrao_chave_bronze: str = (
        "{prefixo}/id_canal={id_canal}/id_video={id_video}/data_coleta={data_coleta}/lote={id_lote}.jsonl"
    )
    padrao_chave_prata: str = (
        "{prefixo}/id_canal={id_canal}/id_video={id_video}/versao={timestamp_versao}/comentarios.parquet"
    )
    padrao_chave_ouro_video: str = (
        "{prefixo}/id_canal={id_canal}/id_video={id_video}/tecnica={tecnica}/data={data_referencia}/topicos.parquet"
    )
    padrao_chave_ouro_consolidado: str = (
        "{prefixo}/id_canal={id_canal}/consolidado/tecnica={tecnica}/data={data_referencia}/topicos.parquet"
    )


@dataclass(frozen=True, slots=True)
class ConfiguracaoMLflow:
    """Parâmetros de rastreamento e serving do MLflow."""

    tracking_uri_env: str
    serving_url_env: str


@dataclass(frozen=True, slots=True)
class ConfiguracaoAPI:
    """Parâmetros do servidor HTTP FastAPI."""

    porta: int
    tempo_limite_segundos: float
    cors_origens: list[str] = field(default_factory=lambda: ["*"])
    top_termos_padrao: int = 5
    tamanho_pagina_padrao: int = 10
    tamanho_pagina_maximo: int = 100


@dataclass(frozen=True, slots=True)
class ConfiguracaoObservabilidade:
    """Parâmetros de exportação e coleta de métricas."""

    prometheus: bool
    grafana: bool
    labels_alta_cardinalidade: bool
    provedor_visualizacao: TipoProvedorVisualizacao = TipoProvedorVisualizacao.GRAFANA
    url_visualizacao: str = "http://localhost:3000"


@dataclass(frozen=True, slots=True)
class ConfiguracaoGlobal:
    """Contêiner global fortemente tipado contendo todas as configurações."""

    projeto: ConfiguracaoProjeto
    coleta: ConfiguracaoColeta
    processamento: ConfiguracaoProcessamento
    topicos: ConfiguracaoTopicos
    tendencias: ConfiguracaoTendencias
    persistencia: ConfiguracaoPersistencia
    mlflow: ConfiguracaoMLflow
    api: ConfiguracaoAPI
    observabilidade: ConfiguracaoObservabilidade
