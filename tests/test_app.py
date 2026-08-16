"""Pruebas de la lógica pura de la GUI (equivalente a ``testApp.m``)."""

from types import SimpleNamespace

from analizador.core.resolver import resolver_calculo


def test_potencia_pf():
    v = SimpleNamespace(P=250000, fp=0.9, tipo="inductiva")
    texto, r = resolver_calculo("potenciaPF", v)
    assert "Q = 121081" in texto
    assert hasattr(r, "meta")


def test_correccion_fp():
    v = SimpleNamespace(P=1200, fp1=0.6, fp2=0.8, V=200, f=60)
    texto, r = resolver_calculo("correccionFP", v)
    assert "Qc = 700" in texto
    assert abs(r.C_uF - 46.42) < 0.01


def test_carga_vz():
    v = SimpleNamespace(Vmag=200, Vang=0, R=10, X=20)
    _, r = resolver_calculo("cargaVZ", v)
    assert abs(r.I - (4 - 8j)) < 1e-9


def test_trifasico():
    import math
    v = SimpleNamespace(VL=120 * math.sqrt(3), conexion="Y", R=24, X=0)
    _, r = resolver_calculo("trifasico", v)
    assert abs(r.P - 1800) < 1e-6


def test_per_unit():
    v = SimpleNamespace(Sbase=100e6, Vbase=13.8e3, fases="trifasico",
                        valor=13.8e3, tipoMag="V")
    _, r = resolver_calculo("perUnit", v)
    assert abs(r.valor_pu - 1) < 1e-9


def test_error_controlado():
    v = SimpleNamespace(P=250000, fp=1.5, tipo="inductiva")
    texto = resolver_calculo("potenciaPF", v)[0]
    assert "ERROR" in texto
