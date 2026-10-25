# Python e qualidade

- Python 3.12+.
- Usar tipagem estrita e contratos explícitos.
- Não usar `Any`, `typing.Any` ou `from typing import *`.
- Usar `Protocol`, `TypeVar`, `Generic`, `Literal`, `Final`, `Self`, `@final`, `@override` e `@runtime_checkable` quando agregarem clareza real.
- Identificadores próprios em português; respeitar nomes especiais exigidos pelo ecossistema.
- Evitar nomes que sombreiem módulos/bibliotecas como `logging`, `json`, `pandas`, `mlflow` ou `sklearn`.
- Um arquivo deve ter uma responsabilidade principal e, quando aplicável, uma classe principal.
- Aplicar SOLID, composição, exceções de domínio em português, pytest e verificação estática estrita.
- Preferir operações vetorizadas em vez de loops Python sobre linhas de DataFrame.
