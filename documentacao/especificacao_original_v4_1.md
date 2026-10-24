Regras gerais de Python do projeto

- Utilizar **Python 3.12+** como versão mínima oficial do projeto.

- Usar **tipagem forte e explícita** em todo código próprio.

- É proibido utilizar:

```python
Any
typing.Any
```

- Não utilizar `Any` direta ou indiretamente como forma de contornar problemas de tipagem.

- Preferir recursos modernos de tipagem quando houver necessidade semântica real:

```python
Protocol
TypeVar
Generic
Self
Literal
Final
@final
ClassVar
TypeAlias
@override
@overload
@runtime_checkable
```

- Em Python 3.12+, utilizar:

```python
from typing import override
```

- Não utilizar:

```python
from typing import *
```

- Importar somente os recursos efetivamente utilizados.

---

## Nomenclatura

- Nomes próprios do projeto deverão ser escritos em **português**.

Isso se aplica a:

```text
classes
métodos
funções
atributos
enums
protocolos
serviços
adapters
factories
repositórios
exceções
pacotes
módulos
```

- Bibliotecas externas deverão manter seus nomes oficiais.

Exemplo:

```python
from sklearn.pipeline import Pipeline
```

---

## Módulos e pacotes

- Todo módulo ou pacote Python próprio deverá possuir **exatamente duas palavras**, separadas por `_`.

Exemplos:

```text
registro_logs.py
contrato_dados.py
coletor_metricas.py
configuracao_logs.py
modelos_regressao/
motor_sklearn/
gestao_dados/
```

- Não utilizar hífen em módulos ou pacotes importáveis.

Evitar:

```text
registro-logs.py
```

- Exceções são permitidas quando o Python ou alguma ferramenta exigir nomes específicos:

```text
__init__.py
__main__.py
conftest.py
```

---

## Não sombrear bibliotecas

Não criar módulos ou pacotes próprios com nomes iguais aos da biblioteca padrão ou dependências externas.

Evitar:

```text
logging.py
json.py
typing.py
pathlib.py
asyncio.py
enum.py
dataclasses.py
statistics.py
random.py
collections.py
itertools.py
functools.py

pandas.py
numpy.py
sklearn.py
mlflow.py
requests.py
pyspark.py
```

---

## Métodos

- Métodos deverão representar ações claras.

Preferir:

```python
carregar_dados()
validar_schema()
separar_holdout()
treinar_modelo()
calcular_metricas()
registrar_resultado()
verificar_drift()
selecionar_modelo()
```

- Evitar nomes excessivamente genéricos:

```python
run()
execute()
process()
handle()
```

quando existir uma ação de domínio mais clara.

---

# Encapsulamento

O projeto deverá utilizar encapsulamento de forma consistente.

Em Python, os níveis de acesso são representados principalmente por convenções de nomenclatura.

## Atributos públicos

Atributos públicos podem ser acessados diretamente quando fizer sentido expô-los como parte da interface da classe.

Exemplo:

```python
class ResultadoModelo:
    def __init__(self, nome_modelo: str) -> None:
        self.nome_modelo = nome_modelo
```

Usar atributos públicos somente quando seu acesso direto não violar invariantes ou regras de domínio.

---

## Atributos protegidos

Atributos destinados ao uso interno da classe e de subclasses deverão utilizar um `_` inicial.

Exemplo:

```python
class ModeloBase:
    def __init__(self, nome_modelo: str) -> None:
        self._nome_modelo = nome_modelo
```

A convenção:

```text
_nome
```

significa:

```text
uso interno/protegido por convenção
```

Não significa proteção real em runtime.

---

## Atributos privados

Quando houver necessidade real de evitar colisões em subclasses ou proteger detalhes internos de implementação, utilizar `__`.

Exemplo:

```python
class GerenciadorModelo:
    def __init__(self, versao: str) -> None:
        self.__versao = versao
```

Python aplica *name mangling*, transformando internamente o atributo.

Entretanto, isso não representa privacidade absoluta como em Java ou C#.

Utilizar atributos privados somente quando houver justificativa de encapsulamento.

Não transformar todos os atributos em privados indiscriminadamente.

---

# Métodos públicos

Métodos públicos representam operações oferecidas oficialmente pela classe.

Exemplo:

```python
class TreinadorModelo:
    def treinar_modelo(self) -> None: ...
```

São a interface principal utilizada por outros componentes.

---

# Métodos protegidos

Métodos auxiliares destinados à própria classe ou subclasses deverão utilizar `_`.

Exemplo:

```python
class TreinadorBase:
    def treinar_modelo(self) -> None:
        dados = self._preparar_dados()
        self._ajustar_modelo(dados)

    def _preparar_dados(self) -> pd.DataFrame: ...

    def _ajustar_modelo(
        self,
        dados: pd.DataFrame,
    ) -> None: ...
```

---

# Métodos privados

Métodos estritamente internos poderão utilizar `__`.

Exemplo:

```python
class ValidadorDados:
    def validar_dados(self) -> bool:
        return self.__validar_regras_internas()

    def __validar_regras_internas(self) -> bool: ...
```

Utilizar apenas quando houver necessidade real.

Preferir métodos protegidos para extensibilidade quando subclasses puderem precisar sobrescrever o comportamento.

---

# Properties

Quando o acesso a um atributo exigir:

```text
validação
transformação
controle
cálculo
proteção de invariantes
```

utilizar `@property`.

Exemplo:

```python
class ConfiguracaoModelo:
    def __init__(self, nome_modelo: str) -> None:
        self._nome_modelo = nome_modelo

    @property
    def nome_modelo(self) -> str:
        return self._nome_modelo
```

Quando houver alteração controlada:

```python
class ConfiguracaoModelo:
    def __init__(self, limite: float) -> None:
        self._limite = limite

    @property
    def limite(self) -> float:
        return self._limite

    @limite.setter
    def limite(self, valor: float) -> None:
        if valor < 0:
            raise ValueError("O limite não pode ser negativo.")

        self._limite = valor
```

Não criar getters e setters artificiais no estilo:

```python
get_nome()
set_nome()
```

quando uma `property` representar melhor o contrato.

---

# Uma classe principal por arquivo

Preferir:

```text
uma classe principal por arquivo .py
```

Exceções podem existir para:

```text
dataclasses pequenas
Enums relacionados
estruturas fortemente coesas
```

Evitar:

```text
God Classes
classes gigantes
arquivos com dezenas de responsabilidades
```

---

# SOLID

Aplicar de forma prática:

```text
Single Responsibility Principle
Open/Closed Principle
Liskov Substitution Principle
Interface Segregation Principle
Dependency Inversion Principle
```

Não criar interfaces, factories ou abstrações apenas para demonstrar padrões de projeto.

Toda abstração deverá resolver um problema concreto.

---

# Composição e herança

Preferir:

```text
composição
```

quando não houver relação clara de:

```text
"é um"
```

Utilizar herança quando existir:

```text
contrato compartilhado
relação semântica apropriada
Template Method
comportamento comum legítimo
```

Evitar hierarquias profundas.

---

# Classes abstratas

Quando herança fizer parte do design, utilizar:

```python
from abc import ABC, abstractmethod
```

Exemplo:

```python
class EstrategiaModelo(ABC):
    @abstractmethod
    def criar_modelo(self) -> RegressorMixin: ...
```

Não utilizar permanentemente:

```python
raise NotImplementedError
```

como substituto de `@abstractmethod`.

---

# @override

Sempre utilizar `@override` quando um método sobrescrever explicitamente um método da classe base.

Exemplo:

```python
from typing import override


class ModeloRidge(EstrategiaModelo):
    @override
    def criar_modelo(self) -> Ridge: ...
```

Isso ajuda o type checker a detectar mudanças incompatíveis.

---

# @final

Utilizar o decorador `@final` para indicar classes que não devem ser herdadas e métodos que não devem ser sobrescritos por subclasses.

Em Python 3.12+, importar diretamente de `typing`:

```python
from typing import final
```

## Classes finais

Aplicar `@final` quando uma classe possuir uma implementação completa e não fizer sentido permitir sua especialização por herança.

Exemplo:

```python
from typing import final


@final
class CalculadoraMetricas:
    def calcular_rmse(
        self,
        valores_reais: list[float],
        valores_previstos: list[float],
    ) -> float: ...
```

Regras:

- Utilizar `@final` quando a classe não fizer parte de uma hierarquia extensível.
- Não aplicar `@final` em classes abstratas destinadas à herança.
- Não aplicar indiscriminadamente em todas as classes concretas.
- Preferir composição quando for necessário reutilizar funcionalidades de uma classe final.

## Métodos finais

Aplicar `@final` quando um método herdado não puder ter seu comportamento alterado por subclasses.

Exemplo:

