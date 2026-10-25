"""Módulo de carregamento e validação centralizada das configurações YAML.

Arquitetura genérica e desacoplada de domínios específicos, extensível para
qualquer projeto de agrupamento não supervisionado.
"""

import os
import re
from pathlib import Path
from typing import Final, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.excecoes import ErroConfiguracao

PADRAO_VARIAVEL_AMBIENTE: Final[re.Pattern[str]] = re.compile(r"\$\{([A-Za-z0-9_]+)(?::-([^}]*))?\}")


def expandir_variaveis_ambiente(conteudo: str) -> str:
    """Substitui padrões ${VAR} ou ${VAR:-default} pelos valores de ambiente correspondentes."""

    def substituir(match: re.Match[str]) -> str:
        nome_var = match.group(1)
        valor_padrao = match.group(2) if match.group(2) is not None else ""
        return os.environ.get(nome_var, valor_padrao)

    return PADRAO_VARIAVEL_AMBIENTE.sub(substituir, conteudo)


# ==============================================================================
# Modelos de Cadastro e Metadados do Projeto
# ==============================================================================


class ConfigMapeamentoOrigem(BaseModel):
    """Mapeamento de chaves e campos de dados da fonte externa."""

    tipo_fonte: str = "api_rest"
    identificador_primario: str = "id"
    identificador_contexto: str = "contexto_id"
    campo_texto_consulta: str = "texto"
    campos_numericos_padrao: list[str] = Field(default_factory=list)
    campos_temporais: list[str] = Field(default_factory=list)


class ConfigInfraestruturaProjeto(BaseModel):
    """Parâmetros de infraestrutura específicos do projeto."""

    datalake_bucket: str = "datalake-clustering"
    mlflow_experimento: str = "experimento_clustering"


class ConfigCadastroProjetoInfo(BaseModel):
    """Cadastro formal e metadados de domínio do projeto de agrupamento."""

    id_projeto: str = "projeto_agrupamento"
    nome: str = "Agrupamento Não Supervisionado"
    descricao: str = "Pipeline reutilizável de clustering não supervisionado"
    versao: str = "1.0.0"
    dominio: str = "geral"
    entidade: str = "amostra"
    mapeamento_origem: ConfigMapeamentoOrigem = Field(default_factory=ConfigMapeamentoOrigem)
    infraestrutura: ConfigInfraestruturaProjeto = Field(default_factory=ConfigInfraestruturaProjeto)


class ConfigCadastroProjeto(BaseModel):
    """Container para o arquivo cadastro_projeto.yaml."""

    cadastro_projeto: ConfigCadastroProjetoInfo = Field(default_factory=ConfigCadastroProjetoInfo)


# ==============================================================================
# Modelos de Projeto e Funcionalidades Globais
# ==============================================================================


class ConfigProjetoInfo(BaseModel):
    nome: str = "projeto_clustering"
    ambiente: str = "desenvolvimento"
    idioma: str = "pt-BR"


class ConfigFuncionalidadePLN(BaseModel):
    habilitado: bool = False


class ConfigFuncionalidadeTemporal(BaseModel):
    habilitado: bool = False


class ConfigFuncionalidadeAPI(BaseModel):
    habilitado: bool = True


class ConfigFuncionalidadeMLflow(BaseModel):
    habilitado: bool = True


class ConfigFuncionalidades(BaseModel):
    pln: ConfigFuncionalidadePLN = Field(default_factory=ConfigFuncionalidadePLN)
    analise_temporal: ConfigFuncionalidadeTemporal = Field(default_factory=ConfigFuncionalidadeTemporal)
    api: ConfigFuncionalidadeAPI = Field(default_factory=ConfigFuncionalidadeAPI)
    mlflow: ConfigFuncionalidadeMLflow = Field(default_factory=ConfigFuncionalidadeMLflow)


class ConfigExecucao(BaseModel):
    modo: str = "incremental"
    falhar_em_configuracao_invalida: bool = True


class ConfigProjeto(BaseModel):
    projeto: ConfigProjetoInfo = Field(default_factory=ConfigProjetoInfo)
    funcionalidades: ConfigFuncionalidades = Field(default_factory=ConfigFuncionalidades)
    execucao: ConfigExecucao = Field(default_factory=ConfigExecucao)


# ==============================================================================
# Modelos de Ingestão de Fontes (Desacoplados e Extensíveis)
# ==============================================================================


