"""Pruebas del entorno de circuito trifásico (clase + asistente + consola)."""

import math

import numpy as np

from analizador.asistente import _ejecutar_comando, parse_complejo
from analizador.circuito import CircuitoTrifasico
from analizador.errors import AnalizadorError

from .conftest import raises_codigo


def test_parse_complejo():
    assert abs(parse_complejo("10+5j") - (10 + 5j)) < 1e-9
    assert abs(parse_complejo("2-8j") - (2 - 8j)) < 1e-9
    assert abs(parse_complejo("4j") - 4j) < 1e-9
    assert abs(parse_complejo("10") - 10) < 1e-9
    assert abs(parse_complejo("-0.2 + 0.05j") - (-0.2 + 0.05j)) < 1e-9
    raises_codigo(lambda: parse_complejo("abc"),
                  "analizador:circuito:complejoInvalido")


def test_conversion_delta_y_transparente():
    c = CircuitoTrifasico()
    c.agregar_carga("Delta", 30 + 40j)
    assert c.cargas[0]["conexion"] == "Delta"
    assert abs(c.cargas[0]["z_y"] - (10 + 40j / 3)) < 1e-9


def test_impedancia_equivalente_paralelo():
    c = CircuitoTrifasico()
    c.agregar_carga("Y", 30 + 40j)
    c.agregar_carga("Y", 20 - 15j)
    y_eq = 1 / (30 + 40j) + 1 / (20 - 15j)
    z_eq = 1 / y_eq
    assert abs(c.impedancia_equivalente() - z_eq) < 1e-9


def test_resolver_material_aceptacion():
    """Caso del material (test_trifasico): fuente 120*sqrt(3), linea 2+4j,
    cargas Y 30+40j y Y 20-15j."""
    c = CircuitoTrifasico()
    c.set_fuente(120 * math.sqrt(3), 0)
    c.set_linea(2 + 4j)
    c.agregar_carga("Y", 30 + 40j)
    c.agregar_carga("Y", 20 - 15j)

    r = c.resolver()
    assert abs(abs(r.i_linea) - 5) < 1e-6
    assert abs(r.P - 1800) < 1e-6
    assert abs(r.Q - 0) < 1e-6
    assert abs(abs(r.v_carga) - math.sqrt(110 ** 2 + 20 ** 2)) < 1e-3
    assert abs(abs(r.v_carga) * math.sqrt(3) - 193.64) < 1e-2


def test_resolver_con_delta():
    """Una carga en Delta equivale a su Y / 3: mismos resultados."""
    c = CircuitoTrifasico()
    c.set_fuente(208, 0)
    c.set_linea(0.1 + 0.05j)
    c.agregar_carga("Delta", 30 + 40j)
    r_delta = c.resolver()

    c2 = CircuitoTrifasico()
    c2.set_fuente(208, 0)
    c2.set_linea(0.1 + 0.05j)
    c2.agregar_carga("Y", (30 + 40j) / 3)
    r_y = c2.resolver()

    assert abs(r_delta.P - r_y.P) < 1e-9
    assert abs(r_delta.z_eq - r_y.z_eq) < 1e-9
    assert abs(abs(r_delta.i_linea) - abs(r_y.i_linea)) < 1e-9


def test_estado_acumulativo():
    """Z_eq queda guardada para operaciones acumulativas (sin anotar)."""
    c = CircuitoTrifasico()
    c.set_fuente(208, 0)
    c.agregar_carga("Y", 30 + 40j)
    c.resolver()
    assert c.z_eq is not None
    assert c.z_total is not None
    # la impedancia equivalente sirve como base para una nueva carga en serie
    z_prev = c.z_eq
    c.set_linea(0.5 + 0.2j)
    c.resolver()
    assert abs(c.z_total - (z_prev + 0.5 + 0.2j)) < 1e-9


def test_reporte_incluye_datos_clave():
    c = CircuitoTrifasico()
    c.set_fuente(208, 0)
    c.agregar_carga("Y", 30 + 40j)
    c.resolver()
    reporte = c.reporte()
    for clave in ("Impedancia equivalente", "Corriente de linea",
                  "Tension en la carga", "Potencia compleja total",
                  "FP"):
        assert clave in reporte, "Falta '%s' en el reporte" % clave


def test_errores_estado():
    c = CircuitoTrifasico()
    raises_codigo(lambda: c.impedancia_equivalente(),
                  "analizador:circuito:sinCargas")
    raises_codigo(lambda: c.resolver(), "analizador:circuito:sinFuente")
    raises_codigo(lambda: c.reporte(), "analizador:circuito:sinResolver")


def test_consola_comandos():
    """Verifica el parser natural mediante _ejecutar_comando (sin input())."""
    c = CircuitoTrifasico()
    _ejecutar_comando(c, "fuente 208")
    assert abs(c.v_linea - 208) < 1e-9
    _ejecutar_comando(c, "linea 0.1+0.05j")
    assert abs(c.z_linea - (0.1 + 0.05j)) < 1e-9
    _ejecutar_comando(c, "carga Delta 30+40j")
    _ejecutar_comando(c, "add Y 20-15j")
    assert len(c.cargas) == 2
    _ejecutar_comando(c, "resolver")
    assert c.resultado is not None
    _ejecutar_comando(c, "cargas")
    _ejecutar_comando(c, "limpiar")
    assert len(c.cargas) == 0
    # comando desconocido lanza error controlado
    try:
        _ejecutar_comando(c, "zzz 1")
        assert False, "Deberia haber lanzado AnalizadorError"
    except AnalizadorError as err:
        assert err.codigo == "analizador:circuito:comandoDesconocido"


def test_consola_ayuda_y_salida():
    c = CircuitoTrifasico()
    _ejecutar_comando(c, "ayuda")
    _ejecutar_comando(c, "ver")
    assert c is not None
