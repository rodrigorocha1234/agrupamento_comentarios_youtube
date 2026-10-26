"""Modelos de configuração visual, diagnósticos de agrupamento e exportação analítica."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from app.configuracao.expansor import expandir_variaveis_ambiente


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


class ConfigMetricaResumo(BaseModel):
    nome: str
    coluna: str
    operacao: Literal["media", "soma", "proporcao", "mediana"] = "media"
    divisor: float = 1.0


class ConfigAmostrasAnalises(BaseModel):
    quantidade_por_cluster: int = 5
    colunas: list[str] = Field(default_factory=list)


class ConfigDispersaoGrafico(BaseModel):
    """Atributos configurados para os eixos da dispersão 2D."""

    atributo_x: str = ""
    atributo_y: str = ""


class ConfigBoxplotGrafico(BaseModel):
    """Atributo configurado para geração de diagramas boxplot."""

    atributo: str = ""


class ConfigTabelaResumoGrafico(BaseModel):
    """Rótulos dos cabeçalhos da tabela descritiva de clusters."""

    coluna_cluster: str = "Cluster"
    coluna_persona: str = "Persona / Negócio"
    coluna_alerta: str = "Alerta"
    coluna_quantidade: str = "Qtd Amostras"
    coluna_proporcao: str = "Proporção (%)"
    coluna_distancia_centroide: str = "Dist. Centroide"


class ConfigLayoutGraficos(BaseModel):
    """Configurações visuais, títulos de eixos e cabeçalhos de relatórios."""

    titulo_pca: str = "Projeção Exploratória dos Agrupamentos (PCA 2D)"
    titulo_distribuicao: str = "Distribuição de Amostras por Cluster"
    eixo_x_distribuicao: str = "Agrupamento"
    eixo_y_distribuicao: str = "Quantidade de Amostras"
    titulo_perfil: str = "Perfil Médio dos Atributos por Cluster"
    titulo_resumo: str = "Resumo Estatístico dos Clusters"
    titulo_relatorio: str = "Relatório Analítico de Agrupamento"
    subtitulo_relatorio: str = "Diagnósticos visuais, distribuição de grupos e projeções multidimensionais."
    tema: str = "plotly_white"
    cor_ruido: str = "#888888"
    cor_cluster_padrao: str = "#3498db"
    rotulo_ruido: str = "Ruído (-1)"


class ConfigAnalisesInfo(BaseModel):
    engine: Literal["plotly", "altair", "pandas_profiling"] = "plotly"
    clusters: ConfigClustersAnalises = Field(default_factory=ConfigClustersAnalises)
    exportacao: ConfigExportacaoAnalises = Field(default_factory=ConfigExportacaoAnalises)
    layout: ConfigLayoutGraficos = Field(default_factory=ConfigLayoutGraficos)
    tabela_resumo: ConfigTabelaResumoGrafico = Field(default_factory=ConfigTabelaResumoGrafico)
    dispersao: ConfigDispersaoGrafico = Field(default_factory=ConfigDispersaoGrafico)
    boxplot: ConfigBoxplotGrafico = Field(default_factory=ConfigBoxplotGrafico)
    metricas_resumo: list[ConfigMetricaResumo] = Field(default_factory=list)
    amostras: ConfigAmostrasAnalises = Field(default_factory=ConfigAmostrasAnalises)

    @classmethod
    def carregar_de_arquivo(cls, caminho: Path | str = "config/analises.yaml") -> "ConfigAnalisesInfo":
        """Carrega a configuração de análises a partir de um arquivo YAML se disponível."""
        path = Path(caminho)
        if not path.is_file():
            return cls()
        try:
            conteudo = expandir_variaveis_ambiente(path.read_text(encoding="utf-8"))
            dados = yaml.safe_load(conteudo) or {}
            if isinstance(dados, dict) and "analises" in dados and isinstance(dados["analises"], dict):
                return cls.model_validate(dados["analises"])
            if isinstance(dados, dict):
                return cls.model_validate(dados)
        except (yaml.YAMLError, OSError, ValueError):
            return cls()
        return cls()


class ConfigAnalises(BaseModel):
    analises: ConfigAnalisesInfo = Field(default_factory=ConfigAnalisesInfo)
