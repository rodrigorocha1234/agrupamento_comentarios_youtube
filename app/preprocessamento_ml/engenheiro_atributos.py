"""Orquestrador da engenharia de atributos e geração da camada Gold no Data Lakehouse."""

from dataclasses import dataclass
from typing import Final

import pandas as pd
from sklearn.pipeline import Pipeline

from app.conf_yaml import ConfigAtributosInfo, ConfigPreprocessamentoInfo
from app.contratos.repositorio import ProtocoloRepositorioLakehouse
from app.excecoes import ErroPreprocessamento
from app.preprocessamento_ml.preparador_dados import PreparadorDados
from app.preprocessamento_ml.transformadores import FabricaTransformadores

SUFIXO_VISAO_MATRIZ: Final[str] = "matriz_treino"
SUFIXO_VISAO_METADADOS: Final[str] = "metadados"


@dataclass(frozen=True)
class ResultadoEngenhariaAtributos:
    """Encapsula o artefato de atributos gerado pronto para modelagem e auditoria."""

    matriz_treino: pd.DataFrame
    metadados: pd.DataFrame
    pipeline: Pipeline
    nomes_atributos: list[str]
    uri_gold_matriz: str = ""
    uri_gold_metadados: str = ""


class EngenheiroAtributos:
    """Conduz a transformação dos dados da camada Silver para a matriz analítica Gold."""

    def __init__(
        self,
        config_atributos: ConfigAtributosInfo,
        preparador: PreparadorDados | None = None,
    ) -> None:
        self._config_atributos = config_atributos
        self._preparador = preparador or PreparadorDados(config_atributos)

    def processar(
        self,
        dados_silver: pd.DataFrame,
        config_preprocessamento: ConfigPreprocessamentoInfo,
    ) -> ResultadoEngenhariaAtributos:
        """Executa a segregação, imputação e transformação dos dados em memória."""
        df_treino_bruto, df_metadados = self._preparador.preparar(dados_silver)

        pipeline = FabricaTransformadores.criar_pipeline(config_preprocessamento)

        try:
            matriz_array = pipeline.fit_transform(df_treino_bruto)
        except Exception as exc:
            raise ErroPreprocessamento(f"Falha ao ajustar pipeline de pré-processamento: {exc}") from exc

        # Determina os nomes das colunas de saída
        if config_preprocessamento.habilitado and config_preprocessamento.reducao_dimensional.habilitado:
            qtd_componentes = config_preprocessamento.reducao_dimensional.componentes
            nomes_colunas = [f"componente_{i + 1}" for i in range(qtd_componentes)]
        else:
            nomes_colunas = list(df_treino_bruto.columns)

        matriz_df = pd.DataFrame(
            matriz_array,
            index=df_treino_bruto.index,
            columns=nomes_colunas,
        )

        return ResultadoEngenhariaAtributos(
            matriz_treino=matriz_df,
            metadados=df_metadados,
            pipeline=pipeline,
            nomes_atributos=nomes_colunas,
        )

    def processar_e_persistir_gold(
        self,
        identificador: str | int,
        dados_silver: pd.DataFrame,
        config_preprocessamento: ConfigPreprocessamentoInfo,
        repositorio: ProtocoloRepositorioLakehouse,
    ) -> ResultadoEngenhariaAtributos:
        """Processa a matriz analítica e grava os dados no RustFS/S3 sob a camada Gold."""
        resultado = self.processar(dados_silver, config_preprocessamento)

        uri_matriz = repositorio.gravar_gold(
            identificador=identificador,
            dados=resultado.matriz_treino,
            sufixo_visao=SUFIXO_VISAO_MATRIZ,
        )

        uri_metadados = ""
        if not resultado.metadados.empty:
            uri_metadados = repositorio.gravar_gold(
                identificador=identificador,
                dados=resultado.metadados,
                sufixo_visao=SUFIXO_VISAO_METADADOS,
            )

        return ResultadoEngenhariaAtributos(
            matriz_treino=resultado.matriz_treino,
            metadados=resultado.metadados,
            pipeline=resultado.pipeline,
            nomes_atributos=resultado.nomes_atributos,
            uri_gold_matriz=uri_matriz,
            uri_gold_metadados=uri_metadados,
        )
