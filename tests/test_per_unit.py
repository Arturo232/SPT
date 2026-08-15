"""Pruebas del sistema por unidad (equivalente a ``testPerUnit.m``)."""

import math

from analizador.errors import AnalizadorError
from analizador.modules.per_unit import (change_of_base, from_per_unit,
                                         per_unit_base, to_per_unit)
from analizador.services import service_per_unit

from .conftest import raises_codigo


def test_bases_trifasicas(tol):
    base = per_unit_base(100e6, 13.8e3, "trifasico")
    assert base.fases == "trifasico"
    assert abs(base.Zbase - 1.9044) < 1e-4
    assert abs(base.Ibase - 100e6 / (math.sqrt(3) * 13.8e3)) < 1e-6
    assert abs(base.Ybase - 1 / 1.9044) < 1e-6


def test_bases_monofasicas(tol):
    base_mono = per_unit_base(10e3, 480)
    assert base_mono.fases == "monofasico"
    assert abs(base_mono.Zbase - 480 ** 2 / 10e3) < 1e-6
    assert abs(base_mono.Ibase - 10e3 / 480) < 1e-6


def test_conversion(tol):
    base = per_unit_base(100e6, 13.8e3, "trifasico")
    assert abs(to_per_unit(13.8e3, base, "V") - 1) < tol
    assert abs(from_per_unit(1, base, "V") - 13.8e3) < 1e-6
    assert abs(to_per_unit(50e6, base, "S") - 0.5) < tol
    assert abs(from_per_unit(0.5, base, "S") - 50e6) < 1e-6
    assert abs(to_per_unit(0.9522, base, "Z") - 0.5) < 1e-9
    assert abs(from_per_unit(0.5, base, "Z") - 0.9522) < 1e-9


def test_cambio_de_base():
    z_nuevo = change_of_base(0.05, 100e6, 13.8e3, 50e6, 13.8e3)
    assert abs(z_nuevo - 0.025) < 1e-12
    z_nuevo2 = change_of_base(0.05, 100e6, 13.8e3, 100e6, 138e3)
    assert abs(z_nuevo2 - 0.0005) < 1e-12


def test_servicio(tol):
    res = service_per_unit(100e6, 13.8e3, "trifasico", 13.8e3, "V")
    assert hasattr(res, "meta")
    assert abs(res.valor_pu - 1) < tol
    assert res.tipo == "V"
    res_err = service_per_unit(-100e6, 13.8e3, "trifasico")
    assert isinstance(res_err, dict) and "codigo" in res_err


def test_errores():
    base = per_unit_base(100e6, 13.8e3, "trifasico")
    raises_codigo(lambda: per_unit_base(100e6, 13.8e3, "hexafasico"),
                         "analizador:perUnit:fasesInvalida")
    raises_codigo(lambda: to_per_unit(1, base, "X"),
                         "analizador:perUnit:tipoInvalido")