class ConfigSegredoFonte(BaseModel):
    variavel_ambiente: str = ""


class ConfigBancoDadosInfo(BaseModel):
    dsn: str = ""
    consulta_ou_tabela: str = ""
    coluna_chave: str = "id"
    coluna_timestamp: str = "data_criacao"


class ConfigAPIRestInfo(BaseModel):
    endpoint: str = ""
    metodo: Literal["GET", "POST"] = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    parametro_paginacao: str = "cursor"


class ConfigFonteInfo(BaseModel):
    """Configuração genérica de fonte de dados."""

    tipo: Literal["steam_api", "banco_dados", "api_rest"] = "api_rest"
    endpoint: str | None = None
    timeout_segundos: int = 30
    tentativas_maximas: int = 5
    espera_base_segundos: float = 1.0
    identificadores: list[str | int] = Field(default_factory=list)
    appids: list[int] = Field(default_factory=list)
    segredo: ConfigSegredoFonte = Field(default_factory=ConfigSegredoFonte)
    banco_dados: ConfigBancoDadosInfo | None = None
    api_rest: ConfigAPIRestInfo | None = None

    @model_validator(mode="after")
    def sincronizar_identificadores(self) -> "ConfigFonteInfo":
        """Compatibiliza appids com o identificadores genérico."""
        if self.appids and not self.identificadores:
            self.identificadores = [str(x) for x in self.appids]
        elif self.identificadores and not self.appids:
            self.appids = [int(x) for x in self.identificadores if str(x).isdigit()]
        return self


class ConfigParametrosFonte(BaseModel):
    """Parâmetros arbitrários de consulta/requisição específicos da fonte informada no YAML."""

    model_config = ConfigDict(extra="allow")


class ConfigColeta(BaseModel):
    """Parâmetros de orquestração de coleta e checkpointing."""

    model_config = ConfigDict(extra="allow")
    incremental: bool = True
    checkpoint_habilitado: bool = True
    deduplicar_por: str = "id"
    intervalo_minutos: int = 1440


class ConfigFonteDados(BaseModel):
    fonte: ConfigFonteInfo = Field(default_factory=ConfigFonteInfo)
    parametros_api: ConfigParametrosFonte = Field(default_factory=ConfigParametrosFonte)
    coleta: ConfigColeta = Field(default_factory=ConfigColeta)


# ==============================================================================
# Modelos de Processamento Tabular e Data Lakehouse
# ==============================================================================


class ConfigItemColuna(BaseModel):
    model_config = ConfigDict(extra="allow")
    nome: str
    habilitado: bool = False


class ConfigColunasProcessamento(BaseModel):
    model_config = ConfigDict(extra="allow")
    habilitado: bool = False
    incluir: list[str | ConfigItemColuna] = Field(default_factory=list)
    colunas: list[str | ConfigItemColuna] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalizar_colunas(self) -> "ConfigColunasProcessamento":
        if self.colunas and not self.incluir:
            self.incluir = self.colunas
        elif self.incluir and not self.colunas:
            self.colunas = self.incluir
        return self

    def obter_colunas_selecionadas(self) -> list[str]:
        """Retorna a lista de nomes das colunas ativas para seleção."""
        if not self.habilitado:
            return []
        itens = self.incluir if self.incluir else self.colunas
        colunas: list[str] = []
        for item in itens:
            if isinstance(item, str):
                colunas.append(item)
            elif item.habilitado:
                colunas.append(item.nome)
        return colunas


class ConfigCondicaoFiltro(BaseModel):
    model_config = ConfigDict(extra="allow")
    nome: str = ""
    habilitado: bool = False
    expressao_pandas: str = ""
    expressao_polars: str = ""
    coluna: str | None = None
    operador: str | None = None
    valor: str | int | float | bool | None = None


class ConfigFiltrosProcessamento(BaseModel):
    habilitado: bool = False
    combinacao: Literal["and", "or"] = "and"
    condicoes: list[ConfigCondicaoFiltro] = Field(default_factory=list)


class ConfigOperacaoTransformacao(BaseModel):
    model_config = ConfigDict(extra="allow")
    coluna: str
    habilitado: bool = False
    expressao_pandas: str = ""
    expressao_polars: str = ""


class ConfigTransformacoesProcessamento(BaseModel):
    habilitado: bool = False
    operacoes: list[ConfigOperacaoTransformacao] = Field(default_factory=list)


