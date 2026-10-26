"""Modelos de pré-processamento de Machine Learning (Scikit-Learn)."""

from typing import Literal

from pydantic import BaseModel, Field


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
