"""Pruebas del flujo de carga N-barras (equivalente a ``testFlujoCarga.m``)."""

import math

import numpy as np

from analizador.modules.flujo_potencia import (bus_structure,
                                               caso2_barras, ejemplo3_barras,
                                               gauss_seidel_power_flow,
                                               line_structure,
                                               newton_raphson_power_flow,
                                               power_mismatch, ybus_matrix,
                                               zbus_matrix)
from analizador.services import service_flujo_carga

from .conftest import raises_codigo


def test_ybus_2_barras():
    b2, l2 = caso2_barras()
    y = ybus_matrix(2, l2)
    assert abs(y[0, 0] + 10j) < 1e-12
    assert abs(y[0, 1] - 10j) < 1e-12
    assert abs(y[1, 0] - 10j) < 1e-12
    assert abs(y[1, 1] + 10j) < 1e-12


def test_zbus_3_barras():
    b3, l3 = ejemplo3_barras()
    y3 = ybus_matrix(3, l3)
    z3 = zbus_matrix(y3)
    assert np.max(np.abs(z3 @ y3 - np.eye(3))) < 1e-8


def test_newton_raphson_2_barras():
    b2, l2 = caso2_barras()
    r2 = newton_raphson_power_flow(b2, l2)
    assert r2.converged
    assert abs(r2.V[1] - 0.998746) < 1e-3
    assert abs(r2.delta_deg[1] - 2.8696) < 0.01
    assert abs(r2.Pslack + 0.5) < 1e-3
    m2 = power_mismatch(r2.V, r2.delta, r2.Ybus, b2)
    assert np.max(np.abs(np.concatenate([m2.dP, m2.dQ]))) < 1e-6


def test_newton_raphson_3_barras():
    b3, l3 = ejemplo3_barras()
    r3 = newton_raphson_power_flow(b3, l3)
    assert r3.converged
    assert abs(r3.V[1] - 0.984951) < 1e-4
    assert abs(r3.delta_deg[1] + 0.84919) < 1e-3
    assert abs(r3.delta_deg[2] - 0.98912) < 1e-3
    assert abs(r3.Pslack - 0.003810) < 1e-4
    assert abs(r3.perdidas - 0.003810) < 1e-4
    m3 = power_mismatch(r3.V, r3.delta, r3.Ybus, b3)
    assert np.max(np.abs(np.concatenate([m3.dP, m3.dQ]))) < 1e-6


def test_gauss_seidel_misma_solucion():
    b3, l3 = ejemplo3_barras()
    r3 = newton_raphson_power_flow(b3, l3)
    g3 = gauss_seidel_power_flow(b3, l3)
    assert g3.converged
    assert np.max(np.abs(g3.V - r3.V)) < 1e-4
    assert np.max(np.abs(g3.delta - r3.delta)) < 1e-4


def test_balance_potencias():
    b3, l3 = ejemplo3_barras()
    r3 = newton_raphson_power_flow(b3, l3)
    p_especificada = [b.P for b in b3]
    assert abs(r3.perdidas - (r3.Pslack + sum(p_especificada[1:]))) < 1e-9


def test_servicio():
    b3, l3 = ejemplo3_barras()
    res = service_flujo_carga(b3, l3, "nr")
    assert hasattr(res, "meta")
    assert res.converged
    assert res.metodo == "Newton-Raphson"
    res_gs = service_flujo_carga(b3, l3, "gs")
    assert res_gs.converged
    res_err = service_flujo_carga(b3, l3, "xx")
    assert isinstance(res_err, dict) and "codigo" in res_err


def test_errores_estructura():
    raises_codigo(lambda: bus_structure(1, "swing"),
                         "analizador:flujoCarga:tipoBarraInvalido")
    raises_codigo(
        lambda: newton_raphson_power_flow([bus_structure(1, "pq")],
                                          [line_structure(1, 1, 0.02, 0.1, 0)]),
        "analizador:flujoCarga:sinSlack")
