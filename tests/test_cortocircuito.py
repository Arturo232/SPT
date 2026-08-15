"""Pruebas de cortocircuitos (equivalente a ``testCortocircuito.m``)."""

from analizador.modules.cortocircuitos import (double_line_to_ground_fault,
                                               line_to_line_fault,
                                               single_line_to_ground_fault,
                                               three_phase_fault_current)
from analizador.services import service_cortocircuito

from .conftest import raises_codigo


def _setup():
    return 1.0, 1j * 0.1, 1j * 0.1, 1j * 0.1


def test_trifasica(tol):
    vf, z1, z2, z0 = _setup()
    r = three_phase_fault_current(vf, z1)
    assert abs(abs(r.If) - 10) < tol


def test_slg(tol):
    vf, z1, z2, z0 = _setup()
    r = single_line_to_ground_fault(vf, z1, z2, z0, 0)
    assert abs(r.I1 - (1 / (0.3j))) < tol
    assert abs(r.If_mag - 10) < tol
    assert abs(r.Ib) < tol and abs(r.Ic) < tol


def test_ll(tol):
    vf, z1, z2, z0 = _setup()
    r = line_to_line_fault(vf, z1, z2, 0)
    assert abs(r.I1 - (1 / (0.2j))) < tol
    assert abs(abs(r.Ib) - 5 * (3 ** 0.5)) < tol
    assert abs(r.Ia) < tol


def test_llg(tol):
    vf, z1, z2, z0 = _setup()
    r = double_line_to_ground_fault(vf, z1, z2, z0, 0)
    assert abs(r.I1 - (1 / (0.15j))) < tol
    assert abs(r.I0 - r.I2) < tol
    assert abs(r.Ia) < tol
    assert abs(abs(r.Ib) - 10) < tol


def test_servicio(tol):
    vf, z1, z2, z0 = _setup()
    res = service_cortocircuito("slg", vf, z1, z2, z0, 0)
    assert hasattr(res, "meta")
    assert abs(res.If_mag - 10) < tol
    res3 = service_cortocircuito("3f", vf, z1, z2, z0)
    assert abs(res3.If_mag - 10) < tol
    res_err = service_cortocircuito("xx", vf, z1, z2, z0)
    assert isinstance(res_err, dict) and "codigo" in res_err


def test_errores():
    raises_codigo(lambda: three_phase_fault_current(1.0, 0),
                         "analizador:core:cero")