class ConfigNovoAtributo(BaseModel):
    nome: str
    habilitado: bool = False
    expressao_pandas: str = ""
    expressao_polars: str = ""


class ConfigCriacaoColunas(BaseModel):
    habilitado: bool = False
    atributos: list[ConfigNovoAtributo] = Field(default_factory=list)


class ConfigValidacaoProcessamento(BaseModel):
    falhar_se_colunas_ausentes: bool = True
    remover_duplicatas: bool = True


class ConfigProcessamentoInfo(BaseModel):
    motor: Literal["pandas", "polars"] = "pandas"
    cabecalho: bool = True
    colunas: ConfigColunasProcessamento = Field(default_factory=ConfigColunasProcessamento)
    selecao_colunas: ConfigColunasProcessamento = Field(default_factory=ConfigColunasProcessamento)
    filtros: ConfigFiltrosProcessamento = Field(default_factory=ConfigFiltrosProcessamento)
    transformacoes: ConfigTransformacoesProcessamento = Field(default_factory=ConfigTransformacoesProcessamento)
    criacao_colunas: ConfigCriacaoColunas = Field(default_factory=ConfigCriacaoColunas)
    validacao: ConfigValidacaoProcessamento = Field(default_factory=ConfigValidacaoProcessamento)

    @model_validator(mode="after")
    def sincronizar_selecao_colunas(self) -> "ConfigProcessamentoInfo":
        if self.selecao_colunas.habilitado and not self.colunas.habilitado:
            self.colunas = self.selecao_colunas
        elif not self.selecao_colunas.habilitado and self.colunas.habilitado:
            self.selecao_colunas = self.colunas
        elif (self.selecao_colunas.incluir or self.selecao_colunas.colunas) and not (self.colunas.incluir or self.colunas.colunas):
            self.colunas = self.selecao_colunas
        elif (self.colunas.incluir or self.colunas.colunas) and not (self.selecao_colunas.incluir or self.selecao_colunas.colunas):
            self.selecao_colunas = self.colunas
        return self


class ConfigProcessamento(BaseModel):
    processamento: ConfigProcessamentoInfo = Field(default_factory=ConfigProcessamentoInfo)


class ConfigCamadaLake(BaseModel):
    prefixo: str = "bronze"
    caminho: str | None = None

    @model_validator(mode="after")
    def resolver_prefixo(self) -> "ConfigCamadaLake":
        if self.caminho and (not self.prefixo or self.prefixo == "bronze"):
            self.prefixo = self.caminho.strip("/").split("/")[-1]
        return self


class ConfigMetadadosLake(BaseModel):
    model_config = ConfigDict(extra="allow")
    incluir_timestamp_coleta: bool = True
    incluir_identificador: bool = True
    incluir_appid: bool | None = None
    incluir_versao_schema: bool = True

    @model_validator(mode="after")
    def sincronizar_identificador(self) -> "ConfigMetadadosLake":
        if self.incluir_appid is not None:
            self.incluir_identificador = self.incluir_appid
        return self


class ConfigDatalakeInfo(BaseModel):
    habilitado: bool = True
    tipo: Literal["s3", "rustfs"] = "s3"
    formato: Literal["parquet", "json"] = "parquet"
    bucket: str = "datalake-clustering"
    endpoint_url: str = "http://127.0.0.1:9000"
    regiao: str = "us-east-1"
    bronze: ConfigCamadaLake = Field(default_factory=lambda: ConfigCamadaLake(prefixo="bronze"))
    silver: ConfigCamadaLake = Field(default_factory=lambda: ConfigCamadaLake(prefixo="silver"))
    gold: ConfigCamadaLake = Field(default_factory=lambda: ConfigCamadaLake(prefixo="gold"))
    metadados: ConfigMetadadosLake = Field(default_factory=ConfigMetadadosLake)


class ConfigDatalake(BaseModel):
    datalake: ConfigDatalakeInfo = Field(default_factory=ConfigDatalakeInfo)


# ==============================================================================
# Modelos de Atributos e Pré-processamento
# ==============================================================================


class ConfigTreinoAtributos(BaseModel):
    habilitado: bool = True
    colunas: list[str] = Field(default_factory=list)


class ConfigAvaliacaoAtributos(BaseModel):
    colunas: list[str] = Field(default_factory=list)


