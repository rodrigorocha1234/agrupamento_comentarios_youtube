"""Modelos Pydantic fortemente tipados para validação declarativa de configurações."""

from pydantic import BaseModel, ConfigDict


class ModeloBaseConfiguracao(BaseModel):
    """Modelo base imutável com proibição estrita de campos desconhecidos."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class MetadadosProjeto(ModeloBaseConfiguracao):
    """Identificação e versão do schema do projeto."""

    versao_schema: str
    nome_projeto: str


class FuncionalidadesAtivas(ModeloBaseConfiguracao):
    """Flags de funcionalidades globais do projeto."""

    processamento_linguagem_natural: bool = False
    analise_temporal: bool = False


class ProcessamentoGeral(ModeloBaseConfiguracao):
    """Definição do motor tabular principal."""

    motor: str = "pandas"


class MachineLearningGeral(ModeloBaseConfiguracao):
    """Framework e algoritmo base."""

    framework: str = "sklearn"
    algoritmo: str = "kmeans"


class ConfiguracaoProjeto(ModeloBaseConfiguracao):
    """Mapeamento completo do arquivo projeto.yaml."""

    configuracao: MetadadosProjeto
    funcionalidades: FuncionalidadesAtivas
    processamento: ProcessamentoGeral
    machine_learning: MachineLearningGeral


class JogoSteam(ModeloBaseConfiguracao):
    """Definição de jogo a ser coletado."""

    appid: int


class ParametrosRequisicaoSteam(ModeloBaseConfiguracao):
    """Parâmetros oficiais do serviço IUserReviewsService/GetAppReviews/v1."""

    key_env: str | None = None
    filter: str = "recent"
    languages: tuple[str, ...] = ("brazilian",)
    day_range: int = 30
    cursor: str = "*"
    review_type: str = "all"
    purchase_type: str = "all"
    num_per_page: int = 100
    filter_offtopic_activity: bool = True
    display_language: str = "brazilian"
    use_review_quality: bool = True
    date_range_start: int | None = None
    date_range_end: int | None = None
    date_range_exclude: bool = False
    playtime_min_hours: int | None = None
    playtime_max_hours: int | None = None
    primarily_steam_deck: bool | None = None
    hardware_os: str | None = None
    hardware_cpu: str | None = None
    hardware_gpu: str | None = None
    hardware_device_type: str | None = None


class ModosColetaSteam(ModeloBaseConfiguracao):
    """Estratégias de cobertura da coleta."""

    historica: bool = True
    recente: bool = True
    atualizada: bool = True
    reconciliacao_periodica: bool = True


class ResilienciaColetaSteam(ModeloBaseConfiguracao):
    """Parâmetros de retry e tolerância da API."""

    max_tentativas: int = 5
    timeout_segundos: int = 30
    concorrencia_maxima: int = 1


class DetalhesSteam(ModeloBaseConfiguracao):
    """Mapeamento do bloco steam no YAML de fontes."""

    periodicidade: str = "diaria"
    jogos: tuple[JogoSteam, ...]
    endpoint: str = "IUserReviewsService/GetAppReviews/v1"
    parametros: ParametrosRequisicaoSteam
    modos_coleta: ModosColetaSteam
    resiliencia: ResilienciaColetaSteam


class ConfiguracaoSteamApi(ModeloBaseConfiguracao):
    """Mapeamento do arquivo steam_api.yaml."""

    steam: DetalhesSteam


class ConexaoSqlite(ModeloBaseConfiguracao):
    """Parâmetros específicos de conexão com SQLite."""

    caminho: str
    modo_journal: str = "WAL"
    timeout_segundos: int = 30


class ConexaoPostgres(ModeloBaseConfiguracao):
    """Parâmetros de conexão com PostgreSQL."""

    url_env: str = "STAGING_POSTGRES_DSN"


class ConexoesStaging(ModeloBaseConfiguracao):
    """Opções de conexão suportadas."""

    sqlite: ConexaoSqlite
    postgres: ConexaoPostgres


class DetalhesStaging(ModeloBaseConfiguracao):
    """Definições operacionais do banco de staging."""

    ativado: bool = True
    tecnologia: str = "sqlite"
    estrategia_escrita: str = "upsert_versionado"
    conexao: ConexoesStaging
    lote_registros: int = 500
    preservar_historico: bool = True
    usar_outbox: bool = True
    retencao_dias: int = 90


class ConfiguracaoStaging(ModeloBaseConfiguracao):
    """Mapeamento do arquivo staging.yaml."""

    staging: DetalhesStaging


class CamadaBronzeConfiguracao(ModeloBaseConfiguracao):
    """Configuração da camada Bronze."""

    prefixo: str
    formato: str = "json"
    imutavel: bool = True


class CamadaSilverConfiguracao(ModeloBaseConfiguracao):
    """Configuração da camada Silver."""

    prefixo: str
    formato: str = "parquet"
    reconciliar_historico: bool = True


class CamadaGoldConfiguracao(ModeloBaseConfiguracao):
    """Configuração da camada Gold."""

    prefixo: str
    formato: str = "parquet"


class CamadasDatalake(ModeloBaseConfiguracao):
    """Conjunto de camadas do Lakehouse."""

    bronze: CamadaBronzeConfiguracao
    silver: CamadaSilverConfiguracao
    gold: CamadaGoldConfiguracao


class DetalhesDatalake(ModeloBaseConfiguracao):
    """Mapeamento do bloco datalake."""

    ativado: bool = True
    armazenamento: str = "s3"
    endpoint_url_env: str = "S3_ENDPOINT_URL"
    regiao_env: str = "AWS_DEFAULT_REGION"
    access_key_env: str = "AWS_ACCESS_KEY_ID"
    secret_key_env: str = "AWS_SECRET_ACCESS_KEY"
    bucket: str = "steam-reviews"
    camadas: CamadasDatalake


class ConfiguracaoDatalake(ModeloBaseConfiguracao):
    """Mapeamento do arquivo datalake.yaml."""

    datalake: DetalhesDatalake


class ServicoInferenciaMlflow(ModeloBaseConfiguracao):
    """Configurações de serving do MLflow."""

    ativado: bool = False
    porta: int = 8080


class DetalhesMlflow(ModeloBaseConfiguracao):
    """Mapeamento de rastreamento do MLflow."""

    ativado: bool = True
    tracking_uri_env: str = "MLFLOW_TRACKING_URI"
    experimento: str = "steam_reviews_clustering"
    artefatos_destino_env: str = "MLFLOW_ARTIFACTS_DESTINATION"
    registrar_modelos: bool = True
    serving: ServicoInferenciaMlflow


class ConfiguracaoMlflow(ModeloBaseConfiguracao):
    """Mapeamento do arquivo mlflow.yaml."""

    mlflow: DetalhesMlflow


class ConfiguracaoPaginacaoIncremental(ModeloBaseConfiguracao):
    """Parâmetros de paginação lazy."""

    tamanho_pagina: int = 100
    maximo_paginas_por_execucao: int = 10000
    detectar_cursor_repetido: bool = True


class ConfiguracaoStagingIncremental(ModeloBaseConfiguracao):
    """Parâmetros de processamento em lote no staging."""

    tamanho_lote: int = 500
    transacao_por_lote: bool = True
    checkpoint_por_lote: bool = True


class ConfiguracaoPublicacaoIncremental(ModeloBaseConfiguracao):
    """Parâmetros de publicação outbox."""

    tamanho_lote: int = 500
    retomar_apos_falha: bool = True


class LimitesIncrementais(ModeloBaseConfiguracao):
    """Limites de contenção e backpressure."""

    maximo_registros_em_buffer: int = 1000


class DetalhesFluxosIncrementais(ModeloBaseConfiguracao):
    """Mapeamento do bloco fluxos_incrementais."""

    ativado: bool = True
    modo: str = "sincronico"
    paginacao: ConfiguracaoPaginacaoIncremental
    staging: ConfiguracaoStagingIncremental
    publicacao: ConfiguracaoPublicacaoIncremental
    limites: LimitesIncrementais


class ConfiguracaoFluxosIncrementais(ModeloBaseConfiguracao):
    """Mapeamento do arquivo fluxos_incrementais.yaml."""

    fluxos_incrementais: DetalhesFluxosIncrementais