```python
from typing import final, override


class TreinadorBase:
    def validar_modelo(self) -> bool: ...


class TreinadorRidge(TreinadorBase):
    @final
    @override
    def validar_modelo(self) -> bool:
        return True
```

Nesse exemplo, subclasses de `TreinadorRidge` não deverão sobrescrever `validar_modelo()`.

## Integração com `@override`

Quando um método sobrescrever outro da classe base e também precisar impedir novas sobrescritas, utilizar ambos os decoradores:

```python
@final
@override
def validar_modelo(self) -> bool: ...
```

## Validação estática

O decorador `@final` é utilizado principalmente por verificadores estáticos de tipos, como Pyright e mypy.

**Importante:** `@final` não impede herança ou sobrescrita durante a execução normal do Python. A restrição deve ser verificada pelo type checker configurado em modo `strict`.

## Regra arquitetural

Utilizar os decoradores conforme a responsabilidade:

| Decorador | Aplicação |
|---|---|
| `@final` | Impedir herança de classes ou sobrescrita de métodos no contrato estático. |
| `@override` | Declarar explicitamente a sobrescrita de um método herdado. |
| `@abstractmethod` | Exigir implementação de métodos em subclasses concretas. |
| `@property` | Controlar acesso, validação ou transformação de atributos. |
| `@staticmethod` | Definir operações que não dependem do estado da instância ou da classe. |
| `@classmethod` | Definir operações relacionadas à classe, incluindo métodos de fábrica. |

**Princípio:** utilizar `@final` para proteger contratos arquiteturais que não devem ser estendidos, sem prejudicar a extensibilidade legítima do projeto.

---

# Exceções

Criar exceções próprias em português.

Exemplo:

```python
class ErroCarregamentoDados(RuntimeError):
    pass
```

Preservar a exceção original:

```python
try:
    ...
except OSError as erro:
    raise ErroCarregamentoDados("Não foi possível carregar os dados.") from erro
```

Evitar:

```python
except Exception:
    pass
```

Nunca ignorar erros silenciosamente.

Evitar capturar `Exception` de forma indiscriminada.

---

# Configuração

Toda configuração variável deverá vir de arquivos YAML.

Evitar hardcoded de:

```text
parâmetros
hiperparâmetros
thresholds
features
target
modelos
scalers
encoders
tuning
validação cruzada
drift
métricas
infraestrutura
regras de negócio
```

O código Python deverá implementar comportamento.

O YAML deverá definir configuração.

---

# Pandas

Priorizar processamento vetorizado.

Evitar:

```python
iterrows()
itertuples()
apply(axis=1)
```

quando houver solução vetorizada.

Evitar:

```text
for sobre linhas
for sobre índices
atribuição célula a célula
transformação manual registro por registro
```

A ordem preferencial é:

```text
operações vetorizadas
↓
Series.str / Series.dt / Series.cat
↓
assign / where / mask
↓
numpy.where / numpy.select
↓
groupby.agg / groupby.transform
↓
merge / join
↓
isin / between
↓
fillna / replace / clip
```

Exemplo incorreto:

```python
for indice, linha in dataframe.iterrows():
    dataframe.loc[indice, "preco_m2"] = linha["Valor_da_Venda"] / linha["Metragem"]
```

Preferir:

```python
dataframe = dataframe.assign(
    preco_m2=dataframe["Valor_da_Venda"].div(dataframe["Metragem"])
)
```

---

# Polars

Utilizar `polars` quando o processamento tabular se beneficiar de execução eficiente, avaliação lazy, paralelismo ou redução do consumo de memória.

A escolha entre `pandas` e `polars` deverá considerar o volume dos dados, as operações necessárias, a compatibilidade com as bibliotecas do projeto e a clareza do código. Não migrar automaticamente um fluxo para Polars sem benefício técnico demonstrável.

## Regras de uso

- Manter os nomes oficiais da biblioteca externa: `polars`, `pl.DataFrame`, `pl.LazyFrame` e demais APIs.
- Preferir operações nativas e expressões Polars a loops Python sobre linhas.
- Preferir `select`, `with_columns`, `filter`, `group_by`, `agg`, `join`, `when/then/otherwise` e expressões `pl.col(...)` quando forem adequadas.
- Preferir `LazyFrame` e a cadeia de operações lazy para fluxos tabulares extensos, permitindo ao otimizador planejar a execução.
- Utilizar `collect()` somente no ponto em que seja necessário materializar o resultado de uma consulta lazy.
- Usar `scan_csv`, `scan_parquet` ou outras funções de leitura lazy compatíveis com a fonte quando isso evitar carregar os dados antecipadamente.
- Evitar converter repetidamente entre `pandas.DataFrame`, `polars.DataFrame`, listas e dicionários sem necessidade.
- Não presumir que uma operação lazy será sempre mais rápida; medir o desempenho no fluxo real.
- Verificar a compatibilidade de cada modelo, transformador e ferramenta de Machine Learning antes de escolher Polars como formato de entrada.
- Não usar Polars como justificativa para ignorar validação de schema, tipagem, qualidade dos dados ou prevenção de data leakage.

## Exemplo vetorizado

```python
import polars as pl

dados = pl.DataFrame(
    {
        "Valor": [250_000.0, 320_000.0, 410_000.0],
        "Metragem": [70.0, 80.0, 100.0],
    }
)

dados = dados.with_columns((pl.col("Valor") / pl.col("Metragem")).alias("preco_m2"))
```

## Exemplo com avaliação lazy

```python
import polars as pl

consulta = (
    pl.scan_parquet("dados/imoveis.parquet")
    .filter(pl.col("Metragem") > 0)
    .with_columns((pl.col("Valor") / pl.col("Metragem")).alias("preco_m2"))
    .group_by("Bairro")
    .agg(
        pl.col("Valor").median().alias("mediana_valor"),
        pl.col("preco_m2").mean().alias("media_preco_m2"),
    )
)

resultado = consulta.collect()
```

## Integração com Pandas e Machine Learning

- Escolher um formato de dados principal por etapa do pipeline, evitando conversões desnecessárias.
- Converter para Pandas apenas quando uma biblioteca ou API exigir esse formato, ou quando a conversão tiver sido validada como apropriada.
- Confirmar que a conversão preserva tipos, valores ausentes, categorias, ordem das colunas e semântica dos dados.
- Ajustar imputadores, encoders, scalers e demais transformadores exclusivamente nos dados de treino de cada fold.
- Em validação cruzada, construir e ajustar o pré-processamento dentro do pipeline de cada fold para evitar vazamento de dados.
- Testar resultados e métricas após qualquer mudança de Pandas para Polars; não assumir equivalência apenas porque as operações parecem semelhantes.

---

# Loops Python

Loops não são proibidos no projeto.

Podem ser utilizados para:

```text
modelos
folds
strategies
experimentos
arquivos
configurações
objetos
componentes de infraestrutura
```

A restrição aplica-se principalmente ao processamento tabular linha a linha no pandas quando houver solução vetorizada.

---

# map

`map()` poderá ser utilizado quando representar de forma clara uma transformação funcional.

Exemplo:

```python
nomes_normalizados = list(map(str.lower, nomes_modelos))
```

Preferir `map()` principalmente quando:

```text
a transformação já existe como função
não há necessidade de lógica complexa
a intenção permanecer clara
```

Não utilizar `map()` apenas para evitar uma compreensão mais legível.

---

# filter

`filter()` poderá ser utilizado para filtrar iteráveis quando houver um predicado claro.

Exemplo:

```python
modelos_ativos = list(
    filter(
        verificar_modelo_ativo,
        configuracoes_modelos,
    )
)
```

Para estruturas pandas, continuar priorizando:

```python
loc
query
isin
between
where
mask
```

em vez de converter dados para listas e usar `filter()`.

---

# reduce

Quando for necessário realizar uma redução funcional, utilizar:

```python
from functools import reduce
```

Exemplo:

```python
resultado = reduce(
    combinar_resultados,
    resultados_modelos,
)
```

Usar `reduce()` somente quando representar claramente uma composição/redução sucessiva.

Para operações simples, preferir funções nativas:

```python
sum()
min()
max()
all()
any()
```

---

# zip

Utilizar `zip()` para percorrer iteráveis relacionados em paralelo.

Exemplo:

```python
for nome_modelo, resultado in zip(
    nomes_modelos,
    resultados,
    strict=True,
):
    ...
```

Em Python moderno, quando os iteráveis deveriam obrigatoriamente possuir o mesmo tamanho, preferir:

```python
zip(..., strict=True)
```

Isso permite detectar inconsistências silenciosas.

---

# zip_longest

Quando os iteráveis puderem possuir comprimentos diferentes e isso for parte intencional da regra, utilizar:

