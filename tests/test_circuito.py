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
                  "TENSIONES EN LA CARGA", "POTENCIA",
                  "Tension de fase", "FP"):
        assert clave in reporte, "Falta '%s' en el reporte" % clave


def test_todas_las_variables_fuente():
    """Verifica Vf/VL de fuente, caida de linea y tensiones de carga."""
    c = CircuitoTrifasico()
    c.set_fuente(208, 0)
    c.set_linea(0.1 + 0.05j)
    c.agregar_carga("Y", 30 + 40j)
    r = c.resolver()

    # Vf de la fuente = VL/sqrt(3)
    assert abs(abs(r.v_fuente_fase) - 208 / math.sqrt(3)) < 1e-9
    # fasor de línea de la fuente conserva la magnitud VL
    assert abs(abs(r.v_fuente_linea) - 208) < 1e-9
    # balance de tensiones: Vf_fuente = V_carga + I*Z_linea
    assert abs(r.v_fuente_fase - (r.v_carga + r.v_caida_linea)) < 1e-9
    # caida de linea = I*Z_linea
    assert abs(r.v_caida_linea - r.i_linea * r.z_linea) < 1e-9


def test_detalle_por_carga_y():
    """Carga en Y: I_f = I_L, V_L = sqrt(3)*V_f."""
    c = CircuitoTrifasico()
    c.set_fuente(208, 0)
    c.agregar_carga("Y", 30 + 40j)
    r = c.resolver()
    det = r.cargas[0]
    assert det["conexion"] == "Y"
    # If = IL ; VL = sqrt(3)*|Vf|
    assert abs(det["i_fase"] - det["i_linea"]) < 1e-9
    assert abs(abs(det["v_linea_fasor"]) - math.sqrt(3) * abs(det["v_fase"])) < 1e-9
    # S de la carga es 1/3 del total cuando hay una sola carga
    assert abs(det["P"] - r.P) < 1e-9
    assert abs(det["Q"] - r.Q) < 1e-9


def test_detalle_por_carga_delta():
    """Carga en Delta: I_f = I_L/sqrt(3), V_f = V_L."""
    c = CircuitoTrifasico()
    c.set_fuente(208, 0)
    c.agregar_carga("Delta", 30 + 40j)
    r = c.resolver()
    det = r.cargas[0]
    assert det["conexion"] == "Delta"
    assert abs(abs(det["i_fase"]) - abs(det["i_linea"]) / math.sqrt(3)) < 1e-9
    assert abs(abs(det["v_fase"]) - abs(det["v_linea_fasor"])) < 1e-9
    # S de la carga igual al total
    assert abs(det["P"] - r.P) < 1e-9


def test_comandos_consulta_variables():
    """Los comandos de consulta individual funcionan tras resolver."""
    c = CircuitoTrifasico()
    _ejecutar_comando(c, "fuente 208")
    _ejecutar_comando(c, "carga Y 30+40j")
    _ejecutar_comando(c, "resolver")
    # no deben lanzar excepciones
    for cmd in ("variables", "vl", "vf", "il", "if", "s", "detalle 1", "ver"):
        _ejecutar_comando(c, cmd)
    # antes de resolver, consultas devuelven mensaje (sin excepcion)
    c2 = CircuitoTrifasico()
    _ejecutar_comando(c2, "fuente 208")
    _ejecutar_comando(c2, "carga Y 30+40j")
    for cmd in ("vl", "vf", "il", "if", "s", "variables"):
        _ejecutar_comando(c2, cmd)


def test_fuente_desde_voltaje_de_fase():
    """Si el dato es V_f, se deriva V_L = sqrt(3)*V_f."""
    c = CircuitoTrifasico()
    c.set_fuente(120, 0, "fase")
    assert abs(c.v_linea - 120 * math.sqrt(3)) < 1e-9
    assert abs(abs(c.v_fuente_fase) - 120) < 1e-9
    assert abs(c.v_fuente_fase.real - 120) < 1e-9

    # equivalente a definir V_L directamente
    c2 = CircuitoTrifasico()
    c2.set_fuente(120 * math.sqrt(3), 0, "linea")
    assert abs(c.v_fuente_fase - c2.v_fuente_fase) < 1e-9


def test_fuente_desde_linea_por_defecto():
    c = CircuitoTrifasico()
    c.set_fuente(208)
    assert abs(c.v_linea - 208) < 1e-9
    assert abs(abs(c.v_fuente_fase) - 208 / math.sqrt(3)) < 1e-9


def test_comando_fuente_fase():
    c = CircuitoTrifasico()
    _ejecutar_comando(c, "fuente 120 fase")
    assert abs(c.v_linea - 120 * math.sqrt(3)) < 1e-9
    assert abs(abs(c.v_fuente_fase) - 120) < 1e-9
    # con angulo
    _ejecutar_comando(c, "fuente 100 f 30")
    assert abs(abs(c.v_fuente_fase) - 100) < 1e-9
    assert abs(np.rad2deg(np.angle(c.v_fuente_fase)) - 30) < 1e-9
    # compatibilidad: fuente <VL> [angulo]
    _ejecutar_comando(c, "fuente 208 15")
    assert abs(c.v_linea - 208) < 1e-9
    assert abs(np.rad2deg(np.angle(c.v_fuente_fase)) - 15) < 1e-9


