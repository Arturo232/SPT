"""Pruebas de componentes simétricas (equivalente a ``testComponentesSimetricas.m``)."""

import numpy as np

from analizador.modules.componentes_simetricas import (abc_to_sequence,
                                                       operador_a,
                                                       sequence_to_abc)
from analizador.services import service_componentes_simetricas

from .conftest import raises_codigo


def test_operador_a(tol):
    a = operador_a()
    assert abs(abs(a) - 1) < tol
    assert abs(np.rad2deg(np.angle(a)) - 120) < tol


def test_secuencia_positiva_pura(tol):
    x = 10
    abc_pos = np.array([x, x * np.exp(1j * np.deg2rad(-120)),
                        x * np.exp(1j * np.deg2rad(120))])
    seq = abc_to_sequence(abc_pos)
    assert abs(seq[0]) < 1e-9
    assert abs(seq[1] - 10) < tol
    assert abs(seq[2]) < 1e-9


def test_secuencia_negativa_pura(tol):
    x = 10
    abc_neg = np.array([x, x * np.exp(1j * np.deg2rad(120)),
                        x * np.exp(1j * np.deg2rad(-120))])
    seq = abc_to_sequence(abc_neg)
    assert abs(seq[0]) < 1e-9
    assert abs(seq[1]) < 1e-9
    assert abs(seq[2] - 10) < tol


def test_sistema_desbalanceado(tol):
    abc = np.array([10, 10 * np.exp(1j * np.deg2rad(-120)), 0])
    seq = abc_to_sequence(abc)
    assert abs(seq[0] - 10 * np.exp(1j * np.deg2rad(-60)) / 3) < tol
    assert abs(seq[1] - 20 / 3) < tol
    assert abs(seq[2] - 10 * np.exp(1j * np.deg2rad(60)) / 3) < tol


def test_round_trip(tol):
    abc = np.array([10, 10 * np.exp(1j * np.deg2rad(-120)), 0])
    recuperado = sequence_to_abc(abc_to_sequence(abc))
    assert np.max(np.abs(recuperado - abc)) < tol


def test_servicio(tol):
    abc = np.array([10, 10 * np.exp(1j * np.deg2rad(-120)), 0])
    res = service_componentes_simetricas("abc012", abc)
    assert hasattr(res, "meta")
    assert abs(res.seq[1] - 20 / 3) < tol
    res2 = service_componentes_simetricas("012abc", abc_to_sequence(abc))
    assert np.max(np.abs(res2.xabc - abc)) < tol


def test_errores():
    raises_codigo(lambda: abc_to_sequence(np.array([1, 2])),
                         "analizador:componentesSimetricas:noTrifasico")
