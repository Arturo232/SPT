"""Pruebas unitarias de las funcionalidades avanzadas de la consola y menús."""

import os
from unittest.mock import patch

from analizador.services.asistente import SesionConsola, _ejecutar_comando
from analizador.core.circuito import CircuitoTrifasico, CircuitoMonofasico


def test_pcarga_con_v_nominal_tri():
    sesion = SesionConsola()
    sesion.cambiar_modo("tri")
    # Agregar carga por potencia indicando V_nominal explícito (208 V)
    _ejecutar_comando(sesion, "pcarga Delta 1200+900j 208")
    assert len(sesion.circuito.cargas) == 1
    c = sesion.circuito.cargas[0]
    assert c["conexion"] == "Delta"
    assert c["por_potencia"] is True
    # Z_fase = 208^2 / conj(1200/3 + j900/3) = 43264 / (400 - 300j) = 43264 * (400 + 300j) / 250000 = 69.2224 + j51.9168
    assert abs(c["z_fase"].real - 69.2224) < 1e-3


def test_pcarga_con_v_nominal_mono():
    sesion = SesionConsola()
    sesion.cambiar_modo("mono")
    _ejecutar_comando(sesion, "pcarga 1200+600j 120")
    assert len(sesion.circuito.cargas) == 1
    c = sesion.circuito.cargas[0]
    # En mono, la carga es directamente la impedancia Z
    # Z = 120^2 / conj(1200 + 600j) = 14400 / (1200 - 600j) = 14400*(1200+600j)/1800000 = 9.6 + j4.8
    assert abs(c.real - 9.6) < 1e-3
    assert abs(c.imag - 4.8) < 1e-3


def test_consola_exportar(tmp_path):
    sesion = SesionConsola()
    sesion.cambiar_modo("tri")
    _ejecutar_comando(sesion, "fuente 208")
    _ejecutar_comando(sesion, "linea 0.1+0.05j")
    _ejecutar_comando(sesion, "carga Delta 30+40j")
    _ejecutar_comando(sesion, "resolver")

    archivo_txt = str(tmp_path / "test_reporte.txt")
    archivo_json = str(tmp_path / "test_reporte.json")
    archivo_csv = str(tmp_path / "test_reporte.csv")

    _ejecutar_comando(sesion, f"exportar txt {archivo_txt}")
    assert os.path.exists(archivo_txt)
    with open(archivo_txt, "r", encoding="utf-8") as f:
        contenido = f.read()
        assert "CIRCUITO TRIFASICO" in contenido

    _ejecutar_comando(sesion, f"exportar json {archivo_json}")
    assert os.path.exists(archivo_json)

    _ejecutar_comando(sesion, f"exportar csv {archivo_csv}")
    assert os.path.exists(archivo_csv)


def test_consola_grafica():
    sesion = SesionConsola()
    sesion.cambiar_modo("tri")
    _ejecutar_comando(sesion, "fuente 208")
    _ejecutar_comando(sesion, "carga Y 10+5j")
    _ejecutar_comando(sesion, "resolver")

    with patch("matplotlib.pyplot.show"):
        _ejecutar_comando(sesion, "grafica")
        _ejecutar_comando(sesion, "grafica potencia")
