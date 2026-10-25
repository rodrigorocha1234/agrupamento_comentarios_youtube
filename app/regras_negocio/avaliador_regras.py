"""Motor seguro de avaliação declarativa de regras de negócio para clusters e amostras."""

from typing import Literal

import pandas as pd
import polars as pl

from app.analise_clusters.analisador_clusters import PerfilCluster
from app.conf_yaml import ConfigRegraItem, ConfigRegrasNegocioInfo
from app.processamento_dados.avaliador_expressao import AvaliadorExpressao


class AvaliadorRegrasNegocio:
    """Aplica regras de negócio declarativas sobre perfis agregados e dados individuais via expressões seguras."""

    def __init__(self, config: ConfigRegrasNegocioInfo) -> None:
        self._config = config
        self._habilitado = config.habilitado
        self._motor: Literal["pandas", "polars"] = config.motor
        self._regras = [r for r in config.regras if r.habilitado]
        self._avaliador_expressao = AvaliadorExpressao()

    @property
    def habilitado(self) -> bool:
        """Indica se o motor de regras de negócio está ativado."""
        return self._habilitado

    @property
    def motor(self) -> str:
        """Retorna o motor configurado para avaliação de expressões ('pandas' ou 'polars')."""
        return self._motor

    @staticmethod
    def _criar_dataframe_perfil(perfil: PerfilCluster) -> pd.DataFrame:
        """Estrutura os atributos do perfil em DataFrame para avaliação vetorizada de expressões."""
        dados: dict[str, object] = {
            "id_cluster": [perfil.id_cluster],
            "quantidade_amostras": [perfil.quantidade_amostras],
            "proporcao_amostras": [perfil.proporcao_amostras],
            "distancia_media_centroide": [
                perfil.distancia_media_centroide if perfil.distancia_media_centroide is not None else 0.0
            ],
        }
        for attr, val in perfil.medias_atributos.items():
            dados[attr] = [val]
            dados[f"{attr}_media"] = [val]
        for attr, val in perfil.medianas_atributos.items():
            dados[f"{attr}_mediana"] = [val]
        for m_nome, m_val in perfil.metricas_personalizadas.items():
            dados[m_nome] = [m_val]
        return pd.DataFrame(dados)

    def _avaliar_regra_cluster(self, perfil: PerfilCluster, regra: ConfigRegraItem) -> bool:
        """Avalia se um perfil de cluster satisfaz a expressão configurada da regra."""
        expr_polars = regra.expressao_polars.strip()
        expr_pandas = regra.expressao_pandas.strip()

        if self._motor == "polars" and expr_polars:
            df_perfil = self._criar_dataframe_perfil(perfil)
            df_pl = pl.from_pandas(df_perfil)
            mascara = self._avaliador_expressao.avaliar_mascara_polars(expr_polars, df_pl)
            return bool(mascara[0]) if len(mascara) > 0 else False

        if expr_pandas:
            df_perfil = self._criar_dataframe_perfil(perfil)
            mascara = self._avaliador_expressao.avaliar_filtro_pandas(expr_pandas, df_perfil)
            return bool(mascara.iloc[0]) if len(mascara) > 0 else False

        if expr_polars:
            df_perfil = self._criar_dataframe_perfil(perfil)
            df_pl = pl.from_pandas(df_perfil)
            mascara = self._avaliador_expressao.avaliar_mascara_polars(expr_polars, df_pl)
            return bool(mascara[0]) if len(mascara) > 0 else False

        return False

    def aplicar_regras_perfil(self, perfil: PerfilCluster) -> PerfilCluster:
        """Aplica regras de negócio com alvo 'cluster' e anota persona e alertas."""
        if not self._habilitado:
            return perfil

        # Ruído não recebe persona de cluster normal
        if perfil.id_cluster == -1:
            return perfil

        rotulo_final = perfil.rotulo_negocio
        alerta_final = perfil.alerta_negocio
        prioridade_final = perfil.prioridade_negocio

        regras_cluster = [r for r in self._regras if r.alvo == "cluster"]

        for regra in regras_cluster:
            casou = self._avaliar_regra_cluster(perfil, regra)
            if casou:
                if regra.acao.rotulo:
                    rotulo_final = regra.acao.rotulo
                if regra.acao.alerta:
                    alerta_final = True
                if regra.acao.prioridade:
                    prioridade_final = regra.acao.prioridade
                break

        return PerfilCluster(
            id_cluster=perfil.id_cluster,
            nome_rotulo=perfil.nome_rotulo,
            quantidade_amostras=perfil.quantidade_amostras,
            proporcao_amostras=perfil.proporcao_amostras,
            medias_atributos=perfil.medias_atributos,
            medianas_atributos=perfil.medianas_atributos,
            distancia_media_centroide=perfil.distancia_media_centroide,
            rotulo_negocio=rotulo_final,
            alerta_negocio=alerta_final,
            prioridade_negocio=prioridade_final,
            metricas_personalizadas=perfil.metricas_personalizadas,
        )

    def aplicar_regras_clusters(self, perfis: list[PerfilCluster]) -> list[PerfilCluster]:
        """Aplica regras de negócio sobre uma lista completa de perfis agregados de clusters."""
        if not self._habilitado:
            return perfis
        return [self.aplicar_regras_perfil(p) for p in perfis]

    def aplicar_regras_amostras(self, dados: pd.DataFrame) -> pd.DataFrame:
        """Aplica regras de negócio declarativas sobre linhas de dados individuais via expressões seguras."""
        if not self._habilitado or dados.empty:
            return dados

        resultado = dados.copy()
        regras_amostra = [r for r in self._regras if r.alvo == "amostra"]
        df_pl_cache: pl.DataFrame | None = None

        for regra in regras_amostra:
            expr_polars = regra.expressao_polars.strip()
            expr_pandas = regra.expressao_pandas.strip()
            mascara_final: pd.Series | None = None

            if self._motor == "polars" and expr_polars:
                if df_pl_cache is None:
                    df_pl_cache = pl.from_pandas(resultado)
                bool_arr = self._avaliador_expressao.avaliar_mascara_polars(expr_polars, df_pl_cache)
                mascara_final = pd.Series(bool_arr, index=resultado.index, dtype=bool)
            elif expr_pandas:
                m = self._avaliador_expressao.avaliar_filtro_pandas(expr_pandas, resultado)
                mascara_final = pd.Series(m, index=resultado.index, dtype=bool)
            elif expr_polars:
                if df_pl_cache is None:
                    df_pl_cache = pl.from_pandas(resultado)
                bool_arr = self._avaliador_expressao.avaliar_mascara_polars(expr_polars, df_pl_cache)
                mascara_final = pd.Series(bool_arr, index=resultado.index, dtype=bool)

            if mascara_final is None:
                continue

            nome_col_tag = f"tag_{regra.acao.tag}" if regra.acao.tag else f"tag_{regra.nome.lower().replace(' ', '_')}"
            resultado[nome_col_tag] = mascara_final

            if regra.acao.alerta:
                if "alerta_negocio" in resultado.columns:
                    resultado["alerta_negocio"] = resultado["alerta_negocio"] | mascara_final
                else:
                    resultado["alerta_negocio"] = mascara_final

        return resultado
