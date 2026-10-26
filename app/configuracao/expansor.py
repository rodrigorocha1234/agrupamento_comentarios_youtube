"""Utilitário de interpolação e expansão segura de variáveis de ambiente em strings YAML."""

import os
import re
from typing import Final

PADRAO_VARIAVEL_AMBIENTE: Final[re.Pattern[str]] = re.compile(
    r"\$\{([A-Za-z0-9_]+)(?::-([^}]*))?\}"
)


def expandir_variaveis_ambiente(conteudo: str) -> str:
    """Substitui padrões ${VAR} ou ${VAR:-default} pelos valores de ambiente correspondentes."""

    def substituir(match: re.Match[str]) -> str:
        nome_var = match.group(1)
        valor_padrao = match.group(2) if match.group(2) is not None else ""
        return os.environ.get(nome_var, valor_padrao)

    return PADRAO_VARIAVEL_AMBIENTE.sub(substituir, conteudo)
