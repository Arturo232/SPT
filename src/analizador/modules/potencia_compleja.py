"""Potencia compleja (equivalente a ``modules/potenciaCompleja/*.m``).

Flujos A (VI), B (VZ) y C (PF), suma de cargas y corriente de la fuente.
Solo cálculos: nunca imprimen.
"""

import math
from types import SimpleNamespace

import numpy as np

from ..core import (complex_power, current_from_power,
                    current_from_voltage_impedance, power_factor,
                    power_from_vi, rad2deg, validate_input)
from ..errors import error_analizador


def load_power_from_z(V, Z):
    """Potencia compleja de una carga a partir de ``V`` y ``Z``.

    Relaciones: ``I = V/Z``, ``S = V*conj(I)`` (≡ ``|V|^2/conj(Z)``).
    """
    validate_input("numeric", V, "V")
    validate_input("numeric", Z, "Z")
    validate_input("nonzero", Z, "Z")
    i = current_from_voltage_impedance(V, Z)
    result = power_from_vi(V, i)
    result.Z = Z
    return result


def source_current(stotal, V):
    """Corriente que entrega la fuente: ``I = conj(S/V)``."""
    validate_input("numeric", stotal, "Stotal")
    validate_input("numeric", V, "V")
    validate_input("nonzero", V, "V")
    return current_from_power(stotal, V)


def _extraer_s(arg):
    """Extrae la potencia compleja de un argumento (número o estructura)."""
    if isinstance(arg, SimpleNamespace):
        if hasattr(arg, "S"):
            return arg.S
        if hasattr(arg, "P") and hasattr(arg, "Q"):
            return arg.P + 1j * arg.Q
        error_analizador("potenciaCompleja", "estructuraInvalida",
                         "Error: la estructura debe contener S, o bien P y Q.")
    if isinstance(arg, dict):
        if "S" in arg:
            return arg["S"]
        if "P" in arg and "Q" in arg:
            return arg["P"] + 1j * arg["Q"]
        error_analizador("potenciaCompleja", "estructuraInvalida",
                         "Error: la estructura debe contener S, o bien P y Q.")
    return arg


def sum_power(*potencias):
    """Suma varias potencias complejas y devuelve la potencia total.

    Cada argumento puede ser un número complejo ``S`` o una estructura con
    campo ``S`` (o campos ``P`` y ``Q``).
    Regresa ``{S, P, Q, Sabs, fp, phi_deg, type}``.
    """
    if len(potencias) == 0:
        error_analizador("potenciaCompleja", "sinEntradas",
                         "Error: indique al menos una potencia.")
    s_total = 0
    for k, arg in enumerate(potencias, start=1):
        s_k = _extraer_s(arg)
        validate_input("numeric", s_k, f"S{k}")
        s_total = s_total + s_k
    result = SimpleNamespace()
    result.S = s_total
    result.P = np.real(s_total)
    result.Q = np.imag(s_total)
    fp_info = power_factor(s_total)
    result.Sabs = fp_info.Sabs
    result.fp = fp_info.fp
    result.type = fp_info.type
    result.phi_deg = rad2deg(np.angle(s_total))
    return result


def _power_from_pf(P, fp, tipo):
    """Flujo C: desde P, FP y tipo de carga."""
    validate_input("numeric", P, "P")
    validate_input("fp", fp, "fp")
    validate_input("positive", P, "P")
    phi = math.degrees(math.acos(fp))
    t = tipo.lower()
    if t in ("inductiva", "atraso", "atrasado", "ind", "l"):
        q = P * math.tan(math.radians(phi))
        tipo_out = "inductiva"
    elif t in ("capacitiva", "adelanto", "adelantado", "cap", "c"):
        q = -P * math.tan(math.radians(phi))
        tipo_out = "capacitiva"
    elif t in ("resistiva", "r"):
        q = 0.0
        tipo_out = "resistiva"
    else:
        error_analizador("potenciaCompleja", "tipoInvalido",
                         "Error: tipo de carga no reconocido: {0}", tipo)
    s = P + 1j * q
    result = SimpleNamespace()
    result.S = s
    result.P = P
    result.Q = q
    result.Sabs = abs(s)
    result.fp = abs(P) / result.Sabs
    result.phi_deg = rad2deg(np.angle(s))
    result.type = tipo_out
    return result


def solve_carga(mode, *args):
    """Resuelve la potencia de una carga según los datos disponibles.

    Modos:
      'VI' -> solve_carga('VI', V, I)
      'VZ' -> solve_carga('VZ', V, Z)
      'PF' -> solve_carga('PF', P, fp, tipo)
    """
    m = mode.upper()
    if m == "VI":
        if len(args) != 2:
            error_analizador("potenciaCompleja", "argumentos",
                             "Uso: solve_carga('VI', V, I)")
        return power_from_vi(args[0], args[1])
    if m == "VZ":
        if len(args) != 2:
            error_analizador("potenciaCompleja", "argumentos",
                             "Uso: solve_carga('VZ', V, Z)")
        return load_power_from_z(args[0], args[1])
    if m == "PF":
        if len(args) != 3:
            error_analizador("potenciaCompleja", "argumentos",
                             "Uso: solve_carga('PF', P, fp, tipo)")
        return _power_from_pf(args[0], args[1], args[2])
    error_analizador("potenciaCompleja", "modoDesconocido",
                     "Error: modo no valido. Use 'VI', 'VZ' o 'PF'.")
