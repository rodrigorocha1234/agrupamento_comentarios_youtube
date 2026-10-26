"""Modelos de cadastro formal e metadados de domínio do projeto."""

from pydantic import BaseModel, Field


class ConfigMapeamentoOrigem(BaseModel):
    """Mapeamento de chaves e campos de dados da fonte externa."""

    tipo_fonte: str = "api_rest"
    identificador_primario: str = "id"
    identificador_contexto: str = "contexto_id"
    campo_texto_consulta: str = "texto"
    campos_numericos_padrao: list[str] = Field(default_factory=list)
    campos_temporais: list[str] = Field(default_factory=list)


class ConfigInfraestruturaProjeto(BaseModel):
    """Parâmetros de infraestrutura específicos do projeto."""

    datalake_bucket: str = "datalake-clustering"
    mlflow_experimento: str = "experimento_clustering"


class ConfigCadastroProjetoInfo(BaseModel):
    """Cadastro formal e metadados de domínio do projeto de agrupamento."""

    id_projeto: str = "projeto_agrupamento"
    nome: str = "Agrupamento Não Supervisionado"
    descricao: str = "Pipeline reutilizável de clustering não supervisionado"
    versao: str = "1.0.0"
    dominio: str = "geral"
    entidade: str = "amostra"
    mapeamento_origem: ConfigMapeamentoOrigem = Field(default_factory=ConfigMapeamentoOrigem)
    infraestrutura: ConfigInfraestruturaProjeto = Field(default_factory=ConfigInfraestruturaProjeto)


class ConfigCadastroProjeto(BaseModel):
    """Container para o arquivo cadastro_projeto.yaml."""

    cadastro_projeto: ConfigCadastroProjetoInfo = Field(default_factory=ConfigCadastroProjetoInfo)
