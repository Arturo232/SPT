"""Pruebas de formateo y exportación (equivalente a ``testFormato.m``)."""

import json
import os
import tempfile

import numpy as np

from analizador.services import service_analizar_carga
from analizador.utils import export_results, format_complex, format_power
from analizador.viz import phasor_plot, power_triangle


def test_format_complex():
    rect, polar = format_complex(3 + 4j)
    assert "3 + j4" in rect
    assert "5 angulo" in polar
    r2, p2 = format_complex(4 - 8j)
    assert "4 - j8" in r2
    assert "angulo -63.4349" in p2


def test_format_power():
    s = format_power(1200 + 1600j)
    assert "P = 1200" in s
    assert "Q = 1600" in s
    assert "ATRASO" in s


def test_exportacion_txt_json_csv(tmp_path):
    result = service_analizar_carga("PF", 250e3, 0.9, "inductiva")

    f_txt = export_results(result, str(tmp_path / "analizador_faseF.txt"))
    assert os.path.isfile(f_txt)
    with open(f_txt, encoding="utf-8") as fh:
        contenido = fh.read()
    assert "P = 250000" in contenido

    f_json = export_results(result, str(tmp_path / "analizador_faseF.json"))
    assert os.path.isfile(f_json)
    with open(f_json, encoding="utf-8") as fh:
        datos = json.load(fh)
    assert "P" in datos
    assert "Q" in datos

    f_csv = export_results(result, str(tmp_path / "analizador_faseF.csv"))
    assert os.path.isfile(f_csv)
    with open(f_csv, encoding="utf-8") as fh:
        lineas = fh.readlines()
    assert len(lineas) > 1

    f_xlsx = export_results(result, str(tmp_path / "analizador_faseF.xlsx"))
    assert os.path.isfile(f_xlsx)


def test_extension_automatica(tmp_path):
    result = service_analizar_carga("PF", 250e3, 0.9, "inductiva")
    f_auto = export_results(result, str(tmp_path / "analizador_faseF_auto"))
    assert os.path.isfile(f_auto)
    assert f_auto.endswith(".txt")


def test_graficas_no_fallan():
    ax1 = phasor_plot([120, 120 * np.exp(1j * np.deg2rad(-120)),
                       120 * np.exp(1j * np.deg2rad(120))])
    assert ax1 is not None
    ax2 = power_triangle(1200, 1600)
    assert ax2 is not None
