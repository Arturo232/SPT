"""Pruebas del módulo de corrección de FP (equivalente a ``testCorreccionFP.m``)."""

from analizador.errors import AnalizadorError
from analizador.modules.correccion_fp import (capacitor_kvar,
                                              capacitor_reactance,
                                              capacitor_value,
                                              corrected_power_factor,
                                              required_reactive_power)

from .conftest import raises_codigo


def test_required_reactive_power(tol):
    comp = required_reactive_power(1200, 0.6, 0.8)
    assert abs(comp.Q1 - 1600) < tol
    assert abs(comp.Q2 - 900) < tol
    assert abs(comp.Qc - 700) < tol
    assert comp.requiereCompensacion == "capacitiva"


def test_capacitor_reactance(tol):
    comp = required_reactive_power(1200, 0.6, 0.8)
    xc = capacitor_reactance(200, comp.Qc)
    assert abs(xc.Xc - 40000 / 700) < tol


def test_capacitor_value():
    comp = required_reactive_power(1200, 0.6, 0.8)
    xc = capacitor_reactance(200, comp.Qc)
    cap = capacitor_value(60, xc.Xc)
    assert abs(cap.C_uF - 46.42) < 0.01


def test_corrected_power_factor(tol):
    comp = required_reactive_power(1200, 0.6, 0.8)
    corregido = corrected_power_factor(1200, comp.Q1, -comp.Qc)
    assert abs(corregido.fp - 0.8) < tol
    assert corregido.type == "inductiva"


def test_capacitor_kvar(tol):
    assert abs(capacitor_kvar(8000) - 8) < tol


def test_errores():
    raises_codigo(lambda: required_reactive_power(1200, 1.2, 0.8),
                         "analizador:core:fpInvalido")
    raises_codigo(lambda: capacitor_reactance(200, 0),
                         "analizador:correccionFP:QcCero")
    raises_codigo(lambda: capacitor_value(-60, 10),
                         "analizador:core:frecuenciaInvalida")
