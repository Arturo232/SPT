"""Máquinas eléctricas (equivalente a ``modules/maquinasElectricas/*.m``)."""

from types import SimpleNamespace

import numpy as np

from ..core import rad2deg, validate_input


def sync_generator_emf(V, I, Xs, Ra=0):
    """FEM interna de un generador síncrono.

    Relación: ``E = V + I*(Ra + jXs)`` (corriente saliente positiva).
    Regresa ``{V, I, Xs, Ra, E, E_mag, delta_deg}``.
    """
    validate_input("numeric", V, "V")
    validate_input("numeric", I, "I")
    validate_input("numeric", Xs, "Xs")
    validate_input("numeric", Ra, "Ra")
    e = V + I * (Ra + 1j * Xs)
    result = SimpleNamespace()
    result.V = V
    result.I = I
    result.Xs = Xs
    result.Ra = Ra
    result.E = e
    result.E_mag = abs(e)
    result.delta_deg = rad2deg(np.angle(e) - np.angle(V))
    return result


def power_angle_curve(E, V, Xs, delta_deg):
    """Curva potencia-ángulo de un generador síncrono.

    Relaciones: ``P = E*V/Xs * sin(delta)``, ``Pmax = E*V/Xs``.
    Regresa ``{E, V, Xs, delta_deg, P, Pmax}``.
    """
    validate_input("numeric", E, "E")
    validate_input("numeric", V, "V")
    validate_input("numeric", Xs, "Xs")
    validate_input("positive", Xs, "Xs")
    validate_input("numeric", delta_deg, "deltaDeg")
    import math
    p_max = E * V / Xs
    result = SimpleNamespace()
    result.E = E
    result.V = V
    result.Xs = Xs
    result.delta_deg = delta_deg
    result.P = p_max * math.sin(math.radians(delta_deg))
    result.Pmax = p_max
    return result
