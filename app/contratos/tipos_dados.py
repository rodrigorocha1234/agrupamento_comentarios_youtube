"""Definições canônicas de tipos estritos para registros, valores escalares e JSON."""

type ValorEscalar = str | int | float | bool | None
type RegistroDado = dict[str, ValorEscalar]

# Tipo recursivo estrito para payloads JSON arbitrários (sem Any e sem object)
type ValorJson = (
    str
    | int
    | float
    | bool
    | None
    | list["ValorJson"]
    | dict[str, "ValorJson"]
)
type DicionarioJson = dict[str, ValorJson]