```python
from itertools import zip_longest
```

Exemplo:

```python
for esperado, obtido in zip_longest(
    valores_esperados,
    valores_obtidos,
    fillvalue=None,
):
    ...
```

Não utilizar `zip_longest()` quando diferenças de tamanho representarem erro. Nesse caso, preferir:

```python
zip(..., strict=True)
```

---

# itertools

Preferir ferramentas da biblioteca padrão quando reduzirem código manual e deixarem a intenção clara.

Recursos úteis incluem:

```python
chain
combinations
combinations_with_replacement
permutations
product
islice
takewhile
dropwhile
groupby
cycle
repeat
accumulate
pairwise
zip_longest
```

Exemplos de aplicação no projeto:

```text
combinações de modelos
combinações de parâmetros
encadeamento de coleções
processamento lazy
comparações entre modelos
criação de pares
geração de produtos cartesianos
```

Exemplo:

```python
from itertools import combinations

pares_modelos = combinations(
    nomes_modelos,
    2,
)
```

Evitar materializar iteradores em listas sem necessidade.

---

# Iteradores e avaliação lazy

Quando possível, preservar processamento lazy.

Preferir:

```python
iterador = map(...)
```

quando não for necessário criar imediatamente uma lista.

Converter para:

```python
list(...)
tuple(...)
```

somente quando o consumidor exigir materialização.

Isso é especialmente importante para conjuntos grandes de dados que não estejam sendo manipulados por pandas.

---

# collections

Utilizar estruturas especializadas de `collections` quando representarem melhor o problema.

Recursos recomendados:

```python
Counter
defaultdict
deque
ChainMap
namedtuple
```

Usar somente quando houver vantagem sobre estruturas básicas.

---

# Counter

Utilizar:

```python
from collections import Counter
```

para contagem de elementos em iteráveis Python.

Exemplo:

```python
frequencias = Counter(nomes_modelos)
```

Para colunas pandas, normalmente preferir:

```python
serie.value_counts()
```

---

# defaultdict

Utilizar:

```python
from collections import defaultdict
```

quando houver necessidade legítima de valores padrão durante agrupamento ou acumulação.

Exemplo:

```python
resultados: defaultdict[str, list[float]] = defaultdict(list)
```

Não utilizar quando `dict` normal oferecer contrato mais explícito.

---

# deque

Utilizar:

```python
from collections import deque
```

quando houver necessidade de:

```text
fila
pilha
buffer
janela deslizante
inserções e remoções eficientes nas extremidades
```

Evitar `list.pop(0)` para implementação frequente de filas.

---

# ChainMap

Utilizar:

```python
from collections import ChainMap
```

quando for necessário representar múltiplas camadas de configuração sem copiar todos os dicionários.

Possíveis casos:

```text
configuração padrão
configuração de ambiente
configuração específica do modelo
override de execução
```

Utilizar apenas se o comportamento de precedência estiver claramente documentado.

---

# namedtuple

`namedtuple` poderá ser utilizado para estruturas leves e imutáveis.

Entretanto, quando houver regras de domínio, validação, tipos mais ricos ou comportamento associado, preferir:

```python
@dataclass(frozen=True)
```

ou uma classe de domínio dedicada.

---

# Compreensões

Compreensões são permitidas quando simples e legíveis:

```python
modelos_ativos = [nome for nome in nomes_modelos if nome in configuracoes]
```

Evitar compreensões profundamente aninhadas ou contendo múltiplas regras de negócio.

Quando a lógica crescer, extrair para uma função com nome semântico.

---

# Generators e iterators

Utilizar `generators` e `iterators` para percorrer sequências de forma incremental, especialmente quando não for necessário manter todos os elementos simultaneamente em memória.

## Iterators

Um iterador é um objeto que fornece elementos um de cada vez e mantém seu estado de iteração. Em geral, pode ser consumido uma única vez.

- Preferir `iter()` e `next()` quando o controle explícito da iteração for necessário.
- Não presumir que um iterador possa ser reutilizado depois de consumido.
- Materializar com `list()` ou `tuple()` somente quando o contrato do consumidor exigir uma coleção concreta ou múltiplas passagens.
- Tratar o fim normal da iteração por meio do protocolo de iteração; evitar tratar `StopIteration` indiscriminadamente fora desse contexto.
- Documentar quando uma função retorna um iterador consumível uma única vez.

Exemplo:

```python
nomes_modelos = iter(("Ridge", "RandomForest", "HistGradientBoosting"))

primeiro_modelo = next(nomes_modelos)
```

## Generators

Um generator é uma forma de criar um iterador, normalmente usando uma função com `yield` ou uma generator expression.

- Preferir generators quando os elementos puderem ser produzidos sob demanda.
- Usar `yield` para emitir resultados incrementalmente sem construir uma coleção completa.
- Evitar guardar em memória todos os resultados de grandes sequências quando o consumidor puder processá-los um por vez.
- Não usar generators quando for necessário acessar elementos por índice, percorrer a sequência várias vezes ou disponibilizar uma coleção materializada.
- Manter funções geradoras simples, com responsabilidade clara e tipos de retorno explícitos, como `Iterator[ResultadoModelo]` ou `Generator[ResultadoModelo, None, None]`, conforme o contrato necessário.
- Não confundir avaliação lazy com execução paralela: um generator, por si só, não executa trabalho em paralelo.

Exemplo:

```python
from collections.abc import Iterator


def gerar_nomes_modelos() -> Iterator[str]:
    yield "Ridge"
    yield "RandomForest"
    yield "HistGradientBoosting"
```

## Aplicações no projeto

Generators e iterators podem ser úteis para:

```text
leitura incremental de registros
processamento de arquivos grandes
produção de resultados de experimentos
encadeamento de etapas compatíveis com iteráveis
avaliação sob demanda de combinações
redução do uso de memória fora de operações tabulares vetorizadas
```

Não utilizar generators para substituir operações vetorizadas de Pandas ou expressões nativas de Polars quando estas forem mais adequadas ao processamento tabular.

---

# Generator expressions

Preferir generator expressions quando não houver necessidade de materializar todos os elementos.

Exemplo:

```python
quantidade_ativos = sum(1 for modelo in modelos if modelo.ativo)
```

---

# enumerate

Quando for necessário índice e elemento ao mesmo tempo, utilizar:

```python
for indice, modelo in enumerate(modelos):
    ...
```

em vez de:

```python
for indice in range(len(modelos)):
    modelo = modelos[indice]
```

Essa regra não autoriza processamento linha a linha de `DataFrame`.

---

# Padrões de projeto

Utilizar quando resolverem problemas concretos:

```text
Strategy
Factory
Adapter
Observer
Repository
Facade
```

Outros padrões poderão ser utilizados quando tecnicamente justificados.

Não adicionar padrões apenas para aumentar a quantidade de abstrações do projeto.

---

# Qualidade arquitetural

O código deverá ser:

```text
desacoplado
testável
reutilizável
coeso
extensível
fortemente tipado
observável
configurável
```

Separar claramente:

```text
domínio
infraestrutura
configuração
persistência
orquestração
Machine Learning
observabilidade
regras de negócio
```

---

# Testes

Utilizar:

```text
pytest
```

Criar:

```text
testes unitários
testes de integração
testes de contrato
testes parametrizados
```

Utilizar quando apropriado:

```python
@pytest.fixture
@pytest.mark.parametrize
```

Mocks deverão ser utilizados principalmente para dependências externas e efeitos colaterais.

---

# Type checking

Configurar o type checker em modo:

```text
strict
```

Violações críticas de tipagem deverão falhar no CI.

O objetivo é detectar antecipadamente:

```text
tipos incompatíveis
retornos incorretos
parâmetros incorretos
atributos inexistentes
sobrescritas incompatíveis
uso indevido de Optional
```

---

# Regra de prioridade para código Python

Quando houver mais de uma solução possível, preferir nesta ordem:

```text
1. recurso nativo da linguagem
2. biblioteca padrão
3. operação vetorizada da biblioteca utilizada
4. recurso moderno e idiomático do pacote
5. abstração própria
6. implementação manual
```

Exemplo:

```text
sum()
```

é preferível a implementar manualmente um acumulador quando ambos resolvem exatamente o mesmo problema.

Da mesma forma:

```text
zip(..., strict=True)
itertools
collections
functools
```

devem ser preferidos a implementações manuais equivalentes quando aumentarem clareza, segurança e manutenção.

---

# Princípio geral

O projeto deve buscar código:

```text
Python moderno
+
tipagem forte
+
encapsulamento adequado
+
baixo acoplamento
+
alta coesão
+
configuração externa
+
processamento vetorizado
+
biblioteca padrão antes de reinventar soluções
+
testes automatizados
+
arquitetura extensível
```

