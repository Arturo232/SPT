"""Pruebas del módulo de circuitos monofásicos.

En MATLAB no existe una suite dedicada; aquí se verifica el comportamiento
básico de serie/paralelo R-X y de los circuitos serie/paralelo.
"""

from analizador.errors import AnalizadorError
from analizador.modules.circuitos import (solve_parallel_circuit,
                                          solve_parallel_rx,
                                          solve_series_circuit,
                                          solve_series_rx)

from .conftest import raises_codigo


def test_serie_rx(tol):
    r = solve_series_rx(10, 20)
    assert abs(r.Z - (10 + 20j)) < tol
    assert abs(r.Zmag - (10 ** 2 + 20 ** 2) ** 0.5) < tol


def test_paralelo_rx(tol):
    r = solve_parallel_rx(10, 20)
    # Y = 1/10 + 1/(j20) ; Zeq = 1/Y
    y = 1 / 10 + 1 / (20j)
    z_esperada = 1 / y
    assert abs(r.Zeq - z_esperada) < tol


def test_serie_circuito(tol):
    r = solve_series_circuit(200, 10 + 20j)
    assert abs(r.I - (4 - 8j)) < tol
    assert abs(r.S - (800 + 1600j)) < tol


def test_paralelo_circuito(tol):
    r = solve_parallel_circuit(200, 100, 10 + 20j)
    y = 1 / 100 + 1 / (10 + 20j)
    z_eq = 1 / y
    assert abs(r.Zeq - z_eq) < tol
    i_esperada = 200 / z_eq
    assert abs(r.I - i_esperada) < tol


def test_errores():
    raises_codigo(lambda: solve_parallel_rx(10, 0),
                  "analizador:circuitosMonofasicos:Xcero")
    raises_codigo(lambda: solve_parallel_circuit(200),
                  "analizador:circuitosMonofasicos:sinImpedancias")
