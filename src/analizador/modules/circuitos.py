"""Circuitos monofásicos (equivalente a ``modules/circuitosMonofasicos/*.m``).

Serie/paralelo R-X, resolución de circuitos serie y paralelo mediante
admitancias. Solo cálculos: nunca imprimen.
"""

from types import SimpleNamespace

from ..core import (admittance_from_impedance, current_from_voltage_impedance,
                    impedance_from_admittance, power_from_vi,
                    rad2deg, validate_input)
from ..errors import error_analizador


def solve_series_rx(R, X):
    """Impedancia equivalente de una conexión serie R-X.

    Regresa ``{R, X, Z, Zmag, angleDeg}``.
    """
    validate_input("numeric", R, "R")
    validate_input("numeric", X, "X")
    validate_input("positive", R, "R")
    result = SimpleNamespace()
    result.R = R
    result.X = X
    result.Z = R + 1j * X
    result.Zmag = abs(result.Z)
    result.angleDeg = rad2deg(math_angle(result.Z))
    return result


def solve_parallel_rx(R, X):
    """Impedancia equivalente de una conexión R-X en paralelo.

    Relaciones: ``Y = 1/R + 1/(jX)``, ``Zeq = 1/Y``.
    Regresa ``{R, X, Y, Zeq, Zmag, angleDeg}``.
    """
    validate_input("numeric", R, "R")
    validate_input("numeric", X, "X")
    validate_input("positive", R, "R")
    if X == 0:
        error_analizador("circuitosMonofasicos", "Xcero",
                         "Error: la reactancia X no puede ser cero en una rama reactiva.")
    result = SimpleNamespace()
    result.R = R
    result.X = X
    y_resistiva = admittance_from_impedance(R)
    y_reactiva = admittance_from_impedance(1j * X)
    result.Y = y_resistiva + y_reactiva
    result.Zeq = impedance_from_admittance(result.Y)
    result.Zmag = abs(result.Zeq)
    result.angleDeg = rad2deg(math_angle(result.Zeq))
    return result


def solve_series_circuit(V, Z):
    """Resuelve un circuito serie con impedancia equivalente ``Z``.

    Relaciones: ``I = V/Z``, ``S = V*conj(I)``.
    Regresa la estructura de ``power_from_vi`` más ``Z``.
    """
    validate_input("numeric", V, "V")
    validate_input("numeric", Z, "Z")
    validate_input("nonzero", Z, "Z")
    i = current_from_voltage_impedance(V, Z)
    result = power_from_vi(V, i)
    result.Z = Z
    return result


def solve_parallel_circuit(V, *impedancias):
    """Resuelve un circuito con varias impedancias en paralelo.

    Relaciones: ``Ytotal = sum(1/Zk)``, ``Zeq = 1/Ytotal``, ``I = V/Zeq``.
    Regresa la estructura de ``solve_series_circuit`` más ``Ytot`` y ``Zeq``.
    """
    validate_input("numeric", V, "V")
    if len(impedancias) == 0:
        error_analizador("circuitosMonofasicos", "sinImpedancias",
                         "Error: indique al menos una impedancia en paralelo.")
    y_total = 0
    for k, zk in enumerate(impedancias, start=1):
        validate_input("numeric", zk, f"Z{k}")
        validate_input("nonzero", zk, f"Z{k}")
        y_total = y_total + admittance_from_impedance(zk)
    z_equivalente = impedance_from_admittance(y_total)
    result = solve_series_circuit(V, z_equivalente)
    result.Ytot = y_total
    result.Zeq = z_equivalente
    return result


def math_angle(z):
    """Ángulo en radianes de un complejo (ayuda de compatibilidad)."""
    from numpy import angle
    return angle(z)