class ConfigEngenhariaAtributos(BaseModel):
    habilitado: bool = False
    operacoes: list[dict[str, str | int | float | bool]] = Field(default_factory=list)


class ConfigTextoAtributos(BaseModel):
    incluir_no_treino: bool = False
    motivo: str = ""


class ConfigAtributosInfo(BaseModel):
    identificadores: list[str] = Field(default_factory=list)
    treino: ConfigTreinoAtributos = Field(default_factory=ConfigTreinoAtributos)
    avaliacao: ConfigAvaliacaoAtributos = Field(default_factory=ConfigAvaliacaoAtributos)
    engenharia: ConfigEngenhariaAtributos = Field(default_factory=ConfigEngenhariaAtributos)
    texto: ConfigTextoAtributos = Field(default_factory=ConfigTextoAtributos)


class ConfigAtributos(BaseModel):
    atributos: ConfigAtributosInfo = Field(default_factory=ConfigAtributosInfo)


class ConfigValoresAusentes(BaseModel):
    estrategia: Literal["mean", "median", "most_frequent", "constant", "knn"] = "median"
    valor_constante: float = 0.0


class ConfigEscalonamento(BaseModel):
    estrategia: Literal["standard", "minmax", "robust", "maxabs", "none"] = "standard"


class ConfigTransformacoesNumericas(BaseModel):
    habilitado: bool = False
    estrategia: Literal["log1p", "power", "quantile"] = "log1p"


class ConfigOutliers(BaseModel):
    habilitado: bool = False
    estrategia: Literal["iqr", "isolation_forest", "lof"] = "iqr"
    acao: Literal["remover", "sinalizar"] = "sinalizar"


class ConfigSelecaoAtributos(BaseModel):
    habilitado: bool = False
    estrategia: Literal["variancia", "correlacao", "manual"] = "variancia"
    parametros: dict[str, float | int | str] = Field(default_factory=dict)


class ConfigReducaoDimensional(BaseModel):
    habilitado: bool = False
    estrategia: Literal["pca", "truncated_svd"] = "pca"
    componentes: int = 2


class ConfigPreprocessamentoInfo(BaseModel):
    habilitado: bool = True
    valores_ausentes: ConfigValoresAusentes = Field(default_factory=ConfigValoresAusentes)
    escalonamento: ConfigEscalonamento = Field(default_factory=ConfigEscalonamento)
    transformacoes_numericas: ConfigTransformacoesNumericas = Field(default_factory=ConfigTransformacoesNumericas)
    outliers: ConfigOutliers = Field(default_factory=ConfigOutliers)
    selecao_atributos: ConfigSelecaoAtributos = Field(default_factory=ConfigSelecaoAtributos)
    reducao_dimensional: ConfigReducaoDimensional = Field(default_factory=ConfigReducaoDimensional)


class ConfigPreprocessamento(BaseModel):
    preprocessamento: ConfigPreprocessamentoInfo = Field(default_factory=ConfigPreprocessamentoInfo)


# ==============================================================================
# Modelos de Algoritmos e Clustering
# ==============================================================================


class ConfigParametrosKMeans(BaseModel):
    n_clusters: int = 5
    init: str = "k-means++"
    n_init: str | int = "auto"
    max_iter: int = 300


class ConfigParametrosDBSCAN(BaseModel):
    eps: float = 0.5
    min_samples: int = 5
    metric: str = "euclidean"


class ConfigParametrosHDBSCAN(BaseModel):
    min_cluster_size: int = 15
    min_samples: int | None = None
    metric: str = "euclidean"


class ConfigAlgoritmosClustering(BaseModel):
    kmeans: ConfigParametrosKMeans = Field(default_factory=ConfigParametrosKMeans)
    dbscan: ConfigParametrosDBSCAN = Field(default_factory=ConfigParametrosDBSCAN)
    hdbscan: ConfigParametrosHDBSCAN = Field(default_factory=ConfigParametrosHDBSCAN)


class ConfigTuningClustering(BaseModel):
    habilitado: bool = False
    estrategia: str = "grid"
    parametros: dict[str, list[int | float | str]] = Field(default_factory=dict)


class ConfigReproducibilidadeClustering(BaseModel):
    registrar_versoes: bool = True
    registrar_configuracao: bool = True


