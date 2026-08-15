"""Corrección de factor de potencia (equivalente a ``modules/correccionFP/*.m``)."""

import math
from types import SimpleNamespace

import numpy as np

from ..core import power_factor, rad2deg, validate_input
from ..errors import error_analizador


def required_reactive_power(P, fp1, fp2):
    """Compensación reactiva para llevar el FP de ``fp1`` a ``fp2``.

    Relaciones: ``phi = acos(FP)``, ``Q = P*tan(phi)``, ``Qc = Q1 - Q2``.
    Regresa ``{P, fp1, fp2, phi1_deg, phi2_deg, Q1, Q2, Qc, requiereCompensacion}``.
    """
    validate_input("numeric", P, "P")
    validate_input("fp", fp1, "fp1")
    validate_input("fp", fp2, "fp2")
    validate_input("positive", P, "P")
    phi1 = math.degrees(math.acos(fp1))
    phi2 = math.degrees(math.acos(fp2))
    result = SimpleNamespace()
    result.P = P
    result.fp1 = fp1
    result.fp2 = fp2
    result.phi1_deg = phi1
    result.phi2_deg = phi2
    result.Q1 = P * math.tan(math.radians(phi1))
    result.Q2 = P * math.tan(math.radians(phi2))
    result.Qc = result.Q1 - result.Q2
    if result.Qc > 1e-12:
        result.requiereCompensacion = "capacitiva"
    elif result.Qc < -1e-12:
        result.requiereCompensacion = "inductiva"
    else:
        result.requiereCompensacion = "ninguna"
    return result


def capacitor_reactance(V, Qc):
    """Reactancia capacitiva necesaria para entregar ``Qc`` a ``V``.

    Relación: ``|Xc| = V^2 / |Qc|``. Regresa ``{V, Qc, Xc}``.
    """
    validate_input("numeric", V, "V")
    validate_input("numeric", Qc, "Qc")
    if abs(Qc) < np.finfo(float).eps:
        error_analizador("correccionFP", "QcCero",
                         "Error: la compensacion Qc no puede ser cero.")
    result = SimpleNamespace()
    result.V = V
    result.Qc = Qc
    result.Xc = (V ** 2) / abs(Qc)
    return result


def capacitor_value(f, Xc):
    """Valor de la capacitancia a partir de frecuencia y ``Xc``.

    Relaciones: ``C = 1/(2*pi*f*|Xc|)`` [F], ``C_uF = 1e6*C`` [µF].
    """
    validate_input("frequency", f, "f")
    validate_input("numeric", Xc, "Xc")
    if Xc == 0:
        error_analizador("correccionFP", "XcCero", "Error: Xc no puede ser cero.")
    result = SimpleNamespace()
    result.f = f
    result.Xc = Xc
    result.C_F = 1 / (2 * math.pi * f * abs(Xc))
    result.C_uF = result.C_F * 1e6
    return result


def corrected_power_factor(P, Q_old, Qc):
    """Nuevo FP tras añadir una compensación reactiva ``Qc``.

    ``Qc`` es negativa para un capacitor. Relaciones:
    ``Q_new = Q_old + Qc``, ``|S| = sqrt(P^2 + Q_new^2)``, ``FP = |P|/|S|``.
    """
    validate_input("numeric", P, "P")
    validate_input("numeric", Q_old, "Q_old")
    validate_input("numeric", Qc, "Qc")
    q_nueva = Q_old + Qc
    result = SimpleNamespace()
    result.P = P
    result.Q_old = Q_old
    result.Qc = Qc
    result.Q_new = q_nueva
    result.Sabs = math.hypot(P, q_nueva)
    result.fp = abs(P) / result.Sabs
    result.phi_deg = math.degrees(math.atan2(q_nueva, P))
    fp_info = power_factor(P + 1j * q_nueva)
    result.type = fp_info.type
    return result


def capacitor_kvar(qc_var):
    """Convierte ``Qc`` de var a kvar."""
    validate_input("numeric", qc_var, "Qc_var")
    return qc_var / 1000
