"""Manejo de errores unificado del proyecto.

Los identificadores se construyen como ``analizador:<modulo>:<codigo>``.
El catálogo canónico de mensajes está en ``config.py`` (función ``mensajes``).
"""

from __future__ import annotations


class AnalizadorError(Exception):
    """Excepción con el identificador estándar del proyecto."""

    def __init__(self, codigo: str, mensaje: str) -> None:
        self.codigo = codigo
        self.mensaje = mensaje
        super().__init__(mensaje)


def error_analizador(modulo: str, codigo: str, formato: str | None = None,
                     *args: object) -> None:
    """Lanza un ``AnalizadorError`` con id ``analizador:<modulo>:<codigo>``.

    ``formato`` es opcional; si se omite se usa un mensaje genérico.
    """
    id_ = f"analizador:{modulo}:{codigo}"
    if formato:
        mensaje = formato.format(*args)
    else:
        mensaje = f"Error: {codigo}."
    raise AnalizadorError(id_, mensaje)


def construir_error(err: Exception) -> dict[str, object]:
    """Construye una estructura de error controlada a partir de una excepción.

    Regresa un dict ``{codigo, mensaje, causa}`` usado por la capa de
    servicios (equivalente a ``services/private/construirError.m``).
    """
    if isinstance(err, AnalizadorError):
        codigo = err.codigo
        mensaje = err.mensaje
    else:
        codigo = "analizador:servicios:excepcion"
        mensaje = str(err)
    return {"codigo": codigo, "mensaje": mensaje, "causa": err}
