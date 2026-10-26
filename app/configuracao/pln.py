"""Modelos de configuração de Processamento de Linguagem Natural (PLN)."""

from typing import Literal

from pydantic import BaseModel, Field


class ConfigSpacyInfo(BaseModel):
    modelo: str = "pt_core_news_sm"
    remover_stopwords: bool = True
    lematizar: bool = True
    remover_pontuacao: bool = True
    remover_numeros: bool = True
    converter_minusculas: bool = True


class ConfigTFIDFInfo(BaseModel):
    max_features: int = 100
    ngram_range: list[int] = Field(default_factory=lambda: [1, 2])
    min_df: int = 1
    max_df: float = 1.0
    sublinear_tf: bool = True


class ConfigCountInfo(BaseModel):
    max_features: int = 100
    ngram_range: list[int] = Field(default_factory=lambda: [1, 1])
    min_df: int = 1


class ConfigFusaoPLNInfo(BaseModel):
    modo: Literal["apenas_texto", "concatenar"] = "apenas_texto"
    prefixo_coluna: str = "pln_"


class ConfigPLNInfo(BaseModel):
    habilitado: bool = False
    tratamento: Literal["spacy", "tfidf", "count"] = "spacy"
    coluna_texto: str = "review"
    tamanho_minimo_caracteres: int = 3
    substituir_vazios_por: str = "sem_comentario"
    spacy: ConfigSpacyInfo = Field(default_factory=ConfigSpacyInfo)
    tfidf: ConfigTFIDFInfo = Field(default_factory=ConfigTFIDFInfo)
    count: ConfigCountInfo = Field(default_factory=ConfigCountInfo)
    fusao: ConfigFusaoPLNInfo = Field(default_factory=ConfigFusaoPLNInfo)


class ConfigPLN(BaseModel):
    pln: ConfigPLNInfo = Field(default_factory=ConfigPLNInfo)
