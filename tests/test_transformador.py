"""Pruebas del módulo de transformadores (equivalente a ``testTransformador.m``)."""

import math

from analizador.modules.transformadores import (ideal_transformer,
                                                per_unit_transformer,
                                                three_phase_transformer,
                                                transformer_equivalent,
                                                transformer_loss_efficiency,
                                                voltage_regulation)
from analizador.services import service_transformador

from .conftest import raises_codigo


def test_transformador_ideal(tol):
    t = ideal_transformer(480, 100, 20)
    assert abs(t.a - 5) < tol
    assert abs(t.V2 - 96) < tol
    t2 = ideal_transformer(480, 100, 20, 2)
    assert abs(t2.I2 - 10) < tol


def test_impedancia_equivalente(tol):
    assert abs(transformer_equivalent(5, 0.5 + 0.3j, "primario") - (12.5 + 7.5j)) < tol
    assert abs(transformer_equivalent(5, 12.5 + 7.5j, "secundario") - (0.5 + 0.3j)) < tol
    assert abs(transformer_equivalent(5, 0.5 + 0.3j) - (12.5 + 7.5j)) < tol


def test_regulacion():
    assert abs(voltage_regulation(120, 115) - 4.3478260869) < 1e-6


def test_eficiencia(tol):
    e = transformer_loss_efficiency(1000, 50)
    assert abs(e.eficiencia - 95.2380952381) < 1e-6
    assert abs(e.Pin - 1050) < tol


def test_per_unit_transformer():
    p = per_unit_transformer(0.05, 100e6, 13.8e3, 50e6, 13.8e3)
    assert abs(p.Zpu_sistema - 0.025) < 1e-12


def test_trifasico(tol):
    t3 = three_phase_transformer(5, "Y", "Y")
    assert abs(t3.r - 0.2) < tol
    assert t3.desfase_deg == 0
    t4 = three_phase_transformer(5, "Y", "Delta")
    assert abs(t4.r - 1 / (math.sqrt(3) * 5)) < tol
    assert t4.desfase_deg == -30
    t5 = three_phase_transformer(5, "Delta", "Y")
    assert abs(t5.r - math.sqrt(3) / 5) < tol
    assert t5.desfase_deg == 30


def test_errores():
    raises_codigo(lambda: three_phase_transformer(5, "X", "Y"),
                         "analizador:transformadores:conexionInvalida")
    raises_codigo(lambda: transformer_equivalent(5, 1, "mal"),
                         "analizador:transformadores:ladoInvalido")
    raises_codigo(lambda: ideal_transformer(480, 100, 0),
                         "analizador:core:noPositivo")


def test_servicio(tol):
    res = service_transformador(480, 100, 20, 0.5 + 0.3j)
    assert hasattr(res, "meta")
    assert abs(res.V2 - 96) < tol
    assert abs(res.Zprimario_ref - (12.5 + 7.5j)) < tol
    res_err = service_transformador(480, 100, 0, 1)
    assert isinstance(res_err, dict) and "codigo" in res_err
