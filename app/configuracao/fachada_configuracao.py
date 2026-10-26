"""Fachada central (GoF Facade) e Composite para representação unificada das configurações."""

from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from app.configuracao.analises import ConfigAnalises
from app.configuracao.api import ConfigAPI
from app.configuracao.atributos import ConfigAtributos
from app.configuracao.avaliacao import ConfigAvaliacao
from app.configuracao.cadastro import ConfigCadastroProjeto
from app.configuracao.clustering import ConfigClustering
from app.configuracao.construtor_configuracao import ConstrutorConfiguracao
from app.configuracao.datalake import ConfigDatalake
from app.configuracao.fonte_dados import ConfigFonteDados
from app.configuracao.mlflow import ConfigMLflow
from app.configuracao.observabilidade import ConfigObservabilidade
from app.configuracao.pln import ConfigPLN
from app.configuracao.preprocessamento import ConfigPreprocessamento
from app.configuracao.processamento import ConfigProcessamento
from app.configuracao.projeto import ConfigProjeto
from app.configuracao.regras_negocio import ConfigRegrasNegocio
from app.configuracao.temporal import ConfigAnaliseTemporal
from app.excecoes import ErroConfiguracao


class ConfYAML(BaseModel):
    """Representação unificada e validada de todos os arquivos YAML de configuração (GoF Composite/Facade)."""

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
    pln: ConfigPLN = Field(default_factory=ConfigPLN)
    analise_temporal: ConfigAnaliseTemporal = Field(default_factory=ConfigAnaliseTemporal)

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

        # Regra 2: PLN desativado por padrão (a menos que explicitamente habilitado)
        pln_habilitado = self.projeto.funcionalidades.pln.habilitado or self.pln.pln.habilitado
        if not pln_habilitado and self.atributos.atributos.texto.incluir_no_treino:
            raise ErroConfiguracao(
                "Inconsistência: funcionalidades.pln.habilitado é False, "
                "mas atributos.texto.incluir_no_treino está True."
            )

        return self

    @classmethod
    def carregar_de_diretorio(cls, caminho_diretorio: Path | str) -> "ConfYAML":
        """Carrega e valida todos os arquivos YAML do diretório especificado via ConstrutorConfiguracao."""
        valores = ConstrutorConfiguracao.construir_valores(caminho_diretorio)

        return cls(
            cadastro_projeto=valores["cadastro_projeto"],  # type: ignore[arg-type]
            projeto=valores["projeto"],  # type: ignore[arg-type]
            fonte_dados=valores["fonte_dados"],  # type: ignore[arg-type]
            processamento=valores["processamento"],  # type: ignore[arg-type]
            datalake=valores["datalake"],  # type: ignore[arg-type]
            atributos=valores["atributos"],  # type: ignore[arg-type]
            preprocessamento=valores["preprocessamento"],  # type: ignore[arg-type]
            clustering=valores["clustering"],  # type: ignore[arg-type]
            avaliacao=valores["avaliacao"],  # type: ignore[arg-type]
            mlflow=valores["mlflow"],  # type: ignore[arg-type]
            observabilidade=valores["observabilidade"],  # type: ignore[arg-type]
            analises=valores["analises"],  # type: ignore[arg-type]
            api=valores["api"],  # type: ignore[arg-type]
            regras_negocio=valores["regras_negocio"],  # type: ignore[arg-type]
            pln=valores["pln"],  # type: ignore[arg-type]
            analise_temporal=valores["analise_temporal"],  # type: ignore[arg-type]
        )
