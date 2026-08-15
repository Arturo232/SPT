"""Pruebas de la capa de servicios (equivalente a ``tests/testServices.m``)."""

from analizador.services import (service_analizar_carga, service_circuitos,
                                 service_corregir_fp, service_flujo_dos_fuentes)


def _es_error(result):
    return isinstance(result, dict) and "codigo" in result


def test_service_circuitos():
    r1 = service_circuitos("serierx", 10, 20)
    assert abs(r1.Z - (10 + 20j)) < 1e-9
    assert hasattr(r1, "meta")
    r1e = service_circuitos("invalido")
    assert _es_error(r1e)


def test_service_analizar_carga():
    ra = service_analizar_carga("PF", 250e3, 0.9, "inductiva")
    assert abs(ra.Q - 121081) < 1
    rb = service_analizar_carga("VI", 200, 4 - 8j)
    assert abs(rb.S - (800 + 1600j)) < 1e-9
    rc = service_analizar_carga("VZ", 200, 10 + 20j)
    assert abs(rc.I - (4 - 8j)) < 1e-9
    rd = service_analizar_carga("SUM", 400 + 0j, 800 + 1600j)
    assert abs(rd.S - (1200 + 1600j)) < 1e-9
    re = service_analizar_carga("SOURCE", 1200, 1600, 200)
    assert abs(re.I - (6 - 8j)) < 1e-9
    rf = service_analizar_carga("XX")
    assert _es_error(rf)


def test_service_corregir_fp():
    rg = service_corregir_fp(1200, 0.6, 0.8, 200, 60)
    assert abs(rg.Qc - 700) < 1e-9
    assert abs(rg.C_uF - 46.42) < 0.01
    assert abs(rg.fp_corregido - 0.8) < 1e-9
    assert hasattr(rg, "meta")
    rg2 = service_corregir_fp(1200, 1.2, 0.8, 200, 60)
    assert _es_error(rg2)
    assert rg2["codigo"] == "analizador:core:fpInvalido"


def test_service_flujo_dos_fuentes():
    rh = service_flujo_dos_fuentes(1, 30, 1, 0, 1j * 0.1)
    assert abs(rh.P12 - 5) < 1e-9
    assert hasattr(rh, "meta")
    rh2 = service_flujo_dos_fuentes(1, 30, 1, 0, 0)
    assert _es_error(rh2)