# ESPECIFICAÇÃO CONSOLIDADA — STEAM REVIEWS CLUSTERING
## Versão 4.1 — plataforma extensível de agrupamento e análise de dados

## 1. Objetivo, escopo e restrições
Construir uma plataforma genérica de clustering não supervisionado, orientada por arquivos YAML, inicialmente aplicada a avaliações públicas da Steam. Na versão inicial, o texto das avaliações será retido somente para consulta humana e não participará de feature engineering, embeddings ou treinamento. Os atributos iniciais de treinamento serão `num_reviews`, `playtime_forever`, `playtime_last_two_weeks`, `playtime_at_review` e uma representação derivada de `last_played`. Todos serão parametrizáveis; nenhuma lista fixa de colunas deverá ser assumida pelo motor de ML. As reviews em idioma `brazilian` não comprovam residência brasileira.

A solução deverá reutilizar infraestrutura já ativa: antes de criar serviços, examinar o Docker Compose da raiz, dependências instaladas, volumes, redes, variáveis de ambiente e serviços existentes. Manter um Compose raiz; não criar serviços duplicados. Configurar integrações sem segredos no repositório. A implementação deverá seguir as regras gerais de Python presentes na primeira parte deste documento.

Objetivos de negócio: identificar perfis de jogadores que avaliam jogos, relacionar horas de jogo e características da avaliação, comparar jogos, perfis positivos/negativos, engajamento e evolução temporal quando habilitada. A granularidade padrão é review (`appid` + `recommendationid`), não jogador. Outras granularidades dependerão de estratégias de agregação próprias.

## 2. Princípios arquiteturais e regra de decisão sem if de domínio
Adotar separação: adaptadores de origem; staging transacional; Data Lake Bronze/Silver/Gold; qualidade; processamento tabular; engenharia de atributos; pré-processamento; clustering; avaliação/tuning; análise de negócio; persistência; apresentação; observabilidade. Classes de domínio não poderão importar tecnologia concreta de infraestrutura.

Para variações por origem, banco, motor de dados, transformador, algoritmo, framework, gráfico, dashboard, avaliação, política temporal e processamento de linguagem: preferir GoF Strategy + Factory/Abstract Factory + Adapter + Registry; composição e polimorfismo para despacho, com `Enum`/tipos validados nos limites. Para ausência opcional de funcionalidade, usar Null Object quando não mascarar configurações inválidas; para compor transformações, Composite/Pipeline; para notificação de MLflow, métricas e logs, Observer; para repositórios, Repository; para regras compostas, Specification/Composite ou Chain of Responsibility quando a semântica for sequencial; para orquestração, Facade. `Protocol`, `TypeVar` e `Generic` deverão ser usados onde oferecerem contratos verificáveis, sem `Any` no código próprio.

Não introduzir ramificações `if/elif` dependentes de nomes de tecnologias, algoritmos, fontes ou frameworks no núcleo de negócio. O registro de estratégias resolve a implementação; falha de chave desconhecida produz erro de configuração. Condicionais pontuais de validação, tratamento de erros, limites de repetição, comparação de valores ou controle de fluxo são permitidas quando melhorarem clareza e segurança. Nunca substituir uma condição trivial por um padrão artificial. Não executar strings de Python do YAML por `eval` ou `exec`.

## 3. Organização e contratos
Separar pacotes do domínio dos adaptadores e da infraestrutura; respeitar a regra de duas palavras por módulo/pacote e uma classe principal por arquivo. Introduzir contratos para `FonteDados[T]`, `RepositorioStaging[T]`, `MotorTabular[T]`, `TransformadorAtributos[T]`, `EstrategiaAgrupamento[T]`, `AvaliadorClusters[T]`, `PublicadorAnalitico[T]`, `RenderizadorGrafico[T]` e `ObservadorExecucao`. Os contratos deverão explicitar modelos de entrada e saída e não pressupor que Pandas e Polars compartilhem o mesmo tipo de DataFrame.

A classe `ConfYAML`, em `conf_yaml.py`, será fachada exclusiva de carregamento, validação e disponibilização de configurações imutáveis e tipadas. Classes consumidoras recebem a configuração específica por injeção de dependências; não devem reler arquivos. Utilizar Pydantic ou dataclasses com validação estrita, schema_version, defaults explícitos e detecção de chaves desconhecidas. Um validador de compatibilidade deve verificar configurações entre arquivos. Segredos devem vir de variáveis de ambiente ou gestor de segredos, nunca como valores fixos em YAML. Produzir hash do conjunto de YAMLs e versionar configurações utilizadas em cada execução.

## 4. Arquivos YAML separados por responsabilidade
Estrutura recomendada:
```
configuracoes/
  projeto.yaml
  fontes/steam_api.yaml
  infraestrutura/staging.yaml
  infraestrutura/datalake.yaml
  infraestrutura/mlflow.yaml
  infraestrutura/observabilidade.yaml
  processamento/motor_dados.yaml
  processamento/fluxos_incrementais.yaml
  processamento/selecao_colunas.yaml
  processamento/filtros_dados.yaml
  processamento/transformacao_atributos.yaml
  processamento/criacao_atributos.yaml
  machine_learning/atributos_modelo.yaml
  machine_learning/preprocessamento.yaml
  machine_learning/algoritmos.yaml
  machine_learning/otimizacao.yaml
  machine_learning/avaliacao.yaml
  machine_learning/persistencia.yaml
  analises/eda.yaml
  analises/clusters.yaml
  analises/negocio.yaml
  analises/temporal.yaml
  analises/visualizacoes.yaml
  extensoes/processamento_linguagem.yaml
```

A configuração `projeto.yaml` deverá ter `versao_schema`, projeto, modo de execução, seed, `processamento_linguagem_natural: false`, `analise_temporal: false` e opção extensível de novos domínios/tipos de análise via registrador de capacidades, não por cadeia de condicionais.

A configuração `steam_api.yaml` deverá modelar TODOS os parâmetros atualmente documentados no anexo, com enums corretos e validação: `key` (referência de segredo), `appid`, `filter`, `languages`, `day_range`, `cursor`, `review_type`, `purchase_type`, `num_per_page`, `filter_offtopic_activity`, `display_language`, `use_review_quality`, `date_range_start`, `date_range_end`, `date_range_exclude`, `playtime_min_hours`, `playtime_max_hours`, `primarily_steam_deck`, `hardware_os`, `hardware_cpu`, `hardware_gpu` e `hardware_device_type`. Suportar lista de jogos (`appid`) e overrides por jogo sem duplicação da configuração comum. Enviar parâmetros do serviço usando `input_json`. Nunca expor chave em logs. Respeitar o máximo documentado de `num_per_page` de 100.

## 5. Coleta Steam diária, histórica e incremental
Executar coleta uma vez ao dia, por jogo. Implementar estratégias `ColetaHistorica`, `ColetaRecente`, `ColetaAtualizada` e `ReconciliacaoPeriodica`, configuráveis por YAML. Paginar por cursor desde `*` até exaustão ou limites explícitos, usar ordenações adequadas para cobertura (Recent/Updated), e não usar Helpful como estratégia obrigatória para varrer todo o histórico. Aplicar retry com backoff exponencial e jitter, tratamento específico HTTP 429, timeouts, limites de concorrência, rate limit, circuit breaker somente se necessário, retomada por checkpoints e trilha de execução por jogo. `cursor` é estado transitório da coleta, não identificador histórico imutável.

Guardar os campos de review e autor conforme documentação anexa: IDs, texto original para consulta humana, idioma, timestamps, `voted_up`, `votes_up`, `votes_funny`, `weighted_vote_score`, `comment_count`, compras, Early Access, reembolso, resposta do desenvolvedor, Steam Deck, hardware e autor (`steamid`, `num_reviews`, playtime e `last_played`). Nem todos entram no treinamento. Preservar nulos, ausência de campos e versões da API.

## 6. Banco de staging transacional — novo requisito obrigatório
Introduzir staging como primeira persistência controlada da ingestão, entre API Steam e publicação nas camadas do Data Lake. Banco padrão: SQLite. A configuração deverá permitir trocar para PostgreSQL ou outra implementação sem modificar serviço de coleta, regras ou pipeline de ML. Não usar SQL ou tipos específicos do SQLite no domínio. Empregar `RepositorioStaging[T]` (Repository), `AdaptadorSQLite`/`AdaptadorPostgres` (Adapter), `FabricaStaging` com registro de implementações (Factory/Registry), `UnidadeTrabalho` (Unit of Work) para transações e Strategy para políticas de upsert, reconciliação e retenção. Evitar espalhar `if banco == ...` pelo código; validação de configuração deve recusar drivers não registrados.

