"""Construtor (GoF Builder) para carregamento, expansão e validação modular de arquivos YAML."""

from pathlib import Path
from typing import Final

import yaml
from pydantic import BaseModel

from app.configuracao.analises import ConfigAnalises
from app.configuracao.api import ConfigAPI
from app.configuracao.atributos import ConfigAtributos
from app.configuracao.avaliacao import ConfigAvaliacao
from app.configuracao.cadastro import ConfigCadastroProjeto
from app.configuracao.clustering import ConfigClustering
from app.configuracao.datalake import ConfigDatalake
from app.configuracao.expansor import expandir_variaveis_ambiente
from app.configuracao.fonte_dados import ConfigFonteDados
from app.configuracao.mlflow import ConfigMLflow
from app.configuracao.observabilidade import ConfigObservabilidade
from app.configuracao.pln import ConfigPLN
from app.configuracao.preprocessamento import ConfigPreprocessamento
from app.configuracao.processamento import ConfigProcessamento
from app.configuracao.projeto import ConfigProjeto
from app.configuracao.temporal import ConfigAnaliseTemporal
from app.excecoes import ErroConfiguracao


class ConstrutorConfiguracao:
    """Implementa o padrão GoF Builder para montagem e parsing isolado de configurações YAML."""

    ARQUIVOS_OBRIGATORIOS: Final[dict[str, type[BaseModel]]] = {
        "projeto.yaml": ConfigProjeto,
        "fonte_dados.yaml": ConfigFonteDados,
        "processamento.yaml": ConfigProcessamento,
        "datalake.yaml": ConfigDatalake,
        "atributos.yaml": ConfigAtributos,
        "preprocessamento.yaml": ConfigPreprocessamento,
        "clustering.yaml": ConfigClustering,
        "avaliacao.yaml": ConfigAvaliacao,
        "mlflow.yaml": ConfigMLflow,
        "observabilidade.yaml": ConfigObservabilidade,
        "analises.yaml": ConfigAnalises,
        "api.yaml": ConfigAPI,
        "regras_negocio.yaml": BaseModel,  # Carregado via ConfigRegrasNegocio dinamicamente
    }

    @classmethod
    def carregar_arquivo_yaml[T: BaseModel](
        cls,
        caminho: Path,
        modelo_classe: type[T],
        obrigatorio: bool = True,
        instancia_padrao: T | None = None,
    ) -> T:
        """Lê um arquivo YAML único, expande variáveis de ambiente e valida o modelo Pydantic."""
        if not caminho.is_file():
            if obrigatorio:
                raise ErroConfiguracao(f"Arquivo obrigatório de configuração ausente: {caminho}")
            return instancia_padrao if instancia_padrao is not None else modelo_classe()

        try:
            conteudo_bruto = caminho.read_text(encoding="utf-8")
            conteudo_expandido = expandir_variaveis_ambiente(conteudo_bruto)
            dados_dict = yaml.safe_load(conteudo_expandido) or {}
            if not isinstance(dados_dict, dict):
                raise ErroConfiguracao(f"Formato YAML inválido em {caminho.name}: esperado dicionário.")
            return modelo_classe.model_validate(dados_dict)
        except yaml.YAMLError as exc:
            raise ErroConfiguracao(f"Erro de sintaxe YAML em {caminho.name}: {exc}") from exc
        except Exception as exc:
            if isinstance(exc, ErroConfiguracao):
                raise
            raise ErroConfiguracao(f"Falha de validação em {caminho.name}: {exc}") from exc

    @classmethod
    def construir_valores(cls, caminho_diretorio: Path | str) -> dict[str, BaseModel]:
        """Carrega todos os módulos de configuração a partir do diretório fornecido."""
        from app.configuracao.regras_negocio import ConfigRegrasNegocio

        dir_path = Path(caminho_diretorio)
        if not dir_path.is_dir():
            raise ErroConfiguracao(f"Diretório de configuração não encontrado: {dir_path}")

        valores: dict[str, BaseModel] = {}

        # Módulos opcionais
        valores["cadastro_projeto"] = cls.carregar_arquivo_yaml(
            dir_path / "cadastro_projeto.yaml",
            ConfigCadastroProjeto,
            obrigatorio=False,
            instancia_padrao=ConfigCadastroProjeto(),
        )
        valores["pln"] = cls.carregar_arquivo_yaml(
            dir_path / "pln.yaml",
            ConfigPLN,
            obrigatorio=False,
            instancia_padrao=ConfigPLN(),
        )
        valores["analise_temporal"] = cls.carregar_arquivo_yaml(
            dir_path / "analise_temporal.yaml",
            ConfigAnaliseTemporal,
            obrigatorio=False,
            instancia_padrao=ConfigAnaliseTemporal(),
        )

        # Módulos obrigatórios
        mapa_obrigatorios: dict[str, type[BaseModel]] = {
            "projeto.yaml": ConfigProjeto,
            "fonte_dados.yaml": ConfigFonteDados,
            "processamento.yaml": ConfigProcessamento,
            "datalake.yaml": ConfigDatalake,
            "atributos.yaml": ConfigAtributos,
            "preprocessamento.yaml": ConfigPreprocessamento,
            "clustering.yaml": ConfigClustering,
            "avaliacao.yaml": ConfigAvaliacao,
            "mlflow.yaml": ConfigMLflow,
            "observabilidade.yaml": ConfigObservabilidade,
            "analises.yaml": ConfigAnalises,
            "api.yaml": ConfigAPI,
            "regras_negocio.yaml": ConfigRegrasNegocio,
        }

        for nome_arquivo, modelo_classe in mapa_obrigatorios.items():
            chave = nome_arquivo.removesuffix(".yaml")
            valores[chave] = cls.carregar_arquivo_yaml(
                dir_path / nome_arquivo,
                modelo_classe,
                obrigatorio=True,
            )

        return valores
