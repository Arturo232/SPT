"""Pruebas del módulo de sistemas trifásicos (equivalente a ``testTrifasico.m``)."""

import math

import numpy as np

from analizador.core import (admittance_from_impedance, current_from_voltage_impedance,
                             impedance_from_admittance, polar_to_complex,
                             rad2deg, voltage_from_current_impedance)
from analizador.modules.sistemas_trifasicos import (assert_balanced,
                                                    delta_to_wye,
                                                    line_voltage_from_phase,
                                                    phase_voltage_from_line,
                                                    solve_three_phase_load,
                                                    three_phase_power_from_line,
                                                    three_phase_power_from_phase,
                                                    wye_to_delta)
from analizador.services import service_trifasico_carga


def test_aceptacion_material(tol=1e-3):
    VL = 120 * math.sqrt(3)
    z_linea = 2 + 4j
    z1 = 30 + 40j
    z2 = 20 - 15j

    vf = polar_to_complex(phase_voltage_from_line(VL, "Y"), 0)

    z_carga = impedance_from_admittance(
        admittance_from_impedance(z1) + admittance_from_impedance(z2))
    z_total = z_linea + z_carga
    i_fuente = current_from_voltage_impedance(vf, z_total)

    s_fuente = three_phase_power_from_phase(vf, i_fuente)
    assert abs(s_fuente.P - 1800) < 1e-6
    assert abs(s_fuente.Q - 0) < 1e-6
    assert abs(abs(i_fuente) - 5) < 1e-6

    vf_carga = voltage_from_current_impedance(i_fuente, z_carga)
    assert abs(abs(vf_carga) - math.sqrt(110 ** 2 + 20 ** 2)) < tol
    assert abs(line_voltage_from_phase(abs(vf_carga), "Y") - 193.64) < 1e-2
    assert abs(rad2deg(np.angle(vf_carga)) + 30 - 19.7) < 1e-1

    i1 = current_from_voltage_impedance(vf_carga, z1)
    i2 = current_from_voltage_impedance(vf_carga, z2)
    assert abs(abs(i1) - 2.236) < tol
    assert abs(abs(i2) - 4.472) < tol
    assert abs(rad2deg(np.angle(i1)) + 63.4) < 1e-1
    assert abs(rad2deg(np.angle(i2)) - 26.5) < 1e-1

    s1 = three_phase_power_from_phase(vf_carga, i1)
    s2 = three_phase_power_from_phase(vf_carga, i2)
    v_linea = voltage_from_current_impedance(i_fuente, z_linea)
    s_linea = three_phase_power_from_phase(v_linea, i_fuente)
    assert abs(s1.P - 450) < 1e-6 and abs(s1.Q - 600) < 1e-6
    assert abs(s2.P - 1200) < 1e-6 and abs(s2.Q + 900) < 1e-6
    assert abs(s_linea.P - 150) < 1e-6 and abs(s_linea.Q - 300) < 1e-6


def test_transformaciones(tol):
    assert abs(delta_to_wye(30 + 40j) - (10 + 40j / 3)) < tol
    assert abs(wye_to_delta(10 + 40j / 3) - (30 + 40j)) < tol


def test_potencia_desde_linea():
    pot = three_phase_power_from_line(120 * math.sqrt(3), 5, 0)
    assert abs(pot.P - 1800) < 1e-6
    assert abs(pot.Q - 0) < 1e-6


def test_balance():
    van = polar_to_complex(120, 0)
    vbn = polar_to_complex(120, -120)
    vcn = polar_to_complex(120, 120)
    ok, _ = assert_balanced([van, vbn, vcn])
    assert ok


def test_servicio():
    res = service_trifasico_carga(120 * math.sqrt(3), "Y", 24 + 0j)
    assert hasattr(res, "meta")
    assert abs(res.P - 1800) < 1e-6
