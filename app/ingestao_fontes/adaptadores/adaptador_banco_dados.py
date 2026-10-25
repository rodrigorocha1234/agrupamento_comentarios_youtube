"""Adaptador de fonte de dados para bancos de dados relacionais (Postgres, SQLite)."""

import sqlite3
from collections.abc import Callable
from typing import Protocol, override

from app.contratos.fonte_dados import ProtocoloFonteDados
from app.excecoes import ErroConexaoFonte


class ProtocoloCursorDB(Protocol):
    @property
    def description(self) -> list[tuple[str, object, object, object, object, object, object]] | None: ...
    def execute(self, sql: str, parametros: tuple[object, ...] = ...) -> object: ...
    def fetchall(self) -> list[tuple[object, ...]]: ...
    def close(self) -> None: ...


class ProtocoloConexaoDB(Protocol):
    def cursor(self) -> object: ...
    def close(self) -> None: ...


class AdaptadorBancoDados(ProtocoloFonteDados):
    """Implementa a extração em lotes paginados a partir de tabelas ou consultas SQL."""

    def __init__(
        self,
        dsn: str,
        tabela_ou_consulta: str,
        coluna_chave: str = "id",
        conector: Callable[[str], ProtocoloConexaoDB] | None = None,
    ) -> None:
        self._dsn = dsn
        self._tabela_ou_consulta = tabela_ou_consulta
        self._coluna_chave = coluna_chave
        self._conector = conector or self._conector_padrao

    @override
    def extrair_lote(
        self,
        identificador_origem: str | int,
        marcador_posicao: str | None = None,
        limite: int = 100,
    ) -> tuple[list[dict[str, object]], str | None, bool]:
        """Extrai um lote de linhas do banco de dados utilizando marcador de offset ou cursor de chave."""
        offset = int(marcador_posicao) if marcador_posicao and marcador_posicao.isdigit() else 0

        # Constrói consulta paginada segura
        if "select" in self._tabela_ou_consulta.lower():
            sql = f"SELECT * FROM ({self._tabela_ou_consulta}) AS subq LIMIT ? OFFSET ?"
        else:
            tabela_sanitizada = self._tabela_ou_consulta.replace(";", "").strip()
            sql = f"SELECT * FROM {tabela_sanitizada} LIMIT ? OFFSET ?"

        try:
            conexao = self._conector(self._dsn)
            cursor: ProtocoloCursorDB = conexao.cursor()  # type: ignore[assignment]
            cursor.execute(sql, (limite + 1, offset))
            descricoes = cursor.description or []
            nomes_colunas = [desc[0] for desc in descricoes]
            linhas = cursor.fetchall()
            cursor.close()
            if self._conector is self._conector_padrao:
                conexao.close()
        except Exception as exc:
            raise ErroConexaoFonte(
                f"Erro ao consultar banco de dados ({self._dsn}): {exc}"
            ) from exc

        tem_mais = len(linhas) > limite
        linhas_lote = linhas[:limite]

        registros: list[dict[str, object]] = []
        for linha in linhas_lote:
            dicionario_linha: dict[str, object] = {}
            for col, val in zip(nomes_colunas, linha):
                dicionario_linha[col] = val
            registros.append(dicionario_linha)

        novo_marcador = str(offset + len(linhas_lote)) if tem_mais else None
        return registros, novo_marcador, tem_mais

    @override
    def coletar_lote(
        self,
        appid: int,
        cursor: str,
        quantidade_por_pagina: int,
    ) -> tuple[list[dict[str, object]], str, bool]:
        registros, prox_cursor, tem_mais = self.extrair_lote(
            identificador_origem=appid,
            marcador_posicao=cursor,
            limite=quantidade_por_pagina,
        )
        return registros, prox_cursor or "", tem_mais

    @staticmethod
    def _conector_padrao(dsn: str) -> ProtocoloConexaoDB:
        """Cria conexão SQLite para DSNs locais/em memória ou arquivo sqlite."""
        caminho = dsn.replace("sqlite:///", "") if dsn.startswith("sqlite") else dsn
        conexao = sqlite3.connect(caminho)
        return conexao  # type: ignore[return-value]