def test_errores_estado():
    c = CircuitoTrifasico()
    raises_codigo(lambda: c.impedancia_equivalente(),
                  "analizador:circuito:sinCargas")
    # sin cargas: error sinCargas antes que sinDatos
    raises_codigo(lambda: c.resolver(), "analizador:circuito:sinCargas")
    # con carga pero sin fuente/corriente/tension: error sinDatos
    c.agregar_carga("Y", 30 + 40j)
    raises_codigo(lambda: c.resolver(), "analizador:circuito:sinDatos")
    c2 = CircuitoTrifasico()
    raises_codigo(lambda: c2.reporte(), "analizador:circuito:sinResolver")


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


def test_parse_impedancia_polar():
    """Impedancia en forma polar: M angulo A."""
    from analizador.asistente import parse_impedancia
    import cmath
    z = parse_impedancia(["30", "angulo", "53.13"])
    esperado = 30 * (math.cos(math.radians(53.13)) + 1j * math.sin(math.radians(53.13)))
    assert abs(z - esperado) < 1e-6
    z2 = parse_impedancia(["50", "/", "30"])
    esperado2 = 50 * (math.cos(math.radians(30)) + 1j * math.sin(math.radians(30)))
    assert abs(z2 - esperado2) < 1e-6


def test_parse_impedancia_rx():
    """Impedancia por R y X separados."""
    from analizador.asistente import parse_impedancia
    z = parse_impedancia(["10", "20"])
    assert abs(z - (10 + 20j)) < 1e-9
    z2 = parse_impedancia(["-0.2", "0.05"])
    assert abs(z2 - (-0.2 + 0.05j)) < 1e-9


def test_corriente_como_dato():
    """Con la corriente dada, la fuente se deriva: V_f = I * Z_total."""
    c = CircuitoTrifasico()
    c.set_corriente(5)  # I_L = 5 A angulo 0
    c.set_linea(0j)
    c.agregar_carga("Y", 30 + 40j)
    r = c.resolver()
    # Z_eq = 30+40j, I = 5 -> V_f = 150 + j200
    assert abs(r.v_fuente_fase - (150 + 200j)) < 1e-9
    assert abs(abs(r.i_linea) - 5) < 1e-9
    # S = V*conj(I) = (150+j200)*5 = 750 + j1000 por fase -> x3
    assert abs(r.P - 2250) < 1e-6


def test_vcarga_como_dato():
    """Con la tension en la carga dada, la fuente se deriva."""
    c = CircuitoTrifasico()
    c.set_v_carga(110 - 20j)
    c.set_linea(2 + 4j)
    c.agregar_carga("Y", 30 + 40j)
    r = c.resolver()
    # I = V_carga / Z_eq = (110-20j)/(30+40j) = 1 - 2j
    assert abs(r.i_linea - (1 - 2j)) < 1e-9
    # V_fuente = V_carga + I*Z_linea = (110-20j) + (1-2j)(2+4j)
    esperado = (110 - 20j) + (1 - 2j) * (2 + 4j)
    assert abs(r.v_fuente_fase - esperado) < 1e-9


def test_carga_por_potencia():
    """Carga por potencia S -> impedancia Z = |V|^2 / conj(S_fase)."""
    c = CircuitoTrifasico()
    c.set_fuente(200, 0, "fase")  # V_L = 200*sqrt(3), V_f = 200
    c.agregar_carga_por_potencia("Y", 1200 + 1600j)
    # S_fase = (1200+1600j)/3 ; V_f = 200 ; Z = |200|^2 / conj(S_fase)
    s_fase = (1200 + 1600j) / 3
    z_esp = (200 ** 2) / np.conjugate(s_fase)
    assert abs(c.cargas[0]["z_fase"] - z_esp) < 1e-6
    assert c.cargas[0]["por_potencia"] is True


def test_comandos_variantes():
    c = CircuitoTrifasico()
    _ejecutar_comando(c, "corriente 5")
    assert abs(c.i_fuente - 5) < 1e-9
    _ejecutar_comando(c, "carga Y 30 40")        # R y X separados
    assert abs(c.cargas[0]["z_fase"] - (30 + 40j)) < 1e-9
    _ejecutar_comando(c, "linea 2+4j")
    _ejecutar_comando(c, "resolver")
    assert c.resultado is not None

    # vcarga y pcarga
    c2 = CircuitoTrifasico()
    _ejecutar_comando(c2, "vcarga 110-20j")
    assert abs(c2.v_carga_dato - (110 - 20j)) < 1e-9
    _ejecutar_comando(c2, "carga Y 30+40j")
    _ejecutar_comando(c2, "resolver")

    c3 = CircuitoTrifasico()
    _ejecutar_comando(c3, "fuente 200 fase")
    _ejecutar_comando(c3, "pcarga Y 1200+1600j")
    assert c3.cargas[0]["por_potencia"] is True
