"""Pruebas del núcleo matemático (equivalente a ``tests/testCore.m``)."""

import math

import numpy as np

from analizador.core import (admittance_from_impedance, apparent_power,
                             complex_power, complex_to_polar,
                             current_from_power,
                             current_from_voltage_impedance,
                             impedance_from_admittance, impedance_from_power,
                             polar_to_complex, power_factor, power_from_vi,
                             validate_input,
                             voltage_from_current_impedance)
from analizador.errors import AnalizadorError

from .conftest import raises_codigo


def test_polar_rectangular(tol):
    z = polar_to_complex(2, 30)
    assert abs(np.real(z) - 2 * np.cos(np.deg2rad(30))) < tol
    assert abs(np.imag(z) - 2 * np.sin(np.deg2rad(30))) < tol

    p = complex_to_polar(3 + 4j)
    assert abs(p.mag - 5) < tol
    assert abs(p.angleDeg - np.rad2deg(math.atan2(4, 3))) < tol


def test_complex_power(tol):
    V = 200
    I = 4 - 8j
    S = complex_power(V, I)
    assert abs(np.real(S) - 800) < tol
    assert abs(np.imag(S) - 1600) < tol


def test_ohm_laws(tol):
    V = 200
    Z = 10 + 20j
    I = current_from_voltage_impedance(V, Z)
    assert abs(I - (4 - 8j)) < tol
    assert abs(voltage_from_current_impedance(I, Z) - V) < tol
    assert abs(current_from_power(complex_power(V, I), V) - I) < tol
    assert abs(impedance_from_power(V, complex_power(V, I)) - Z) < tol

    Y = admittance_from_impedance(Z)
    assert abs(impedance_from_admittance(Y) - Z) < tol


def test_power_factor(tol):
    fp = power_factor(1200 + 1600j)
    assert abs(fp.fp - 0.6) < tol
    assert fp.type == "inductiva"
    fp_cap = power_factor(1200 - 1600j)
    assert fp_cap.type == "capacitiva"


def test_apparent_power(tol):
    assert abs(apparent_power(1200, 1600) - 2000) < tol


def test_power_from_vi(tol):
    V = 200
    I = 4 - 8j
    res = power_from_vi(V, I)
    assert abs(res.P - 800) < tol
    assert abs(res.Q - 1600) < tol
    assert abs(res.Sabs - 1788.8544) < 1e-3
    assert abs(res.fp - 0.4472) < 1e-3
    assert res.type == "inductiva"
    assert abs(res.phi_deg - np.rad2deg(math.atan2(1600, 800))) < tol


def test_validate_input():
    raises_codigo(lambda: validate_input("fp", 1.2),
                         "analizador:core:fpInvalido")
    raises_codigo(lambda: validate_input("fp", -0.3),
                         "analizador:core:fpInvalido")
    raises_codigo(lambda: validate_input("frequency", -60),
                         "analizador:core:frecuenciaInvalida")
    raises_codigo(lambda: current_from_voltage_impedance(200, 0),
                         "analizador:core:cero")
