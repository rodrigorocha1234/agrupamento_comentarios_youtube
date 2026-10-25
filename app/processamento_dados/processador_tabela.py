"""Processador de tabelas com execução ordenada: primeiro transformações, depois criação de colunas."""

import pandas as pd
import polars as pl

from app.conf_yaml import (
    ConfigCriacaoColunas,
    ConfigFiltrosProcessamento,
    ConfigProcessamentoInfo,
    ConfigTransformacoesProcessamento,
)
from app.excecoes import ErroPreprocessamento
from app.processamento_dados.avaliador_expressao import AvaliadorExpressao


class ProcessadorTabela:
    """Orquestra o pré-processamento tabular executando transformação primeiro e criação de colunas depois."""

    def __init__(self, avaliador: AvaliadorExpressao | None = None) -> None:
        self._avaliador = avaliador or AvaliadorExpressao()

    def processar(self, dados: pd.DataFrame, config: ConfigProcessamentoInfo) -> pd.DataFrame:
        """Executa a esteira de processamento tabular.

        Ordem obrigatória:
        1. Seleção inicial de colunas
        2. Aplicação de filtros declarativos (se habilitados)
        3. Transformação de colunas existentes (PRIMEIRO)
        4. Criação de novas colunas (DEPOIS)
        """
        resultado = dados.copy()

        # 1. Seleção inicial de colunas (se habilitada)
        config_colunas = (
            config.selecao_colunas
            if config.selecao_colunas.habilitado
            else config.colunas
        )
        if config_colunas.habilitado:
            colunas_ativas = config_colunas.obter_colunas_selecionadas()
            if colunas_ativas:
                colunas_existentes = [c for c in colunas_ativas if c in resultado.columns]
                if colunas_existentes:
                    resultado = pd.DataFrame(resultado.loc[:, colunas_existentes])

        # 2. Executar FILTROS declarativos (se habilitados)
        if config.filtros.habilitado and config.filtros.condicoes:
            resultado = self.executar_filtros(resultado, config.filtros, motor=config.motor)

        # 3. Executar TRANSFORMAÇÃO DE COLUNAS PRIMEIRO
        if config.transformacoes.habilitado and config.transformacoes.operacoes:
            resultado = self.executar_transformacoes(
                resultado,
                config.transformacoes,
                motor=config.motor,
            )

        # 4. Executar CRIAÇÃO DE NOVAS COLUNAS DEPOIS
        if config.criacao_colunas.habilitado and config.criacao_colunas.atributos:
            resultado = self.executar_criacao_colunas(
                resultado,
                config.criacao_colunas,
                motor=config.motor,
            )

        return resultado

    def executar_filtros(
        self,
        dados: pd.DataFrame,
        config_filtros: ConfigFiltrosProcessamento,
        motor: str = "pandas",
    ) -> pd.DataFrame:
        """Aplica filtros booleanos baseados em expressões python para Pandas ou Polars."""
        condicoes_ativas = [c for c in config_filtros.condicoes if c.habilitado]
        if not condicoes_ativas or dados.empty:
            return dados.copy()

        if motor == "polars":
            df_pl = pl.from_pandas(dados)
            expressoes_polars: list[pl.Expr] = []
            for cond in condicoes_ativas:
                expr_str = cond.expressao_polars.strip() or cond.expressao_pandas.strip()
                if expr_str:
                    expr_obj = self._avaliador.avaliar_filtro_polars(expr_str)
                    expressoes_polars.append(expr_obj)

            if not expressoes_polars:
                return dados.copy()

            if config_filtros.combinacao == "or":
                expr_combinada = expressoes_polars[0]
                for e in expressoes_polars[1:]:
                    expr_combinada = expr_combinada | e
            else:
                expr_combinada = expressoes_polars[0]
                for e in expressoes_polars[1:]:
                    expr_combinada = expr_combinada & e

            df_filtrado_pl = df_pl.filter(expr_combinada)
            return df_filtrado_pl.to_pandas()

        # Motor padrão Pandas
        mascaras: list[pd.Series] = []
        for cond in condicoes_ativas:
            expr_str = cond.expressao_pandas.strip()
            if expr_str:
                mascara = self._avaliador.avaliar_filtro_pandas(expr_str, dados)
                mascaras.append(mascara)

        if not mascaras:
            return dados.copy()

        if config_filtros.combinacao == "or":
            mascara_final = mascaras[0]
            for m in mascaras[1:]:
                mascara_final = mascara_final | m
        else:
            mascara_final = mascaras[0]
            for m in mascaras[1:]:
                mascara_final = mascara_final & m

        return pd.DataFrame(dados.loc[mascara_final])

    def executar_transformacoes(
        self,
        dados: pd.DataFrame,
        config_transformacoes: ConfigTransformacoesProcessamento,
        motor: str = "pandas",
    ) -> pd.DataFrame:
        """Aplica transformações declarativas nas colunas existentes (executado PRIMEIRO)."""
        resultado = dados.copy()
        for op in config_transformacoes.operacoes:
            if not op.habilitado:
                continue

            coluna = op.coluna
            if coluna not in resultado.columns:
                continue

            if motor == "polars":
                expr_str = op.expressao_polars.strip() or op.expressao_pandas.strip()
                if expr_str:
                    df_pl = pl.from_pandas(resultado)
                    df_pl = self._avaliador.avaliar_polars(expr_str, df_pl, nome_coluna=coluna)
                    resultado = df_pl.to_pandas()
            else:
                expr_str = op.expressao_pandas.strip()
                if expr_str:
                    serie = self._avaliador.avaliar_pandas(expr_str, resultado)
                    resultado[coluna] = serie

        return resultado

    def executar_criacao_colunas(
        self,
        dados: pd.DataFrame,
        config_criacao: ConfigCriacaoColunas,
        motor: str = "pandas",
    ) -> pd.DataFrame:
        """Cria novos atributos vetorizados a partir de expressões (executado DEPOIS das transformações)."""
        resultado = dados.copy()

        for atributo in config_criacao.atributos:
            if not atributo.habilitado:
                continue

            nome_novo = atributo.nome.strip()
            if not nome_novo:
                continue

            if motor == "polars":
                expressao = atributo.expressao_polars.strip() or atributo.expressao_pandas.strip()
                tabela_pl = pl.from_pandas(resultado)
                tabela_transformada = self._avaliador.avaliar_polars(expressao, tabela_pl, nome_novo)
                resultado = tabela_transformada.to_pandas()
            else:
                expressao = atributo.expressao_pandas.strip()
                if not expressao:
                    raise ErroPreprocessamento(
                        f"Expressão Pandas ausente para criação da coluna '{nome_novo}'."
                    )
                serie_nova = self._avaliador.avaliar_pandas(expressao, resultado)
                resultado[nome_novo] = serie_nova

        return resultado
