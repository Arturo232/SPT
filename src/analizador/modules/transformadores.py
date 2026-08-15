"""Transformadores (equivalente a ``modules/transformadores/*.m``)."""

import math
from types import SimpleNamespace

from ..core import validate_input
from ..errors import error_analizador
from .per_unit import change_of_base


def _normalizar_conexion_transformador(conexion):
    if not isinstance(conexion, str):
        error_analizador("transformadores", "conexionInvalida",
                         "Error: la conexion debe ser 'Y' o 'Delta'.")
    c = conexion.lower()
    if c in ("y", "estrella"):
        return "Y"
    if c in ("delta", "d"):
        return "D"
    error_analizador("transformadores", "conexionInvalida",
                     "Error: conexion no reconocida: {0}. Use 'Y' o 'Delta'.", conexion)


def ideal_transformer(V1, N1, N2, I1=None):
    """Transformador ideal.

    Relaciones: ``a = N1/N2``, ``V2 = V1/a``, ``I2 = a*I1`` (si se da I1).
    Regresa ``{N1, N2, a, V1, V2}`` (+ ``I1``, ``I2`` si aplica).
    """
    validate_input("numeric", V1, "V1")
    validate_input("positive", N1, "N1")
    validate_input("positive", N2, "N2")
    result = SimpleNamespace()
    result.N1 = N1
    result.N2 = N2
    result.a = N1 / N2
    result.V1 = V1
    result.V2 = V1 / result.a
    if I1 is not None:
        validate_input("numeric", I1, "I1")
        result.I1 = I1
        result.I2 = result.a * I1
    return result


def transformer_equivalent(a, Z, lado="primario"):
    """Refiere una impedancia al otro lado del transformador.

    ``Z' = a^2 * Z`` (secundario → primario) o ``Z' = Z / a^2``
    (primario → secundario).
    """
    validate_input("numeric", a, "a")
    validate_input("numeric", Z, "Z")
    validate_input("nonzero", a, "a")
    c = lado.lower()
    if c in ("primario", "p"):
        return (a ** 2) * Z
    if c in ("secundario", "s"):
        return Z / (a ** 2)
    error_analizador("transformadores", "ladoInvalido",
                     "Error: lado no reconocido: {0}. Use 'primario' o 'secundario'.", lado)


def per_unit_transformer(zpu_trafo, sbase_trafo, vbase_trafo, sbase_sist, vbase_sist):
    """Cambia la base de la impedancia en p.u. del transformador a la del sistema.

    Regresa ``{Zpu_trafo, Zpu_sistema}``.
    """
    validate_input("numeric", zpu_trafo, "ZpuTrafo")
    validate_input("positive", sbase_trafo, "SbaseTrafo")
    validate_input("positive", vbase_trafo, "VbaseTrafo")
    validate_input("positive", sbase_sist, "SbaseSist")
    validate_input("positive", vbase_sist, "VbaseSist")
    result = SimpleNamespace()
    result.Zpu_trafo = zpu_trafo
    result.Zpu_sistema = change_of_base(zpu_trafo, sbase_trafo, vbase_trafo, sbase_sist, vbase_sist)
    return result


def voltage_regulation(v2_sin_carga, v2_plena_carga):
    """Regulación de tensión en porcentaje.

    ``Reg[%] = (V2_sc - V2_pc) / V2_pc * 100``.
    """
    validate_input("numeric", v2_sin_carga, "V2SinCarga")
    validate_input("numeric", v2_plena_carga, "V2PlenaCarga")
    validate_input("nonzero", v2_plena_carga, "V2PlenaCarga")
    return (abs(v2_sin_carga) - abs(v2_plena_carga)) / abs(v2_plena_carga) * 100


def transformer_loss_efficiency(pout, plosses):
    """Eficiencia y pérdidas de un transformador.

    ``Pin = Pout + Plosses``; ``eficiencia[%] = Pout/Pin*100``.
    """
    validate_input("positive", pout, "Pout")
    validate_input("positive", plosses, "Plosses")
    p_in = pout + plosses
    result = SimpleNamespace()
    result.Pout = pout
    result.Plosses = plosses
    result.Pin = p_in
    result.eficiencia = pout / p_in * 100
    result.perdidas_porcentaje = plosses / p_in * 100
    return result


def three_phase_transformer(a, conexion_primario, conexion_secundario):
    """Relación de tensión de línea y desfase de un transformador trifásico.

    Relaciones (``a = N1/N2``):
      Y-Y / D-D : ``r = 1/a``, desfase 0
      Y-D       : ``r = 1/(sqrt(3)*a)``, desfase -30°
      D-Y       : ``r = sqrt(3)/a``, desfase +30°
    """
    validate_input("numeric", a, "a")
    validate_input("nonzero", a, "a")
    c1 = _normalizar_conexion_transformador(conexion_primario)
    c2 = _normalizar_conexion_transformador(conexion_secundario)
    result = SimpleNamespace()
    result.conexion1 = c1
    result.conexion2 = c2
    par = c1 + c2
    if par in ("YY", "DD"):
        result.r = 1 / a
        result.desfase_deg = 0
    elif par == "YD":
        result.r = 1 / (math.sqrt(3) * a)
        result.desfase_deg = -30
    else:  # DY
        result.r = math.sqrt(3) / a
        result.desfase_deg = 30
    return result
