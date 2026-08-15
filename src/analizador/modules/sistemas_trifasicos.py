"""Sistemas trifásicos balanceados (equivalente a ``modules/sistemasTrifasicos/*.m``)."""

import math
from types import SimpleNamespace

import numpy as np

from ..core import (complex_power, current_from_voltage_impedance,
                    polar_to_complex, power_factor, rad2deg,
                    validate_input)
from ..errors import error_analizador
from .potencia_compleja import sum_power


def normalizar_conexion(conexion):
    """Normaliza el nombre de una conexión a 'Y' o 'Delta'."""
    if not isinstance(conexion, str):
        error_analizador("sistemasTrifasicos", "conexionInvalida",
                         "Error: la conexion debe ser 'Y' o 'Delta'.")
    c = conexion.lower()
    if c in ("y", "estrella", "star"):
        return "Y"
    if c in ("delta", "d"):
        return "Delta"
    error_analizador("sistemasTrifasicos", "conexionInvalida",
                     "Error: conexion no reconocida: {0}. Use 'Y' o 'Delta'.", conexion)


def assert_balanced(phasores, tol=1e-6):
    """Verifica si tres fasores están balanceados.

    Regresa ``(ok, msg)`` con ``msg`` 'balanceado' o 'desbalanceado'.
    """
    validate_input("numeric", phasores, "phasores")
    if np.size(phasores) != 3:
        error_analizador("sistemasTrifasicos", "noTrifasico",
                         "Error: se esperan exactamente 3 fasores.")
    magnitudes = np.abs(phasores)
    ok_mag = (np.max(magnitudes) - np.min(magnitudes)) < tol * np.max(magnitudes)
    angulos = np.sort(np.mod(rad2deg(np.angle(phasores)), 360))
    diferencias = np.diff(np.append(angulos, angulos[0] + 360))
    ok_ang = np.all(np.abs(diferencias - 120) < tol * 1000)
    ok = bool(ok_mag) and bool(ok_ang)
    return ok, ("balanceado" if ok else "desbalanceado")


def line_voltage_from_phase(vf, conexion):
    """Tensión de línea a partir de la tensión de fase (Y: sqrt(3)*Vf)."""
    validate_input("numeric", vf, "Vf")
    validate_input("positive", vf, "Vf")
    c = normalizar_conexion(conexion)
    return math.sqrt(3) * vf if c == "Y" else vf


def phase_voltage_from_line(vl, conexion):
    """Tensión de fase a partir de la tensión de línea (Y: VL/sqrt(3))."""
    validate_input("numeric", vl, "VL")
    validate_input("positive", vl, "VL")
    c = normalizar_conexion(conexion)
    return vl / math.sqrt(3) if c == "Y" else vl


def line_current_from_phase(if_, conexion):
    """Corriente de línea a partir de la corriente de fase (Delta: sqrt(3)*If)."""
    validate_input("numeric", if_, "If")
    validate_input("positive", if_, "If")
    c = normalizar_conexion(conexion)
    return if_ if c == "Y" else math.sqrt(3) * if_


def phase_current_from_line(il, conexion):
    """Corriente de fase a partir de la corriente de línea (Delta: IL/sqrt(3))."""
    validate_input("numeric", il, "IL")
    validate_input("positive", il, "IL")
    c = normalizar_conexion(conexion)
    return il if c == "Y" else il / math.sqrt(3)


def three_phase_power_from_phase(vf, if_):
    """Potencia trifásica a partir de fasores de fase.

    Relaciones: ``Sf = Vf*conj(If)``, ``S3f = 3*Sf``.
    """
    validate_input("numeric", vf, "Vf")
    validate_input("numeric", if_, "If")
    sf = complex_power(vf, if_)
    s3f = 3 * sf
    result = SimpleNamespace()
    result.Sf = sf
    result.S = s3f
    result.P = np.real(s3f)
    result.Q = np.imag(s3f)
    fp_info = power_factor(s3f)
    result.Sabs = fp_info.Sabs
    result.fp = fp_info.fp
    result.type = fp_info.type
    return result


def three_phase_power_from_line(vl, il, phi_deg):
    """Potencia trifásica a partir de valores de línea.

    Relaciones: ``|S3f| = sqrt(3)*VL*IL``, ``P = |S|*cos(phi)``,
    ``Q = |S|*sin(phi)``.
    """
    validate_input("numeric", vl, "VL")
    validate_input("numeric", il, "IL")
    validate_input("numeric", phi_deg, "phiDeg")
    validate_input("positive", vl, "VL")
    validate_input("positive", il, "IL")
    result = SimpleNamespace()
    result.Sabs = math.sqrt(3) * vl * il
    result.P = result.Sabs * math.cos(math.radians(phi_deg))
    result.Q = result.Sabs * math.sin(math.radians(phi_deg))
    result.S = result.P + 1j * result.Q
    fp_info = power_factor(result.S)
    result.fp = fp_info.fp
    result.type = fp_info.type
    result.phi_deg = phi_deg
    return result


def solve_three_phase_load(vl, conexion, zfase):
    """Resuelve una carga trifásica balanceada en Y o Delta.

    Se toma la fase "a" como referencia (ángulo 0). Regresa:
    ``{conexion, VL, Vf, If, IL, Zfase, Sf, S, P, Q, Sabs, fp, type}``.
    """
    validate_input("numeric", vl, "VL")
    validate_input("positive", vl, "VL")
    validate_input("numeric", zfase, "Zfase")
    validate_input("nonzero", zfase, "Zfase")
    c = normalizar_conexion(conexion)

    if c == "Y":
        vf = polar_to_complex(vl / math.sqrt(3), 0)
        i_fase = current_from_voltage_impedance(vf, zfase)
        i_linea = i_fase
    else:
        vf = polar_to_complex(vl, 0)
        i_fase = current_from_voltage_impedance(vf, zfase)
        i_linea = math.sqrt(3) * i_fase * np.exp(1j * math.radians(-30))

    pot = three_phase_power_from_phase(vf, i_fase)

    result = SimpleNamespace()
    result.conexion = c
    result.VL = vl
    result.Vf = vf
    result.If = i_fase
    result.IL = i_linea
    result.Zfase = zfase
    result.Sf = pot.Sf
    result.S = pot.S
    result.P = pot.P
    result.Q = pot.Q
    result.Sabs = pot.Sabs
    result.fp = pot.fp
    result.type = pot.type
    return result


def sum_three_phase_power(*potencias):
    """Suma potencias trifásicas (reutiliza ``sum_power``)."""
    return sum_power(*potencias)


def delta_to_wye(zdelta):
    """``ZY = Zdelta / 3``."""
    validate_input("numeric", zdelta, "Zdelta")
    validate_input("nonzero", zdelta, "Zdelta")
    return zdelta / 3


def wye_to_delta(zy):
    """``Zdelta = 3 * ZY``."""
    validate_input("numeric", zy, "ZY")
    validate_input("nonzero", zy, "ZY")
    return 3 * zy