Estrutura lógica mínima do staging:
- `execucoes_coleta`: `id_execucao`, `appid`, estratégia, início/fim, status, parâmetros, cursor/checkpoint, volume, tentativas e erros.
- `paginas_recebidas`: identificador idempotente da página, jogo, execução, cursor, instante de coleta, hash, status e referência ao payload Bronze.
- `reviews_atuais`: chave `(appid, recommendationid)`, campos normalizados, `timestamp_updated`, hash semântico e última coleta.
- `reviews_historico`: chave `(appid, recommendationid, versao_registro)`, campos/snapshot ou referência ao payload, início da vigência e data da captura.
- `autores_observados`: `steamid`, `appid`, métricas observadas e `data_coleta`; impedir confusão entre estado da coleta e estado no momento da review.
- `marcadores_coleta`: checkpoints por appid + estratégia, atualização e status.
- `eventos_publicacao`: outbox para publicar Bronze/Silver com entrega reexecutável e idempotência.

Requisitos: esquema migrável, constraints/índices, unicidade, transações, operações em lote, tratamento de conflitos, política de retenção, backups, recuperação após falhas, consistência entre staging e Data Lake. Para SQLite: definir WAL quando adequado, busy_timeout, um escritor de cada vez, arquivos em volume persistente e migrações. SQLite é suficiente para protótipo e um escritor; não assumir escalabilidade de múltiplos escritores simultâneos. Para expansão concorrente, migrar via adaptador para PostgreSQL sem mudar interfaces. A escrita na Bronze deverá guardar payload original imutável; definir política de reconciliação quando a gravação no banco e no armazenamento de objetos não formarem uma transação distribuída. Outbox e reprocessamento resolvem publicação eventual; não prometer atomicidade distribuída inexistente.

Exemplo `infraestrutura/staging.yaml`:
```yaml
staging:
  ativado: true
  tecnologia: sqlite
  estrategia_escrita: upsert_versionado
  conexao:
    sqlite:
      caminho: ${STAGING_SQLITE_PATH}
      modo_journal: WAL
      timeout_segundos: 30
    postgres:
      url_env: STAGING_POSTGRES_DSN
  lote_registros: 500
  preservar_historico: true
  usar_outbox: true
  retencao_dias: 90
```
`sqlite` e `postgres` são nomes registrados pelo bootstrap de infraestrutura. Configurações de conexão específicas não devem vazar para contratos de domínio. Se o banco estiver em outro container, configurar a conexão de acordo com o Compose existente.

## 6.1. Generators e iterators na ingestão Steam e no staging
**Requisito obrigatório:** utilizar `Iterator[T]`, `Iterable[T]` e generators (`yield`) para consumo incremental de páginas da API, lotes de reviews, registros do staging e eventos de publicação, quando isso reduzir materialização em memória. Não utilizar generators como substitutos de `DataFrame` vetorizado nem presumir que geradores impliquem paralelismo. Manter as regras gerais de generators/iterators na primeira parte deste documento.

**Contratos e tipos:**
- `Iterator[T]`: fluxo síncrono de passagem única; documentar que consumi-lo esgota o iterador.
- `Iterable[T]`: fonte capaz de fornecer iterador, mas não prometer reiteração a menos que o contrato explicite isso; um iterator também é iterable.
- `Generator[T, None, None]`: usar quando a semântica específica de generator for necessária; preferir `Iterator[T]` no contrato público simples.
- `AsyncIterator[T]`/`AsyncGenerator[T, None]`: apenas quando o adaptador de I/O usar asyncio de ponta a ponta; não misturar event loop com drivers síncronos sem justificativa.
- `Protocol[T_co]` e genéricos de retorno tipado: definir interfaces `FontePaginas[T]`, `LeitorLotes[T]` e `PublicadorEventos[T]`; integrar fontes e destinos com Strategy/Adapter, sem seleção por cadeias `if/elif`.
- `dataclass(frozen=True, slots=True)` para os tipos de transferência, sem `Any`, inclusive nos exemplos e implementações próprias.

**Fluxo de execução com backpressure:** `FontePaginasSteam` gera uma página por vez → extrator produz registros por lote → `RepositorioStaging` grava em transação → outbox registra evento de publicação → publicador lê a outbox em lotes → Bronze/Silver. O produtor somente avança na velocidade permitida pelo consumidor, sem acumular todas as páginas em lista. Limitar tamanho de lote, tamanho de página, memória, tentativas e duração no YAML. Iteradores vinculados a conexão/transação não podem escapar do escopo de vida do contexto que mantém o recurso aberto.

**Exemplo de generator de páginas, simplificado, com cliente abstraído:**

```python
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PaginaReviews:
    registros: tuple[dict[str, object], ...]
    proximo_cursor: str | None


class ClientePaginas(Protocol):
    def buscar_pagina(self, appid: int, cursor: str) -> PaginaReviews: ...


class GeradorPaginasSteam:
    def __init__(self, cliente: ClientePaginas) -> None:
        self._cliente = cliente

    def iterar_paginas(self, appid: int) -> Iterator[PaginaReviews]:
        cursor = "*"
        cursores_visitados: set[str] = set()
        while cursor not in cursores_visitados:
            cursores_visitados.add(cursor)
            pagina = self._cliente.buscar_pagina(appid, cursor)
            if not pagina.registros:
                return
            yield pagina
            if pagina.proximo_cursor is None:
                return
            cursor = pagina.proximo_cursor
```

O exemplo mostra somente a semântica lazy: o adaptador real também deve aplicar limite de páginas, retry/rate limit, validação de resposta, checkpoint, idempotência, controle de repetição de cursor e falhas. A verificação de fim de fluxo é uma condição de controle legítima e **não** viola a diretriz de evitar `if` para seleção de tecnologia/estratégia.

**Iteração em lotes tipados para staging:** o repositório deve aceitar lotes delimitados de registros, não todo o histórico carregado em memória. Uma implementação poderá usar `itertools.batched` (Python 3.12+) para compor lotes, `executemany` no SQLite e escrita em massa equivalente no PostgreSQL; o adaptador selecionado define a operação concreta. Um lote deve representar uma unidade transacional delimitada e permitir `commit`/rollback e checkpoint coerente. Garantir que a falha durante a escrita não marque incorretamente o checkpoint como concluído.

**Configuração em `configuracoes/processamento/fluxos_incrementais.yaml`:**

```yaml
fluxos_incrementais:
  ativado: true
  modo: sincronico  # sincronico | assincrono (exige adaptador compatível)
  paginacao:
    tamanho_pagina: 100
    maximo_paginas_por_execucao: 10000
    detectar_cursor_repetido: true
  staging:
    tamanho_lote: 500
    transacao_por_lote: true
    checkpoint_por_lote: true
  publicacao:
    tamanho_lote: 500
    retomar_apos_falha: true
  limites:
    maximo_registros_em_buffer: 1000
```

O validador YAML deve checar compatibilidade entre `modo`, a fonte, o adaptador de staging e o publicador; os limites devem ser não negativos ou estritamente positivos conforme a semântica. Nunca armazenar generators/iterators como artefatos MLflow: materializar e versionar datasets/manifestos no estágio adequado.

**Iterators e Pandas/Polars:** usar generators para buscar/listrar arquivos, páginas, shards e lotes; após formar uma partição, aplicar operações vetorizadas ou `LazyFrame` do Polars. Evitar `iterrows()`, `itertuples()` e `apply(axis=1)` no processamento tabular quando houver solução nativa. Em volumes maiores, processar partições e publicar Parquet incrementalmente, com esquema consistente e sem conversão reiterada entre motores.

**Testes obrigatórios:** consumo único, finalização sem dados, paginação com cursor repetido, falha na página intermediária, rollback de lote, reexecução idempotente, limite de memória, propagação de exceções, fechamento de recursos e paridade dos dados obtidos por streaming versus coleta integral em uma fixture pequena. Monitorar `steam_pages_consumed_total`, `staging_batches_committed_total`, `staging_batch_duration_seconds` e `stream_buffer_records` (observando cardinalidade adequada).

## 7. Data Lake e trilha de linhagem
MinIO/S3 com caminhos/buckets configuráveis. `Bronze`: payload JSON original com partições por fonte/appid/data_coleta/id_execucao, sem substituição destrutiva. `Silver`: schema normalizado, histórico de versões e snapshots atuais, catálogo de autores, qualidade e metadados. `Gold`: datasets de treino por versão, atribuições de cluster, avaliações, tabelas de negócio, visualizações pré-agregadas e comparações. Registrar `id_execucao`, hash, versões de código, YAML, dados, modelo, algoritmo e execução analítica. Definir manifesto do dataset com chaves e arquivos originais; preferir Parquet nas camadas analíticas. Garantir idempotência, reconciliação entre staging e armazenamento, lifecycle e controle de acesso.

