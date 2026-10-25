"""Módulo de exceções de domínio da aplicação Steam Reviews Clustering."""


class ErroPlataformaClustering(Exception):
    """Exceção base para todos os erros da plataforma."""


class ErroConfiguracao(ErroPlataformaClustering):
    """Lançada quando há inconsistência ou falha na validação de arquivos YAML."""


class ErroColetaSteam(ErroPlataformaClustering):
    """Lançada em falhas de comunicação, limites de taxa ou resposta inválida da API Steam."""


class ErroLakehouse(ErroPlataformaClustering):
    """Lançada em erros de I/O, partição ou integridade das camadas Bronze, Silver e Gold."""


class ErroPreprocessamento(ErroPlataformaClustering):
    """Lançada quando uma transformação de atributos ou imputação falha."""


class ErroClustering(ErroPlataformaClustering):
    """Lançada em falhas durante o ajuste, convergência ou previsão de algoritmos de clustering."""


class ErroAlgoritmoNaoSuportado(ErroClustering):
    """Lançada quando uma operação requisitada não é compatível com o algoritmo selecionado."""


class ErroObservabilidade(ErroPlataformaClustering):
    """Lançada em erros na coleta ou exportação de métricas e logs."""