class ConfigClusteringInfo(BaseModel):
    motor: Literal["sklearn", "pycaret"] = "sklearn"
    algoritmo: Literal["kmeans", "dbscan", "hdbscan"] = "kmeans"
    random_state: int = 42
    algoritmos: ConfigAlgoritmosClustering = Field(default_factory=ConfigAlgoritmosClustering)
    tuning: ConfigTuningClustering = Field(default_factory=ConfigTuningClustering)
    reproducibilidade: ConfigReproducibilidadeClustering = Field(default_factory=ConfigReproducibilidadeClustering)


class ConfigClustering(BaseModel):
    clustering: ConfigClusteringInfo = Field(default_factory=ConfigClusteringInfo)


# ==============================================================================
# Modelos de Avaliação e Métricas
# ==============================================================================


class ConfigItemMetrica(BaseModel):
    habilitado: bool = True


class ConfigMetricasAvaliacao(BaseModel):
    silhouette: ConfigItemMetrica = Field(default_factory=ConfigItemMetrica)
    davies_bouldin: ConfigItemMetrica = Field(default_factory=ConfigItemMetrica)
    calinski_harabasz: ConfigItemMetrica = Field(default_factory=ConfigItemMetrica)
    proporcao_ruido: ConfigItemMetrica = Field(default_factory=ConfigItemMetrica)
    distribuicao_clusters: ConfigItemMetrica = Field(default_factory=ConfigItemMetrica)


class ConfigRestricoesAvaliacao(BaseModel):
    minimo_clusters_sem_ruido: int = 2
    permitir_cluster_unico: bool = False


class ConfigEstabilidadeAvaliacao(BaseModel):
    habilitado: bool = False
    repeticoes: int = 5


class ConfigAvaliacaoInfo(BaseModel):
    metricas: ConfigMetricasAvaliacao = Field(default_factory=ConfigMetricasAvaliacao)
    restricoes: ConfigRestricoesAvaliacao = Field(default_factory=ConfigRestricoesAvaliacao)
    estabilidade: ConfigEstabilidadeAvaliacao = Field(default_factory=ConfigEstabilidadeAvaliacao)


class ConfigAvaliacao(BaseModel):
    avaliacao: ConfigAvaliacaoInfo = Field(default_factory=ConfigAvaliacaoInfo)


# ==============================================================================
# Modelos de Tracking (MLflow) e Observabilidade
# ==============================================================================


class ConfigMLflowInfo(BaseModel):
    habilitado: bool = True
    tracking_uri: str = "http://localhost:5000"
    experiment_name: str = "experimento_clustering"
    registrar_parametros: bool = True
    registrar_metricas: bool = True
    registrar_modelo: bool = True
    registrar_artefatos: bool = True
    tags: dict[str, str] = Field(default_factory=dict)


class ConfigMLflow(BaseModel):
    mlflow: ConfigMLflowInfo = Field(default_factory=ConfigMLflowInfo)


class ConfigPrometheus(BaseModel):
    habilitado: bool = True
    caminho_metricas: str = "/metrics"


class ConfigGrafana(BaseModel):
    habilitado: bool = True
    dashboards: list[str] = Field(default_factory=list)


class ConfigLogsObservabilidade(BaseModel):
    engine: str = "loki"
    alloy_habilitado: bool = True


class ConfigMetricasObservabilidade(BaseModel):
    latencia_percentis: list[float] = Field(default_factory=lambda: [0.50, 0.95, 0.99])
    coletar_throughput: bool = True
    coletar_erros: bool = True
    coletar_retries: bool = True
    coletar_freshness: bool = True
    coletar_qualidade_dados: bool = True


class ConfigObservabilidadeInfo(BaseModel):
    prometheus: ConfigPrometheus = Field(default_factory=ConfigPrometheus)
    grafana: ConfigGrafana = Field(default_factory=ConfigGrafana)
    logs: ConfigLogsObservabilidade = Field(default_factory=ConfigLogsObservabilidade)
    metricas: ConfigMetricasObservabilidade = Field(default_factory=ConfigMetricasObservabilidade)


class ConfigObservabilidade(BaseModel):
    observabilidade: ConfigObservabilidadeInfo = Field(default_factory=ConfigObservabilidadeInfo)


# ==============================================================================
# Modelos de Análises e API
# ==============================================================================