Estrutura ilustrativa:
```
datalake/
  bronze/steam/reviews/appid=<id>/data_coleta=<data>/execucao=<id>/pagina_0001.json
  silver/steam/reviews_historico/
  silver/steam/reviews_atual/
  silver/steam/autores_observados/
  silver/steam/qualidade_dados/
  gold/datasets/projeto=<nome>/versao_dataset=<hash>/
  gold/clusters/versao_modelo=<id>/
  gold/analises/perfis/
  gold/analises/distribuicoes/
  gold/analises/comparacoes/
  gold/analises/temporal/
```

## 8. Motores Pandas/Polars, seleção, filtros e transformações
Padrão `pandas`; `polars` opcional via Strategy/Adapter, com operações vetorizadas e suporte a LazyFrame quando útil. Seleção de colunas, filtros WHERE, transformação de atributos e criação de atributos deverão ter flags independentes `ativado: false` por padrão. Em vez de expressões Python arbitrárias executadas por `eval/exec`, definir AST/DSL declarativa YAML, com operadores aprovados (`igual`, `maior`, `entre`, `pertence`, `soma`, `subtrai`, `divide`, `log1p`, `converter_data`, etc.). Adaptadores traduzem para `pd` ou expressões `pl` nativas, preservando semântica, nulidade e tipos. Extensões de operações são adicionadas no Registry, sem `if` por motor na lógica de negócio. Testar equivalência entre motores; converter formatos apenas na borda exigida pelas bibliotecas ML.

Exemplo:
```yaml
filtros:
  ativado: false
  combinacao: and
  condicoes:
    - coluna: playtime_at_review
      operador: maior_igual
      valor: 120
criacao_atributos:
  ativado: false
  operacoes:
    - nome: horas_ate_review
      tecnica: dividir_constante
      origem: playtime_at_review
      valor: 60
```

## 9. Atributos e granularidades
Separar formalmente `treinamento`, `avaliacao`, `identificacao` e `temporais` no YAML. Inicialmente, `num_reviews`, `playtime_forever`, `playtime_last_two_weeks`, `playtime_at_review` e `last_played` serão contemplados; converter `last_played` para `dias_desde_ultima_atividade` relativamente à data de referência, evitando treinamento direto no timestamp absoluto sem justificativa. Criar outras features opcionais: horas em vez de minutos, `horas_apos_review`, proporção de jogo recente, log de tempos. Tratar zero, nulos, dados inconsistentes e data de referência. `playtime_forever`, `last_played` e `playtime_last_two_weeks` refletem a observação da coleta, não necessariamente a situação quando a review foi criada. A granularidade padrão é a review, com chaves `(appid, recommendationid)`; agregado por jogador/jogo é Strategy separada.

Dados para avaliar e interpretar, mas não necessariamente treinar: `voted_up`, `votes_up`, `votes_funny`, `weighted_vote_score`, `comment_count`, `steam_purchase`, `received_for_free`, `written_during_early_access`, `refunded`. Identificação: `appid`, `recommendationid`, `steamid`. Texto de review e developer_response apenas para apresentação humana no modo sem PLN. Definir política de privacidade, retenção e acesso a identificadores.

## 10. Pré-processamento extensível
Configuração com etapas compostas ordenadas: imputação `SimpleImputer`, `KNNImputer`; escalonamento `nenhum`, `StandardScaler`, `MinMaxScaler`, `RobustScaler`, `MaxAbsScaler`; transformação `log1p`, `PowerTransformer`, `QuantileTransformer`; codificação `OneHotEncoder`, `OrdinalEncoder`; redução `PCA`, `TruncatedSVD`; outliers `IQR`, `IsolationForest`, `LOF` (explicitar semântica de detecção em treino e inferência); seleção `VarianceThreshold`, correlação, manual. Strategy/Factory por técnica, Composite para pipeline, Null Object para etapa opcional válida. Não ajustar transformadores em dados reservados para validação; em estabilidade/repetição, reajustar etapas exclusivamente na amostra de treinamento de cada execução. Separar PCA/SVD para treino de PCA apenas para visualização. Validar domínios matemáticos, número de componentes e incompatibilidades. Com PyCaret, escolher de forma explícita quem é responsável pelo pré-processamento para impedir aplicação duplicada.

## 11. Clustering, frameworks, otimização e avaliação
Framework padrão `sklearn`, PyCaret opcional via Adapter; suporte inicial a `KMeans`, `DBSCAN`, `HDBSCAN`, selecionado no YAML, parâmetros completos por algoritmo. Não forçar que todo algoritmo possua centroides, ruído ou `.predict()`. Catálogo tipado de capacidades lidas dos adaptadores deverá orientar configurações e disponibilidade de gráficos. Registrar seeds quando aplicável. Métodos de tuning: grid, random e extensão futura Optuna/Bayesian, com objetivos configuráveis e restrições como faixa de número de clusters, ruído e tamanho mínimo. Clustering não supervisionado não deve ser tratado automaticamente como problema de CV supervisionada.

Avaliações: Silhouette, Davies-Bouldin, Calinski-Harabasz, taxa de ruído, cobertura, contagens, tamanhos/entropia de grupos, custo e estabilidade ARI/NMI em registros comparáveis; impedir seleção de modelos por uma única métrica. Reportar métricas indisponíveis ou indefinidas e justificar tratamento do ruído; nunca retornar zero fictício. Avaliações internas, estabilidade e negócio são estratégias distintas. Versionar comparações e destacar trade-offs estatísticos versus interpretabilidade.

## 12. MLflow e ciclo de vida dos modelos
Usar Observer para publicar início/fim, parâmetros, métricas, tags e artefatos no MLflow. Salvar pipeline ajustado completo, versionamento do dataset, hash dos YAMLs, dependências, assinatura dos atributos, versão do framework, métricas e perfis/figuras relevantes. Persistência de modelo deve contemplar `atribuir_novos_registros` somente quando houver capacidade real do algoritmo/adaptador; KMeans suporta atribuição nativa, DBSCAN padrão não oferece predição fora da amostra e HDBSCAN depende da implementação/configuração. Não inventar método universal. Para API, reutilizar MLflow Serving quando adequado às capacidades registradas; não tornar FastAPI obrigatório. Prever endpoint/consulta analítica separada para recuperar reviews por cluster sem executar NLP.

## 13. Regras de negócio pós-treinamento
Criar motor declarativo de regras, com flag `ativado: false` por padrão. Diferenciar: regras por review, por cluster e agregações por jogo. Compor predicados via Specification + Composite; priorização/encadeamento quando necessário por Chain of Responsibility; rotulagem pós-treino não altera clusters nem obriga retreino. Permitir regras de medianas, percentuais negativos, tempo de jogo, engajamento, valores nulos e classificação de cluster; registrar versões dos rótulos, justificativas e casos não classificados. Evitar inferir causalidade de correlação. Exemplo:
```yaml
regras_clusters:
  ativado: false
  regras:
    - identificador: experientes_insatisfeitos
      combinacao: and
      condicoes:
        - metrica: mediana_horas_jogadas
          operador: maior_igual
          valor: 100
        - metrica: percentual_reviews_negativas
          operador: maior_igual
          valor: 60
      rotulo: experientes_insatisfeitos
```

## 14. EDA e visualizações pós-treino
Cada visualização terá flag `ativado` e configuração de atributos, filtros, agregações, amostragem, backend e destino. Separar camada semântica Gold de renderização. O renderizador poderá usar Plotly, Altair ou outros registrados; Grafana é destino/plataforma de dashboards, não substituto conceitual 1:1 de uma biblioteca de gráficos; profiling é geração de relatório exploratório. Disponibilizar:
- Clusters: dispersão 2D, dispersão 3D, distribuição absoluta/percentual, perfil estatístico e resumo tabular;
- Estatística: boxplot, violin, histograma, correlação, matriz de dispersão, ECDF, percentis, heatmap normalizado, radar quando útil;
- ML: silhouette plot (quando definida), comparação entre algoritmos/experimentos, PCA/SVD 2D/3D, análise de ruído, distâncias aos centroides apenas para algoritmo compatível, estabilidade por reamostragem;
- Negócio: avaliações positivas/negativas, horas jogadas, interações (`votes_up`, `comment_count`), comparação entre jogos, tabela interativa das reviews originais, composição percentual e absoluta, destaques contra média global;
- Temporal: evolução, tendências, transições e alinhamento entre clusters de versões diferentes.

Exemplos de eixos: `playtime_at_review` x `comment_count`, `playtime_at_review` x `num_reviews`, `playtime_forever` x `votes_up`, `dias_desde_ultima_atividade` x `playtime_last_two_weeks`; cores por cluster e filtros por jogo, período e algoritmo. Não confundir projeção PCA 2D com distância real do modelo. Disponibilizar dashboards executivos, exploração, avaliação, evolução temporal e observabilidade; permitir troca do destino por Adapter sem alterar análise Gold.

