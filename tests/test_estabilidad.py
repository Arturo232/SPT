"""Pruebas del módulo de estabilidad (equivalente a ``testEstabilidad.m``)."""

import math

from analizador.modules.estabilidad import (critical_clearing_time,
                                            equal_area_criterion,
                                            swing_equation)
from analizador.services import service_estabilidad

from .conftest import raises_codigo


def test_swing_equation(tol):
    s = swing_equation(1.0, 0.8, 5, 60)
    assert abs(s.Pa - 0.2) < 1e-9
    assert abs(s.M - 2 * 5 / (2 * math.pi * 60)) < 1e-9


def test_areas_iguales(tol=1e-4):
    ea = equal_area_criterion(1.0, 2.0, 0)
    assert abs(ea.delta0_deg - 30) < tol
    assert abs(ea.deltaCr_deg - 79.56) < 0.05
    assert abs(ea.deltaMax_deg - 150) < tol
    assert abs(ea.A1 - ea.A2) < 1e-6


def test_tiempo_critico(tol=1e-3):
    ea = equal_area_criterion(1.0, 2.0, 0)
    tc = critical_clearing_time(1.0, ea.delta0_deg, ea.deltaCr_deg, 5, 60)
    assert abs(tc.tcr - 0.2142) < tol


def test_servicio(tol=1e-3):
    res = service_estabilidad(1.0, 2.0, 0, 5, 60)
    assert hasattr(res, "meta")
    assert abs(res.deltaCr_deg - 79.56) < 0.05
    assert abs(res.tcr - 0.2142) < tol


def test_errores():
    raises_codigo(lambda: equal_area_criterion(2.5, 2.0, 0),
                         "analizador:estabilidad:PmExcede")
    raises_codigo(lambda: critical_clearing_time(1.0, 80, 70, 5, 60),
                         "analizador:estabilidad:deltaCrInvalido")
    res_err = service_estabilidad(2.5, 2.0, 0, 5, 60)
    assert isinstance(res_err, dict) and "codigo" in res_err
