"""Cortocircuitos (equivalente a ``modules/cortocircuitos/*.m``)."""

import math
from types import SimpleNamespace

import numpy as np

from ..core import rad2deg, validate_input
from ..errors import error_analizador
from .componentes_simetricas import sequence_to_abc


def _armar_falla(tipo, Vf, Z1, Z2, Z0, Zf, i0, i1, i2):
    """Construye la estructura de resultado de una falla asimétrica."""
    result = SimpleNamespace()
    result.tipo = tipo
    result.Vf = Vf
    result.Z1 = Z1
    result.Z2 = Z2
    result.Z0 = Z0
    result.Zf = Zf
    result.I0 = i0
    result.I1 = i1
    result.I2 = i2
    abc = sequence_to_abc(np.array([i0, i1, i2]))
    result.Ia = abc[0]
    result.Ib = abc[1]
    result.Ic = abc[2]
    result.If_mag = max(abs(abc[0]), abs(abc[1]), abs(abc[2]))
    return result


def three_phase_fault_current(Vf, Zth):
    """Corriente de falla trifásica balanceada: ``If = Vf / Zth``.

    Regresa ``{tipo, Vf, Zth, If, If_mag, angle_deg}``.
    """
    validate_input("numeric", Vf, "Vf")
    validate_input("numeric", Zth, "Zth")
    validate_input("nonzero", Zth, "Zth")
    i_falla = Vf / Zth
    result = SimpleNamespace()
    result.tipo = "trifasica"
    result.Vf = Vf
    result.Zth = Zth
    result.If = i_falla
    result.If_mag = abs(i_falla)
    result.angle_deg = rad2deg(np.angle(i_falla))
    return result


def single_line_to_ground_fault(Vf, Z1, Z2, Z0, Zf=0):
    """Falla de línea a tierra (fase a).

    Relaciones: ``I1 = Vf/(Z1+Z2+Z0+3*Zf)``, ``I0=I2=I1``.
    """
    validate_input("numeric", Vf, "Vf")
    i1 = Vf / (Z1 + Z2 + Z0 + 3 * Zf)
    return _armar_falla("SLG (linea a tierra)", Vf, Z1, Z2, Z0, Zf, i1, i1, i1)


def line_to_line_fault(Vf, Z1, Z2, Zf=0):
    """Falla entre líneas (fases b-c).

    Relaciones: ``I1 = Vf/(Z1+Z2+Zf)``, ``I2 = -I1``, ``I0 = 0``.
    """
    validate_input("numeric", Vf, "Vf")
    i1 = Vf / (Z1 + Z2 + Zf)
    return _armar_falla("LL (linea-linea)", Vf, Z1, Z2, math.nan, Zf, 0, i1, -i1)


def double_line_to_ground_fault(Vf, Z1, Z2, Z0, Zf=0):
    """Falla de dos líneas a tierra (fases b-c a tierra).

    Relaciones: ``Zp = Z2*(Z0+3Zf)/(Z2+Z0+3Zf)``; ``I1 = Vf/(Z1+Zp)``.
    """
    validate_input("numeric", Vf, "Vf")
    z_total = Z2 + Z0 + 3 * Zf
    zp = Z2 * (Z0 + 3 * Zf) / z_total
    i1 = Vf / (Z1 + zp)
    i2 = -i1 * (Z0 + 3 * Zf) / z_total
    i0 = -i1 * Z2 / z_total
    return _armar_falla("LLG (dos lineas a tierra)", Vf, Z1, Z2, Z0, Zf, i0, i1, i2)
