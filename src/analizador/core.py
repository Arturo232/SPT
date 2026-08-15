"""Núcleo matemático del analizador (equivalente a ``core/*.m``).

Funciones de cálculo que NO imprimen; devuelven escalares, ``numpy`` arrays
o estructuras de resultado (``SimpleNamespace``) según el contrato de datos
(ver ``docs/contratos.md``).
"""

import math
from types import SimpleNamespace

import numpy as np

from .errors import error_analizador

_EPS = np.finfo(float).eps


def _es_numerico(valor) -> bool:
    if isinstance(valor, np.ndarray):
        return valor.dtype.kind in "biufc"
    if isinstance(valor, (list, tuple)):
        return all(_es_numerico(v) for v in valor)
    return isinstance(valor, (int, float, complex, np.number))


# ---------------------------------------------------------------------------
# Validaciones de entrada
# ---------------------------------------------------------------------------
def validate_input(kind: str, value, name: str = "valor"):
    """Validaciones comunes de entrada para todo el proyecto.

    ``kind`` admite: 'numeric', 'fp', 'positive', 'frequency', 'nonzero',
    'scalar'. ``name`` es una etiqueta usada en los mensajes de error.
    """
    if not _es_numerico(value):
        error_analizador("core", "noNumerico",
                         "Error: {0} debe ser numerico. Valor recibido: {1}",
                         name, type(value).__name__)
    if not isinstance(value, np.ndarray):
        arr = np.asarray(value)
    else:
        arr = value
    k = kind.lower()
    if k == "numeric":
        pass
    elif k == "fp":
        if np.any(arr < 0) or np.any(arr > 1):
            error_analizador("core", "fpInvalido",
                             "Error: el factor de potencia debe estar entre 0 y 1.\nValor recibido: {0}", value)
    elif k == "positive":
        if np.any(arr <= 0):
            error_analizador("core", "noPositivo",
                             "Error: {0} debe ser positivo.\nValor recibido: {1}", name, value)
    elif k == "frequency":
        if np.any(arr <= 0):
            error_analizador("core", "frecuenciaInvalida",
                             "Error: la frecuencia debe ser positiva.\nValor recibido: {0}", value)
    elif k == "nonzero":
        if np.any(arr == 0):
            error_analizador("core", "cero",
                             "Error: {0} no puede ser cero.\nValor recibido: {1}", name, value)
    elif k == "scalar":
        if not np.isscalar(value):
            error_analizador("core", "noEscalar",
                             "Error: {0} debe ser un escalar.\nValor recibido: {1}", name, arr.shape)
    else:
        error_analizador("core", "tipoDesconocido",
                         "Error: tipo de validacion desconocido: {0}", kind)


# ---------------------------------------------------------------------------
# Números complejos
# ---------------------------------------------------------------------------
def polar_to_complex(mag, angle_deg):
    """Convierte un fasor polar a rectangular. ``z = M*(cos + j*sin)``."""
    validate_input("numeric", mag, "mag")
    validate_input("numeric", angle_deg, "angleDeg")
    if np.any(np.asarray(mag) < 0):
        error_analizador("core", "magNegativa",
                         "Error: la magnitud debe ser no negativa. Valor recibido: {0}", mag)
    rad = np.deg2rad(angle_deg)
    return mag * (np.cos(rad) + 1j * np.sin(rad))


def complex_to_polar(z):
    """Convierte un complejo a polar. Regresa ``{mag, angleDeg}``."""
    validate_input("numeric", z, "z")
    return SimpleNamespace(mag=abs(z), angleDeg=np.rad2deg(np.angle(z)))


# ---------------------------------------------------------------------------
# V, I, Z, Y, S
# ---------------------------------------------------------------------------
def complex_power(V, I):
    """Potencia compleja ``S = V * conj(I)``."""
    validate_input("numeric", V, "V")
    validate_input("numeric", I, "I")
    if np.shape(V) != np.shape(I):
        error_analizador("core", "dimensiones",
                         "Error: V e I deben tener las mismas dimensiones.")
    return V * np.conjugate(I)


def current_from_voltage_impedance(V, Z):
    """Ley de Ohm compleja: ``I = V / Z``."""
    validate_input("numeric", V, "V")
    validate_input("numeric", Z, "Z")
    validate_input("nonzero", Z, "Z")
    return V / Z


def voltage_from_current_impedance(I, Z):
    """Ley de Ohm compleja: ``V = I * Z``."""
    validate_input("numeric", I, "I")
    validate_input("numeric", Z, "Z")
    return I * Z


def current_from_power(S, V):
    """``S = V*conj(I)  =>  I = conj(S / V)``."""
    validate_input("numeric", S, "S")
    validate_input("numeric", V, "V")
    validate_input("nonzero", V, "V")
    return np.conjugate(S / V)


def impedance_from_power(V, S):
    """``Z = |V|^2 / conj(S) = V*conj(V)/conj(S)``."""
    validate_input("numeric", V, "V")
    validate_input("numeric", S, "S")
    validate_input("nonzero", S, "S")
    return (V * np.conjugate(V)) / np.conjugate(S)


def admittance_from_impedance(Z):
    """``Y = 1 / Z``."""
    validate_input("numeric", Z, "Z")
    validate_input("nonzero", Z, "Z")
    return 1.0 / Z


def impedance_from_admittance(Y):
    """``Z = 1 / Y``."""
    validate_input("numeric", Y, "Y")
    validate_input("nonzero", Y, "Y")
    return 1.0 / Y


def apparent_power(P, Q):
    """Potencia aparente ``|S| = sqrt(P^2 + Q^2)``."""
    validate_input("numeric", P, "P")
    validate_input("numeric", Q, "Q")
    return np.hypot(P, Q)


def power_factor(S):
    """Factor de potencia y tipo de carga a partir de ``S``.

    Convención de signos: ``Q > 0`` → inductiva / atraso; ``Q < 0`` →
    capacitiva / adelanto.
    """
    validate_input("numeric", S, "S")
    result = SimpleNamespace()
    result.Sabs = abs(S)
    if result.Sabs < _EPS:
        result.fp = 1
        result.type = "resistiva"
        return result
    result.fp = abs(np.real(S)) / result.Sabs
    q = np.imag(S)
    if abs(q) < 1e-12 * result.Sabs:
        result.type = "resistiva"
    elif q > 0:
        result.type = "inductiva"
    else:
        result.type = "capacitiva"
    return result


def power_from_vi(V, I):
    """Estructura completa de potencia a partir de ``V`` e ``I``.

    Regresa ``{V, I, S, P, Q, Sabs, fp, phi_deg, type}``.
    """
    validate_input("numeric", V, "V")
    validate_input("numeric", I, "I")
    result = SimpleNamespace()
    result.V = V
    result.I = I
    result.S = complex_power(V, I)
    result.P = np.real(result.S)
    result.Q = np.imag(result.S)
    fp_info = power_factor(result.S)
    result.Sabs = fp_info.Sabs
    result.fp = fp_info.fp
    result.type = fp_info.type
    result.phi_deg = np.rad2deg(np.angle(result.S))
    return result


def rad2deg(x):
    return np.rad2deg(x)


def deg2rad(x):
    return np.deg2rad(x)