## 15. Análise temporal opcional
`analise_temporal: false` por padrão; histórico de coleta permanece sempre ativo. Ao ativar, criar snapshots comparáveis, janelas, análises de mudança de distribuição e de rótulos. Os IDs de clusters podem ser permutados entre treinamentos: implementar estratégia de alinhamento baseada em perfis, membros coincidentes e distância apropriada antes de relatar evolução. Diferenciar drift de dados, mudança de composição da amostra e instabilidade do treinamento. Não inferir comportamento passado de atributos observados somente no presente.

## 16. Observabilidade e qualidade de dados
Instrumentar métricas de streaming/paginação e ingestão, staging, escrita S3, validações Bronze/Silver/Gold, processamento, feature engineering, tuning, treinamento, avaliação, resultados e infraestrutura. Usar Prometheus/Grafana e Loki/Alloy já existentes, quando disponíveis; logs estruturados com `id_execucao`, `appid`, etapa, versão de dataset e correlação, mas sem segredos nem payload pessoal completo. Indicadores: HTTP 429, taxa de sucesso, requests e retries, páginas e reviews por execução, atraso na coleta, checkpoint parado, duplicatas, falhas de qualidade, duração por etapa, p50/p95/p99, throughput, CPU/memória, cluster count, ruído, estabilidade, desvio de distribuição, frescor dos dados. Criar SLIs/SLOs e alertas configuráveis, evitando labels de alta cardinalidade como `steamid` e `recommendationid`. Dashboard comparativo de Pandas versus Polars, medindo tempo, throughput, memória e equivalência dos resultados.

Quality Gate: validar schema, tipos, unicidade de `(appid, recommendationid)`, nulos, domínios, consistência temporal, integridade entre jogo/review e desvio estatístico. Diferenciar erro bloqueante de aviso. Persistir relatórios e resultados de qualidade por dataset.

## 17. Testes, CI e segurança
pytest para unitários, integração, contrato, parametrizados, end-to-end com fixtures, propriedades/invariantes com Hypothesis quando útil e testes arquiteturais. Testar equivalência entre motores Pandas/Polars, implementação SQLite/PostgreSQL por contratos, idempotência, paginação, HTTP 429, falhas transacionais, replay de outbox, dados fora do domínio e compatibilidade YAML x algoritmo. Garantir testes de reprodutibilidade e contratos de renderização. CI executa type checker strict, lint, formatter, testes, checagem de dependências e segredos; bloquear violações relevantes. Definir política de retenção e acesso para dados públicos associados a identificadores pessoais; analisar termos de uso/licenciamento da API, limites de compartilhamento, requisitos LGPD quando aplicáveis.

## 18. Exemplos de configuração principais
`projeto.yaml`:
```yaml
configuracao:
  versao_schema: '1.0'
  nome_projeto: steam_reviews_clustering
funcionalidades:
  processamento_linguagem_natural: false
  analise_temporal: false
processamento:
  motor: pandas
machine_learning:
  framework: sklearn
  algoritmo: kmeans
```

`fontes/steam_api.yaml` (valores exemplificativos, todos os parâmetros do endpoint devem constar no schema da configuração):
```yaml
steam:
  periodicidade: diaria
  jogos:
    - appid: 427520
    - appid: 526870
  endpoint: IUserReviewsService/GetAppReviews/v1
  parametros:
    key_env: STEAM_API_KEY
    filter: recent
    languages: [brazilian]
    day_range: 30
    cursor: '*'
    review_type: all
    purchase_type: all
    num_per_page: 100
    filter_offtopic_activity: true
    display_language: brazilian
    use_review_quality: true
    date_range_start: null
    date_range_end: null
    date_range_exclude: false
    playtime_min_hours: null
    playtime_max_hours: null
    primarily_steam_deck: null
    hardware_os: null
    hardware_cpu: null
    hardware_gpu: null
    hardware_device_type: null
  modos_coleta:
    historica: true
    recente: true
    atualizada: true
    reconciliacao_periodica: true
  resiliencia:
    max_tentativas: 5
    timeout_segundos: 30
    concorrencia_maxima: 1
```
A opção `key_env` é um parâmetro interno do configurador; o adaptador a resolve para o campo `key` da API. `filter`/`review_type`/`purchase_type` são convertidos de enums nominais para valores int32 exigidos pelo endpoint. Paginação e datas devem obedecer às regras documentadas.

`machine_learning/algoritmos.yaml`:
```yaml
agrupamento:
  algoritmo: kmeans
  parametros:
    kmeans:
      n_clusters: 4
      random_state: 42
      n_init: 10
    dbscan:
      eps: 0.5
      min_samples: 5
    hdbscan:
      min_cluster_size: 20
      min_samples: 5
```

`analises/visualizacoes.yaml`:
```yaml
visualizacoes:
  destino: grafana
  renderizador: plotly
  dispersao_2d:
    ativado: true
    eixo_x: playtime_at_review
    eixo_y: comment_count
    colorir_por: cluster
  distribuicao_clusters:
    ativado: true
  perfil_clusters:
    ativado: true
  resumo_clusters:
    ativado: true
  distancias_centroides:
    ativado: false
  evolucao_temporal:
    ativado: false
```

## 19. Fluxo de execução e responsabilidades
1. `ConfYAML` carrega, tipa e valida todas as configurações e capacidades.
2. Orquestrador seleciona Strategy de coleta Steam por appid e modalidade.
3. Coletor produz páginas via `Iterator[PaginaReviews]` e escreve lotes delimitados, transacionais e idempotentes no RepositorioStaging selecionado pela fábrica; checkpoints acompanham commits.
4. Processo de publicação outbox grava Bronze original e assinala publicação concluída sem perda.
5. Processo Silver normaliza, reconcilia histórico e executa Quality Gate.
6. Processador tabular Pandas ou Polars carrega o dataset versionado e executa transformações declarativas.
7. Preparador ajusta transformadores, seleciona features, produz matrizes de treino sem IDs/texto.
8. Estratégia de clustering e tuning gera partições e métricas com dados/metodologia registrados.
9. Observer MLflow registra artefatos, parâmetros, configurações e desempenho.
10. Gold persiste rótulos por registro, resultados analíticos e perfis; regras de negócio rotulam sem retreinar.
11. Renderizadores e publicadores exibem dashboards; serviços de observabilidade coletam logs e métricas.
12. Modo temporal, PLN ou fontes alternativas são extensões opcionais isoladas e registradas.

## 20. Critérios de aceite (Definition of Done)
- Trocar `sqlite` por `postgres` via YAML + driver/migrações/adaptador, sem alterar serviços de negócio, funcionando nos mesmos testes de contrato.
- Trocar Pandas por Polars via YAML, mantendo equivalência de registros e regras dentro de tolerâncias definidas.
- Trocar KMeans por DBSCAN/HDBSCAN sem condicionais por nome no núcleo e com gráficos validados pelas capacidades.
- Trocar fonte Steam por SQL/Parquet com Strategy/Adapter, preservando contratos e tipagem.
- Coletar mais de um appid diariamente, retomar falhas, evitar duplicações e preservar históricos.
- Demonstrar paginação Steam lazy com generators/iterators tipados e escrita incremental em staging, sem materializar todo o histórico na RAM.
- Validar streaming com encerramento correto, cursor repetido, controle de memória, rollback, checkpoints e fechamento de conexões.
- Demonstrar linhagem API → staging → Bronze → Silver → Gold → MLflow → dashboard.
- Habilitar/desabilitar filtros, seleção, criação/transformação, técnicas de pré-processamento, regras e gráficos pelos YAMLs.
- Manter texto da review disponível para consulta humana sem utilizá-lo no modelo quando PLN estiver desativado.
- Atualizar rótulos e dashboards de negócio após treinamento sem retreinar o algoritmo.
- Garantir testes, CI strict, documentação e métricas de observabilidade.

## 21. Planejamento incremental
Fase 1: infraestrutura existente, configuração, contratos, generators/iterators da Steam, staging SQLite por lotes e Bronze/Silver/Gold, qualidade.
Fase 2: Pandas/Polars, features, pré-processamento, KMeans/DBSCAN/HDBSCAN, reprodutibilidade.
Fase 3: tuning, avaliação/estabilidade, MLflow, dashboard técnico.
Fase 4: regras pós-treino, camada Gold analítica e dashboards de negócio.
Fase 5: adaptador PostgreSQL, novas fontes, PyCaret, análise temporal, módulos opcionais de PLN, visualização interativa avançada.

