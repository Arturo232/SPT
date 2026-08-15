"""Pruebas del flujo de potencia de dos fuentes (equivalente a ``testFlujoPotencia.m``)."""

import math

import numpy as np

from analizador.core import polar_to_complex
from analizador.errors import AnalizadorError
from analizador.modules.flujo_potencia import (active_power_flow,
                                               maximum_transfer_power,
                                               power_flow_two_bus,
                                               reactive_power_flow)

from .conftest import raises_codigo


def test_flujos_reactivos(tol):
    p12 = active_power_flow(1, 30, 1, 0, 0.1)
    assert abs(p12 - 5) < tol
    q12 = reactive_power_flow(1, 30, 1, 0, 0.1)
    assert abs(q12 - (1 - math.cos(math.radians(30))) / 0.1) < tol
    p_max = maximum_transfer_power(1, 1, 0.1)
    assert abs(p_max - 10) < tol


def test_power_flow_two_bus(tol):
    res = power_flow_two_bus(1, 30, 1, 0, 1j * 0.1)
    assert abs(res.P12_reactivo - 5) < tol
    assert abs(res.P12_reactivo - res.P12) < 1e-9
    assert abs(res.Pmax - 10) < tol

    i_esperada = (polar_to_complex(1, 30) - 1) / (1j * 0.1)
    assert abs(res.I12 - i_esperada) < tol
    assert abs(abs(res.I12) - abs(i_esperada)) < tol


def test_linea_con_r():
    res2 = power_flow_two_bus(1, 30, 1, 0, 0.05 + 1j * 0.1)
    assert not hasattr(res2, "P12_reactivo")


def test_errores():
    raises_codigo(lambda: active_power_flow(1, 30, 1, 0, 0),
                         "analizador:core:noPositivo")
    raises_codigo(lambda: power_flow_two_bus(1, 30, 1, 0, 0),
                         "analizador:core:cero")