class ConfigClustersAnalises(BaseModel):
    """Opções visuais e diagnósticos de análise de clusters."""

    model_config = ConfigDict(extra="allow")
    dispersao_2d: bool = True
    dispersao_3d: bool = False
    distribuicao: bool = True
    perfil: bool = True
    resumo: bool = True
    boxplot: bool = True
    violin: bool = True
    histogramas: bool = True
    matriz_correlacao: bool = True
    scatter_matrix: bool = False
    pca_2d: bool = True
    pca_3d: bool = False
    silhouette_plot: bool = True
    ruido: bool = True
    distancia_centroides: bool = True
    interacoes_atributos: bool = True
    evolucao_temporal: bool = False
    tabela_dados_originais: bool = True
    comparar_identificadores: bool = False


class ConfigExportacaoAnalises(BaseModel):
    habilitada: bool = False
    formato: str = "html"


class ConfigAnalisesInfo(BaseModel):
    engine: Literal["plotly", "altair", "pandas_profiling"] = "plotly"
    clusters: ConfigClustersAnalises = Field(default_factory=ConfigClustersAnalises)
    exportacao: ConfigExportacaoAnalises = Field(default_factory=ConfigExportacaoAnalises)


class ConfigAnalises(BaseModel):
    analises: ConfigAnalisesInfo = Field(default_factory=ConfigAnalisesInfo)


class ConfigEndpointsAPI(BaseModel):
    health: str = "/health"
    ready: str = "/ready"
    metrics: str = "/metrics"
    model: str = "/model"
    clusters: str = "/clusters"
    predict: str = "/predict"
    predict_batch: str = "/predict-batch"


class ConfigLimitesAPI(BaseModel):
    tamanho_lote_maximo: int = 1000


class ConfigPrevisaoAPI(BaseModel):
    exigir_suporte_do_algoritmo: bool = True


class ConfigAPIInfo(BaseModel):
    habilitado: bool = True
    prefixo: str = "/api/v1"
    endpoints: ConfigEndpointsAPI = Field(default_factory=ConfigEndpointsAPI)
    limites: ConfigLimitesAPI = Field(default_factory=ConfigLimitesAPI)
    previsao: ConfigPrevisaoAPI = Field(default_factory=ConfigPrevisaoAPI)


class ConfigAPI(BaseModel):
    api: ConfigAPIInfo = Field(default_factory=ConfigAPIInfo)


class ConfigRegrasNegocioInfo(BaseModel):
    habilitado: bool = False
    regras: list[dict[str, str | int | float | bool]] = Field(default_factory=list)


class ConfigRegrasNegocio(BaseModel):
    regras_negocio: ConfigRegrasNegocioInfo = Field(default_factory=ConfigRegrasNegocioInfo)


# ==============================================================================
# Container Unificado e Validador Central
# ==============================================================================


