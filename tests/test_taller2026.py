"""Pruebas de aceptación: los 5 ejercicios del taller 2026.

Equivalente a ``tests/testTaller2026.m``. Los ejercicios solo consumen
funciones generales y se validan contra valores de referencia.
"""

from analizador.exercises import (exercise01, exercise02, exercise03,
                                  exercise04, exercise05)


def test_ejercicio1():
    r1 = exercise01()
    assert abs(r1["Q"] - 121081) < 1
    assert abs(r1["R"] - 0.7465) < 1e-4
    assert abs(r1["X"] - 0.3615) < 1e-4


def test_ejercicio2():
    r2 = exercise02()
    assert abs(r2["R"] - 0.7465) < 1e-4
    assert abs(r2["X"] - 0.3615) < 1e-4


def test_ejercicio3():
    r3 = exercise03()
    assert abs(r3["Qt"] - 21691) < 1
    assert abs(r3["Q1"] + 8217) < 1
    assert abs(r3["S2"] - (10000 + 29908j)) < 1


def test_ejercicio4():
    r4 = exercise04()
    assert abs(r4["Pload"] - 640e3) < 1
    assert abs(r4["Qload"] + 480e3) < 1
    assert abs(r4["Iload"] - (533.3333 + 400j)) < 1
    assert abs(r4["R"] - 2.25) < 1e-3
    assert abs(r4["Xc"] + 3) < 1e-3
    assert abs(r4["Vfuente"] - (1200 + 9333.333j)) < 1e-2


def test_ejercicio5():
    r5 = exercise05()
    assert abs(r5["S1"] - (1000 + 7000j)) < 1
    assert abs(r5["S2"] - (1000 - 2000j)) < 1
    assert abs(r5["S3"] - (4000 + 3000j)) < 1
    assert abs(r5["Stotal"] - (6000 + 8000j)) < 1
    assert abs(r5["I"] - (30 - 40j)) < 1e-6
    assert abs(abs(r5["I"]) - 50) < 1e-6
    assert abs(r5["fp"] - 0.6) < 1e-6
    assert abs(r5["Qc"] + 8000) < 1e-6
    assert abs(r5["C_uF"] - 530.52) < 0.1
    assert abs(abs(r5["Inew"]) - 30) < 1e-6
    assert abs(r5["fp_corregido"] - 1) < 1e-9