## 22. Referência da API anexada e convenções
Usar como contrato de referência a seção `IUserReviewsService/GetAppReviews` disponibilizada no documento original: parâmetros `input_json`, filtros de enum, resposta `query_summary`, `reviews`, `cursor`, `day_range_used` e `total_matching`, autor, hardware e recomendações de paginação. Conferir mudanças posteriores na documentação oficial antes de implementar. Manter nome e tipo dos campos da API no adaptador externo; nomes do domínio, módulos e classes próprios permanecem em português. Em especial, `query_summary.num_reviews` é contagem de avaliações na página, enquanto `author.num_reviews` é número de avaliações públicas do autor: não confundir campos homônimos.


---

# APÊNDICE A — DOCUMENTAÇÃO STEAM FORNECIDA NO ANEXO ORIGINAL (REFERÊNCIA)

IUserReviewsService
Documentação do Steamworks > Referência da Web API do Steamworks > IUserReviewsService
Página indisponível no seu idioma.
Esta página de documentação não está disponível no seu idioma, portanto a versão em inglês está sendo exibida.
Methods for reading Steam user reviews.

Use this interface to get a dump of the reviews on an application in Steam. It replaces store.steampowered.com/appreviews/<appid>?json=1; see Migrating from /appreviews below.

NOTE: This is a Service interface, methods in this interface should be called with the input_json parameter.

For more info on how to use the Steamworks Web API please see the Visão geral da Web API.
GetAppReviews
GET https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/
Name	Type	Required	Description
key	string		(Optional) Steamworks Web API publisher authentication key. Pass a key associated with the app to get the higher rate limit.
appid	uint32	✔	App to get reviews for.
filter	int32		IUserReviewsService#EUserReviewsAppReviewsFilter. Sort order of the results. Defaults to k_EUserReviewsAppReviewsFilter_Helpful, which widens day_range until it finds results, so it will always return reviews. If paging through all the reviews with cursor, use Recent or Updated to eventually receive an empty list.
languages	string[]		API language codes to return reviews in (see Idiomas disponíveis no Steam). Empty means english; "all" means every language. Example usage: languages[0]='english', languages[1]='french', etc.
day_range	uint32		Only used by the Helpful filter. Number of days back from today to look for reviews. Defaults to 30, max 365; 0 means no limit.
cursor	string		Cursor to paginate through the results. Set to '*' or omit for the first request, then pass the cursor value returned in the previous response. Cursor values may contain characters that need to be URL-encoded.
review_type	int32		IUserReviewsService#EUserReviewsReviewType. Defaults to k_EUserReviewsReviewType_All.
purchase_type	int32		IUserReviewsService#EUserReviewsPurchaseType. Defaults to k_EUserReviewsPurchaseType_Steam.
num_per_page	uint32		Number of reviews to return per page. Defaults to 20, max 100.
filter_offtopic_activity	bool		By default, off-topic reviews (aka "Review Bombs") are filtered out. Pass false to include them. See here.
display_language	string		API language code for review_score_desc in the response. Defaults to english.
use_review_quality	bool		Helpful filter only. Ranks reviews that Steam has judged to be low quality (ASCII art, memes, off-topic, uninformative, vote farming) below the others. Defaults to true. If false, the Helpful filter sorts by weighted_vote_score and, unless day_range is 0, only returns reviews with a score of at least 0.5 and at least one helpful vote.
date_range_start	uint32		Unix timestamp. Only return reviews created at or after this time. Ignored unless date_range_end is also set.
date_range_end	uint32		Unix timestamp. Only return reviews created at or before this time. Ignored unless date_range_start is also set.
date_range_exclude	bool		If true, exclude reviews inside the date range instead of returning only them.
playtime_min_hours	uint32		Only return reviews whose author had at least this many hours in the app when the review was written.
playtime_max_hours	uint32		Only return reviews whose author had at most this many hours in the app when the review was written.
primarily_steam_deck	bool		Only return reviews whose author had played more than half their time on Steam Deck when the review was written.
hardware_os	string		Only return reviews written on hardware with this operating system.
hardware_cpu	string		Only return reviews written on hardware with this CPU.
hardware_gpu	string		Only return reviews written on hardware with this GPU.
hardware_device_type	string		Only return reviews written on this type of device.

Gets a page of public reviews for an app.

This method does not require a key, and anonymous responses may be cached for up to 10 minutes. Calls without a key associated with the app share a lower rate limit; a rate-limited call returns HTTP 429.

Response:
Name	Type	Description
query_summary	{message}	Totals for the query. num_reviews is the number of reviews on this page. The score fields (review_score, review_score_desc, total_positive, total_negative, total_reviews) are only returned on the first page, and only when review_type is k_EUserReviewsReviewType_All.
reviews	{message}[]	The reviews on this page. See below.
cursor	string	Pass this as cursor to get the next page.
day_range_used	uint32	Helpful filter only. The day range actually searched. Can be wider than day_range when the requested range had no reviews; 0 means no limit.
total_matching	uint32	Total number of reviews that match the query.

Each entry in reviews:
Name	Type	Description
recommendationid	uint64	Unique ID of the review.
author	{message}	See below.
language	string	API language code the review was written in.
review	string	Text of the review.
timestamp_created	uint32	Unix timestamp when the review was created.
timestamp_updated	uint32	Unix timestamp when the review was last updated.
voted_up	bool	True if this is a positive review.
votes_up	uint32	Number of users who found this review helpful.
votes_funny	uint32	Number of users who found this review funny.
weighted_vote_score	float	Helpfulness score.
comment_count	uint32	Number of comments posted on this review.
steam_purchase	bool	True if the author purchased the app on Steam.
received_for_free	bool	True if the author checked the box saying they got the app for free.
written_during_early_access	bool	True if the review was written while the app was in Early Access.
developer_response	string	Text of the developer's response, if any.
timestamp_dev_responded	uint32	Unix timestamp when the developer responded.
primarily_steam_deck	bool	True if the author played primarily on Steam Deck when the review was written.
refunded	bool	True if the author was refunded for the app.
hardware	{message}	The hardware the author chose to show on the review, if any. See below.

The author of each review:
Name	Type	Description
steamid	fixed64	SteamID of the author.
num_reviews	uint32	Number of public reviews the author has written.
playtime_forever	uint32	Lifetime playtime in the app, in minutes.
playtime_last_two_weeks	uint32	Playtime in the last two weeks, in minutes.
playtime_at_review	uint32	Playtime when the review was written, in minutes.
deck_playtime_at_review	uint32	Steam Deck playtime when the review was written, in minutes.
last_played	uint32	Unix timestamp when the author last played the app.

The hardware of each review, as reported by the author's Steam client:
Name	Type	Description
os	string	Operating system.
cpu_name	string	CPU.
adapter_description	string	GPU.
system_ram	uint64	System RAM, in MB.
vram_size	uint32	Video RAM, in MB.
Migrating from /appreviews
store.steampowered.com/appreviews/<appid>?json=1 is deprecated. GetAppReviews takes the same filters, with these differences:

Parameters are passed in input_json, and the string values are now enums: filter all/recent/updated is Helpful/Recent/Updated (IUserReviewsService#EUserReviewsAppReviewsFilter), and review_type and purchase_type map to IUserReviewsService#EUserReviewsReviewType and IUserReviewsService#EUserReviewsPurchaseType.
language is now languages, a list.
There is a new Funny sort, and new date, playtime, Steam Deck and hardware filters.
The response has no success field; check the HTTP status instead.
author.num_games_owned is no longer returned.
weighted_vote_score is a number, not a string.
Each review has a new refunded field.
hardware has the same fields, but its strings are no longer profanity-filtered.
total_matching and day_range_used are new.
Enums
These are enums which are defined for use with IUserReviewsService.
EUserReviewsAppReviewsFilter
How to sort the results of GetAppReviews.

Name	Value	Description
k_EUserReviewsAppReviewsFilter_Helpful	0	Most helpful, within day_range.
k_EUserReviewsAppReviewsFilter_Recent	1	Most recently created.
k_EUserReviewsAppReviewsFilter_Updated	2	Most recently updated.
k_EUserReviewsAppReviewsFilter_Funny	3	Most votes for funny.
EUserReviewsReviewType
Name	Value	Description
k_EUserReviewsReviewType_All	0	All reviews.
k_EUserReviewsReviewType_Positive	1	Only positive reviews.
k_EUserReviewsReviewType_Negative	2	Only negative reviews.
EUserReviewsPurchaseType
Name	Value	Description
k_EUserReviewsPurchaseType_Steam	0	Only reviews by users who purchased the app on Steam.
k_EUserReviewsPurchaseType_All	1	All reviews.
k_EUserReviewsPurchaseType_NonSteamPurchase	2	Only reviews by users who did not purchase the app on Steam.
