"""Modelos de especificação de processamento tabular (Pandas e Polars)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
