"""Pruebas del módulo de potencia compleja (equivalente a ``testPotenciaCompleja.m``)."""

import numpy as np

from analizador.core import impedance_from_admittance
from analizador.modules.potencia_compleja import (load_power_from_z,
                                                  solve_carga, source_current,
                                                  sum_power)


def test_caso_base(tol):
    V = 200
    z1 = 100
    z2 = 10 + 20j

    s1 = load_power_from_z(V, z1)
    s2 = load_power_from_z(V, z2)
    stotal = sum_power(s1, s2)

    assert abs(s1.I - 2) < tol
    assert abs(s2.I - (4 - 8j)) < tol
    assert abs(s1.S - 400) < tol
    assert abs(s2.S - (800 + 1600j)) < tol
    assert abs(stotal.S - (1200 + 1600j)) < tol
    assert abs(stotal.Sabs - 2000) < tol
    assert abs(stotal.fp - 0.6) < tol

    i = source_current(stotal.S, V)
    assert abs(i - (6 - 8j)) < tol
    assert abs(abs(i) - 10) < tol


def test_flujo_a(tol):
    ra = solve_carga("VI", 200, 6 - 8j)
    assert abs(ra.S - (1200 + 1600j)) < tol


def test_flujo_b(tol):
    z1 = 100
    z2 = 10 + 20j
    z_paralelo = impedance_from_admittance(1 / z1 + 1 / z2)
    rb = solve_carga("VZ", 200, z_paralelo)
    assert abs(rb.S - (1200 + 1600j)) < 1e-6


def test_flujo_c(tol):
    rc = solve_carga("PF", 1200, 0.6, "inductiva")
    assert abs(rc.Q - 1600) < tol
    assert rc.type == "inductiva"
    rd = solve_carga("PF", 1200, 0.6, "capacitiva")
    assert abs(rd.Q + 1600) < tol
    assert rd.type == "capacitiva"
