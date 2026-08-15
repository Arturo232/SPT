"""Pruebas del módulo de máquinas eléctricas (equivalente a ``testMaquinas.m``)."""

import numpy as np

from analizador.modules.maquinas import power_angle_curve, sync_generator_emf
from analizador.services import service_maquina_sincrona

from .conftest import raises_codigo


def test_fem_interna(tol):
    v = 1.0
    i = 0.64 - 0.48j
    r = sync_generator_emf(v, i, 1.0, 0)
    assert abs(r.E - (1.48 + 0.64j)) < 1e-9
    assert abs(r.E_mag - abs(1.48 + 0.64j)) < 1e-9
    assert abs(r.delta_deg - np.rad2deg(np.angle(1.48 + 0.64j))) < 1e-9


def test_curva_potencia_angulo(tol):
    p = power_angle_curve(1, 1, 0.5, 30)
    assert abs(p.P - 1.0) < tol
    assert abs(p.Pmax - 2.0) < tol
    p2 = power_angle_curve(1, 1, 0.5, 90)
    assert abs(p2.P - 2.0) < tol


def test_servicio(tol):
    v = 1.0
    i = 0.64 - 0.48j
    res = service_maquina_sincrona("fem", v, i, 1.0, 0)
    assert hasattr(res, "meta")
    assert abs(res.E - (1.48 + 0.64j)) < 1e-6
    res_p = service_maquina_sincrona("potencia", 1, 1, 0.5, 30)
    assert abs(res_p.P - 1.0) < tol


def test_errores():
    raises_codigo(lambda: power_angle_curve(1, 1, 0, 30),
                         "analizador:core:noPositivo")
