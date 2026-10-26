"""Avaliador seguro de expressões Python para filtros, criação e transformação de colunas."""

import ast
from types import ModuleType
from typing import Final

import numpy as np
import pandas as pd
import polars as pl

from app.excecoes import ErroPreprocessamento

NODOS_PERMITIDOS: Final[set[type[ast.AST]]] = {
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.UAdd,
    # Comparações
    ast.Compare,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    # Operadores lógicos e bitwise para séries/arrays
    ast.BitAnd,
    ast.BitOr,
    ast.Invert,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.Not,
    # Estruturas e referências
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Subscript,
    ast.Attribute,
    ast.Call,
    ast.keyword,
}

NOMES_PERMITIDOS: Final[set[str]] = {"df", "np", "pd", "pl"}


class ValidadorASTSeguro(ast.NodeVisitor):
    """Garante que a expressão contenha apenas nós matemáticos e variáveis autorizadas."""

    def generic_visit(self, node: ast.AST) -> None:
        if type(node) not in NODOS_PERMITIDOS:
            raise ErroPreprocessamento(
                f"Construção sintática '{type(node).__name__}' não é permitida em expressões declarativas."
            )
        super().generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id not in NOMES_PERMITIDOS:
            raise ErroPreprocessamento(
                f"Identificador '{node.id}' não é autorizado. Use apenas: {sorted(NOMES_PERMITIDOS)}."
            )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.startswith("_"):
            raise ErroPreprocessamento(f"Acesso a membros privados ou especiais '{node.attr}' é proibido.")
        self.generic_visit(node)


class AvaliadorExpressao:
    """Executa expressões vetorizadas em Pandas e Polars de forma segura."""

    def __init__(self) -> None:
        self._validador = ValidadorASTSeguro()

    def avaliar_pandas(self, expressao: str, dados: pd.DataFrame) -> pd.Series:
        """Avalia expressão aritmética/transformação para DataFrame Pandas."""
        if not expressao.strip():
            raise ErroPreprocessamento("Expressão para Pandas não pode ser vazia.")

        try:
            arvore = ast.parse(expressao, mode="eval")
            self._validador.visit(arvore)
            codigo = compile(arvore, filename="<expressao_pandas>", mode="eval")
            contexto: dict[str, ModuleType | pd.DataFrame] = {
                "df": dados,
                "np": np,
                "pd": pd,
            }
            resultado = eval(codigo, {"__builtins__": {}}, contexto)
            if isinstance(resultado, pd.Series):
                return resultado
            if isinstance(resultado, (np.ndarray, list, int, float)):
                return pd.Series(resultado, index=dados.index)
            raise ErroPreprocessamento(f"Resultado da expressão não é uma série ou array válido: {type(resultado)}")
        except Exception as exc:
            raise ErroPreprocessamento(f"Falha ao avaliar expressão Pandas '{expressao}': {exc}") from exc

    def avaliar_filtro_pandas(self, expressao: str, dados: pd.DataFrame) -> pd.Series:
        """Avalia expressão booleana de filtro retornando máscara booleana para Pandas."""
        if not expressao.strip():
            raise ErroPreprocessamento("Expressão de filtro para Pandas não pode ser vazia.")

        try:
            arvore = ast.parse(expressao, mode="eval")
            self._validador.visit(arvore)
            codigo = compile(arvore, filename="<filtro_pandas>", mode="eval")
            contexto: dict[str, ModuleType | pd.DataFrame] = {
                "df": dados,
                "np": np,
                "pd": pd,
            }
            resultado = eval(codigo, {"__builtins__": {}}, contexto)
            if isinstance(resultado, pd.Series):
                return resultado.astype(bool)
            if isinstance(resultado, (np.ndarray, list)):
                return pd.Series(resultado, index=dados.index, dtype=bool)
            raise ErroPreprocessamento(f"Resultado do filtro não é uma máscara booleana: {type(resultado)}")
        except Exception as exc:
            raise ErroPreprocessamento(f"Falha ao avaliar filtro Pandas '{expressao}': {exc}") from exc

    def avaliar_polars(self, expressao: str, dados: pl.DataFrame, nome_coluna: str) -> pl.DataFrame:
        """Avalia expressão de criação de coluna para DataFrame Polars."""
        if not expressao.strip():
            raise ErroPreprocessamento("Expressão para Polars não pode ser vazia.")

        try:
            arvore = ast.parse(expressao, mode="eval")
            self._validador.visit(arvore)
            codigo = compile(arvore, filename="<expressao_polars>", mode="eval")
            contexto: dict[str, ModuleType] = {
                "pl": pl,
                "np": np,
            }
            expr_obj = eval(codigo, {"__builtins__": {}}, contexto)
            if isinstance(expr_obj, pl.Expr):
                return dados.with_columns(expr_obj.alias(nome_coluna))
            raise ErroPreprocessamento(f"Resultado não é uma expressão Polars válida: {type(expr_obj)}")
        except Exception as exc:
            raise ErroPreprocessamento(f"Falha ao avaliar expressão Polars '{expressao}': {exc}") from exc

    def avaliar_filtro_polars(self, expressao: str) -> pl.Expr:
        """Avalia expressão de filtro retornando expressão booleana Polars."""
        if not expressao.strip():
            raise ErroPreprocessamento("Expressão de filtro para Polars não pode ser vazia.")

        try:
            arvore = ast.parse(expressao, mode="eval")
            self._validador.visit(arvore)
            codigo = compile(arvore, filename="<filtro_polars>", mode="eval")
            contexto: dict[str, ModuleType] = {
                "pl": pl,
                "np": np,
            }
            expr_obj = eval(codigo, {"__builtins__": {}}, contexto)
            if isinstance(expr_obj, pl.Expr):
                return expr_obj
            raise ErroPreprocessamento(f"Resultado não é uma expressão booleana Polars: {type(expr_obj)}")
        except Exception as exc:
            raise ErroPreprocessamento(f"Falha ao avaliar filtro Polars '{expressao}': {exc}") from exc

    def avaliar_mascara_polars(self, expressao: str, dados: pl.DataFrame) -> np.ndarray:
        """Avalia expressão booleana no Polars retornando array numpy booleano."""
        expr_filtro = self.avaliar_filtro_polars(expressao)
        serie_pl = dados.select(expr_filtro).to_series()
        return np.asarray(serie_pl.to_numpy(), dtype=bool)
