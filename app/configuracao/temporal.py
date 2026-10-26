"""Modelos de configuração da dinâmica cronológica e análise temporal."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from app.configuracao.expansor import expandir_variaveis_ambiente


class ConfigDeteccaoPicosInfo(BaseModel):
    habilitado: bool = True
    limiar_desvio_padrao: float = 2.5
    minimo_amostras_periodo: int = 5


class ConfigVisualizacaoTemporalInfo(BaseModel):
    grafico_evolucao_linhas: bool = True
    grafico_area_empilhada: bool = True
    titulo_evolucao: str = "Evolução Histórica dos Agrupamentos"
    titulo_area_empilhada: str = "Composição Relativa dos Agrupamentos ao Longo do Tempo"


class ConfigAnaliseTemporalInfo(BaseModel):
    habilitado: bool = False
    coluna_referencia: str = "timestamp_created"
    formato_origem: Literal["unix_segundos", "iso8601"] = "unix_segundos"
    granularidade: Literal["diaria", "semanal", "mensal", "anual"] = "mensal"
    preencher_periodos_ausentes: bool = True
    deteccao_picos: ConfigDeteccaoPicosInfo = Field(default_factory=ConfigDeteccaoPicosInfo)
    visualizacoes: ConfigVisualizacaoTemporalInfo = Field(default_factory=ConfigVisualizacaoTemporalInfo)

    @classmethod
    def carregar_de_arquivo(
        cls, caminho: Path | str = "config/analise_temporal.yaml"
    ) -> "ConfigAnaliseTemporalInfo":
        """Carrega a configuração de análise temporal a partir de um arquivo YAML se disponível."""
        path = Path(caminho)
        if not path.is_file():
            return cls()
        try:
            conteudo = expandir_variaveis_ambiente(path.read_text(encoding="utf-8"))
            dados = yaml.safe_load(conteudo) or {}
            if isinstance(dados, dict) and "analise_temporal" in dados and isinstance(dados["analise_temporal"], dict):
                return cls.model_validate(dados["analise_temporal"])
            if isinstance(dados, dict):
                return cls.model_validate(dados)
        except (yaml.YAMLError, OSError, ValueError):
            return cls()
        return cls()


class ConfigAnaliseTemporal(BaseModel):
    analise_temporal: ConfigAnaliseTemporalInfo = Field(default_factory=ConfigAnaliseTemporalInfo)
