"""Componentes simétricas (equivalente a ``modules/componentesSimetricas/*.m``)."""

import math
from types import SimpleNamespace

import numpy as np

from ..core import validate_input
from ..errors import error_analizador


def operador_a():
    """Operador de giro "a" de Fortescue: ``a = 1 angulo 120``."""
    return np.exp(1j * math.radians(120))


def abc_to_sequence(xabc):
    """Transformación de Fortescue abc → 012.

    ``seq = A^{-1} * xabc`` con ``A = [1 1 1; 1 a a^2; 1 a^2 a]``.
    """
    validate_input("numeric", xabc, "xabc")
    if np.size(xabc) != 3:
        error_analizador("componentesSimetricas", "noTrifasico",
                         "Error: se esperan exactamente 3 fasores.")
    a = operador_a()
    a_inv = (1 / 3) * np.array([[1, 1, 1], [1, a, a ** 2], [1, a ** 2, a]])
    return a_inv @ np.asarray(xabc).flatten()


def sequence_to_abc(seq):
    """Transformación inversa de Fortescue 012 → abc."""
    validate_input("numeric", seq, "seq")
    if np.size(seq) != 3:
        error_analizador("componentesSimetricas", "noTrifasico",
                         "Error: se esperan exactamente 3 fasores.")
    a = operador_a()
    A = np.array([[1, 1, 1], [1, a ** 2, a], [1, a, a ** 2]])
    return A @ np.asarray(seq).flatten()
