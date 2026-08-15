"""Estabilidad (equivalente a ``modules/estabilidad/*.m``).

Ecuación de oscilación, criterio de áreas iguales y tiempo crítico de
despeje (modelo clásico generador - bus infinito).
"""

import math
from types import SimpleNamespace

from scipy.optimize import brentq

from ..core import rad2deg, validate_input
from ..errors import error_analizador


def swing_equation(Pm, Pe, H, f):
    """Ecuación de oscilación (swing) de una máquina síncrona.

    ``Pa = Pm - Pe``; ``omega_s = 2*pi*f``; ``M = 2*H/omega_s``.
    Regresa ``{Pm, Pe, Pa, H, f, omega_s, M}``.
    """
    validate_input("numeric", Pm, "Pm")
    validate_input("numeric", Pe, "Pe")
    validate_input("positive", H, "H")
    validate_input("positive", f, "f")
    omega_s = 2 * math.pi * f
    result = SimpleNamespace()
    result.Pm = Pm
    result.Pe = Pe
    result.Pa = Pm - Pe
    result.H = H
    result.f = f
    result.omega_s = omega_s
    result.M = 2 * H / omega_s
    return result


def equal_area_criterion(Pm, Pmax, PmaxFalla):
    """Criterio de áreas iguales para la estabilidad transitoria.

    Regresa ``{delta0_deg, deltaCr_deg, deltaMax_deg, A1, A2, Pm, Pmax,
    Pmax_falla}``.
    """
    validate_input("positive", Pm, "Pm")
    validate_input("positive", Pmax, "Pmax")
    validate_input("numeric", PmaxFalla, "PmaxFalla")
    if Pm >= Pmax:
        error_analizador("estabilidad", "PmExcede",
                         "Error: Pm debe ser menor que Pmax ({0}).", Pmax)

    delta0 = math.asin(Pm / Pmax)
    d_max = math.pi - delta0

    def a1(d):
        return Pm * (d - delta0) + PmaxFalla * (math.cos(d) - math.cos(delta0))

    def a2(d):
        return Pmax * (math.cos(d) - math.cos(d_max)) - Pm * (d_max - d)

    f_obj = lambda d: a1(d) - a2(d)
    delta_cr = brentq(f_obj, delta0 + 1e-6, d_max - 1e-6)

    result = SimpleNamespace()
    result.delta0_deg = rad2deg(delta0)
    result.deltaCr_deg = rad2deg(delta_cr)
    result.deltaMax_deg = rad2deg(d_max)
    result.A1 = a1(delta_cr)
    result.A2 = a2(delta_cr)
    result.Pm = Pm
    result.Pmax = Pmax
    result.Pmax_falla = PmaxFalla
    return result


def critical_clearing_time(Pm, delta0_deg, delta_cr_deg, H, f):
    """Tiempo crítico de despeje (falla en bornes: Pe = 0 durante la falla).

    ``acc = Pm*omega_s/(2H)``; ``tcr = sqrt(2*(deltaCr-delta0)/acc)``.
    Regresa ``{tcr, acc, H, f, delta0_deg, deltaCr_deg}``.
    """
    validate_input("positive", Pm, "Pm")
    validate_input("positive", H, "H")
    validate_input("positive", f, "f")
    omega_s = 2 * math.pi * f
    acc = Pm * omega_s / (2 * H)
    d0 = math.radians(delta0_deg)
    dcr = math.radians(delta_cr_deg)
    if dcr <= d0:
        error_analizador("estabilidad", "deltaCrInvalido",
                         "Error: deltaCr debe ser mayor que delta0.")
    tcr = math.sqrt(2 * (dcr - d0) / acc)
    result = SimpleNamespace()
    result.tcr = tcr
    result.acc = acc
    result.H = H
    result.f = f
    result.delta0_deg = delta0_deg
    result.deltaCr_deg = delta_cr_deg
    return result
