"""Fábrica (Factory) para resolução e instanciação desacoplada de fontes de dados."""

import os

from app.conf_yaml import (
    ConfigAPIRestInfo,
    ConfigBancoDadosInfo,
    ConfigFonteDados,
)
from app.contratos.fonte_dados import ProtocoloFonteDados
from app.excecoes import ErroConfiguracao
from app.ingestao_fontes.adaptadores.adaptador_api_rest import AdaptadorAPIRest
from app.ingestao_fontes.adaptadores.adaptador_banco_dados import AdaptadorBancoDados
from app.ingestao_fontes.adaptadores.adaptador_steam import AdaptadorSteam
from app.ingestao_fontes.cliente_http_resiliente import ClienteHTTPResiliente


class FabricaFontes:
    """Instancia adaptadores concretos de fontes de dados aderentes a ProtocoloFonteDados."""

    @staticmethod
    def criar_fonte(
        config_fonte: ConfigFonteDados,
        cliente_http: ClienteHTTPResiliente | None = None,
    ) -> ProtocoloFonteDados:
        """Resolve a estratégia de ingestão baseada na configuração YAML.

        Args:
            config_fonte: Modelo validado do arquivo fonte_dados.yaml.
            cliente_http: Cliente HTTP compartilhado ou None para criar um novo.

        Retorna:
            Instância que implementa ProtocoloFonteDados.
        """
        tipo_fonte = config_fonte.fonte.tipo.lower().strip()

        # Resolução de secret/API key do ambiente se aplicável
        headers: dict[str, str] = {}
        var_segredo = config_fonte.fonte.segredo.variavel_ambiente
        if var_segredo:
            token = os.environ.get(var_segredo)
            if token:
                headers["Authorization"] = f"Bearer {token}"
                headers["x-api-key"] = token

        if tipo_fonte in ("steam", "steam_api", "steam_reviews"):
            cliente = cliente_http or ClienteHTTPResiliente(
                timeout_segundos=float(config_fonte.fonte.timeout_segundos),
                tentativas_maximas=config_fonte.fonte.tentativas_maximas,
                espera_base_segundos=float(config_fonte.fonte.espera_base_segundos),
                headers_padrao=headers,
            )
            parametros = config_fonte.parametros_api.model_dump()
            return AdaptadorSteam(
                cliente_http=cliente,
                endpoint_base=config_fonte.fonte.endpoint or "https://store.steampowered.com/appreviews/{appid}",
                parametros_adicionais=parametros,
            )

        if tipo_fonte in ("banco_dados", "sql", "postgres", "sqlite"):
            info_banco = config_fonte.fonte.banco_dados or ConfigBancoDadosInfo()
            dsn = info_banco.dsn or os.environ.get("DATABASE_URL", "sqlite:///:memory:")
            tabela_ou_consulta = info_banco.consulta_ou_tabela or "reviews"
            coluna_chave = info_banco.coluna_chave or "id"
            return AdaptadorBancoDados(
                dsn=dsn,
                tabela_ou_consulta=tabela_ou_consulta,
                coluna_chave=coluna_chave,
            )

        if tipo_fonte in ("api_rest", "rest", "http"):
            cliente = cliente_http or ClienteHTTPResiliente(
                timeout_segundos=float(config_fonte.fonte.timeout_segundos),
                tentativas_maximas=config_fonte.fonte.tentativas_maximas,
                espera_base_segundos=float(config_fonte.fonte.espera_base_segundos),
                headers_padrao=headers,
            )
            info_api = config_fonte.fonte.api_rest or ConfigAPIRestInfo()
            headers_api = dict(headers)
            headers_api.update(info_api.headers)
            endpoint = info_api.endpoint or config_fonte.fonte.endpoint or ""
            return AdaptadorAPIRest(
                cliente_http=cliente,
                endpoint=endpoint,
                metodo=info_api.metodo,
                parametro_paginacao=info_api.parametro_paginacao,
                headers=headers_api,
            )

        raise ErroConfiguracao(
            f"Tipo de fonte de dados '{tipo_fonte}' não suportado. "
            f"Tipos autorizados: 'steam_api', 'banco_dados', 'api_rest'."
        )