class ConfYAML(BaseModel):
    """Representação unificada e validada de todos os arquivos YAML de configuração."""

    cadastro_projeto: ConfigCadastroProjeto = Field(default_factory=ConfigCadastroProjeto)
    projeto: ConfigProjeto
    fonte_dados: ConfigFonteDados
    processamento: ConfigProcessamento
    datalake: ConfigDatalake
    atributos: ConfigAtributos
    preprocessamento: ConfigPreprocessamento
    clustering: ConfigClustering
    avaliacao: ConfigAvaliacao
    mlflow: ConfigMLflow
    observabilidade: ConfigObservabilidade
    analises: ConfigAnalises
    api: ConfigAPI
    regras_negocio: ConfigRegrasNegocio

    @model_validator(mode="after")
    def validar_regras_globais(self) -> "ConfYAML":
        """Valida regras arquiteturais cruzadas entre configurações."""
        # Regra 1: Isolamento de identificadores da matriz de treino
        identificadores_set = set(self.atributos.atributos.identificadores)
        treino_set = set(self.atributos.atributos.treino.colunas)
        intersecao = identificadores_set.intersection(treino_set)
        if intersecao:
            raise ErroConfiguracao(
                f"Identificadores não podem fazer parte dos atributos de treino: {sorted(intersecao)}"
            )

        # Regra 2: PLN desativado por padrão
        if (
            not self.projeto.funcionalidades.pln.habilitado
            and self.atributos.atributos.texto.incluir_no_treino
        ):
            raise ErroConfiguracao(
                "Inconsistência: funcionalidades.pln.habilitado é False, "
                "mas atributos.texto.incluir_no_treino está True."
            )

        return self

    @classmethod
    def carregar_de_diretorio(cls, caminho_diretorio: Path | str) -> "ConfYAML":
        """Carrega e valida todos os arquivos YAML do diretório especificado."""
        dir_path = Path(caminho_diretorio)
        if not dir_path.is_dir():
            raise ErroConfiguracao(f"Diretório de configuração não encontrado: {dir_path}")

        arquivos_obrigatorios: Final[dict[str, type[BaseModel]]] = {
            "projeto.yaml": ConfigProjeto,
            "fonte_dados.yaml": ConfigFonteDados,
            "processamento.yaml": ConfigProcessamento,
            "datalake.yaml": ConfigDatalake,
            "atributos.yaml": ConfigAtributos,
            "preprocessamento.yaml": ConfigPreprocessamento,
            "clustering.yaml": ConfigClustering,
            "avaliacao.yaml": ConfigAvaliacao,
            "mlflow.yaml": ConfigMLflow,
            "observabilidade.yaml": ConfigObservabilidade,
            "analises.yaml": ConfigAnalises,
            "api.yaml": ConfigAPI,
            "regras_negocio.yaml": ConfigRegrasNegocio,
        }

        valores_carregados: dict[str, BaseModel] = {}

        # Carrega cadastro_projeto.yaml se presente
        arquivo_cadastro = dir_path / "cadastro_projeto.yaml"
        if arquivo_cadastro.is_file():
            try:
                conteudo_bruto = arquivo_cadastro.read_text(encoding="utf-8")
                conteudo_expandido = expandir_variaveis_ambiente(conteudo_bruto)
                dados_dict = yaml.safe_load(conteudo_expandido) or {}
                valores_carregados["cadastro_projeto"] = ConfigCadastroProjeto.model_validate(dados_dict)
            except Exception as exc:
                raise ErroConfiguracao(f"Falha ao validar cadastro_projeto.yaml: {exc}") from exc
        else:
            valores_carregados["cadastro_projeto"] = ConfigCadastroProjeto()

        for nome_arquivo, modelo_classe in arquivos_obrigatorios.items():
            arquivo_path = dir_path / nome_arquivo
            if not arquivo_path.is_file():
                raise ErroConfiguracao(f"Arquivo obrigatório de configuração ausente: {arquivo_path}")

            try:
                conteudo_bruto = arquivo_path.read_text(encoding="utf-8")
                conteudo_expandido = expandir_variaveis_ambiente(conteudo_bruto)
                dados_dict = yaml.safe_load(conteudo_expandido) or {}
                if not isinstance(dados_dict, dict):
                    raise ErroConfiguracao(f"Formato YAML inválido em {nome_arquivo}: esperado dicionário.")
                instancia = modelo_classe.model_validate(dados_dict)
                chave = nome_arquivo.removesuffix(".yaml")
                valores_carregados[chave] = instancia
            except yaml.YAMLError as exc:
                raise ErroConfiguracao(f"Erro de sintaxe YAML em {nome_arquivo}: {exc}") from exc
            except Exception as exc:
                raise ErroConfiguracao(f"Falha de validação em {nome_arquivo}: {exc}") from exc

        return cls(
            cadastro_projeto=valores_carregados["cadastro_projeto"],  # type: ignore[arg-type]
            projeto=valores_carregados["projeto"],  # type: ignore[arg-type]
            fonte_dados=valores_carregados["fonte_dados"],  # type: ignore[arg-type]
            processamento=valores_carregados["processamento"],  # type: ignore[arg-type]
            datalake=valores_carregados["datalake"],  # type: ignore[arg-type]
            atributos=valores_carregados["atributos"],  # type: ignore[arg-type]
            preprocessamento=valores_carregados["preprocessamento"],  # type: ignore[arg-type]
            clustering=valores_carregados["clustering"],  # type: ignore[arg-type]
            avaliacao=valores_carregados["avaliacao"],  # type: ignore[arg-type]
            mlflow=valores_carregados["mlflow"],  # type: ignore[arg-type]
            observabilidade=valores_carregados["observabilidade"],  # type: ignore[arg-type]
            analises=valores_carregados["analises"],  # type: ignore[arg-type]
            api=valores_carregados["api"],  # type: ignore[arg-type]
            regras_negocio=valores_carregados["regras_negocio"],  # type: ignore[arg-type]
        )
