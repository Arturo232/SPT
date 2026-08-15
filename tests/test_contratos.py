"""Pruebas de los contratos de datos (equivalente a ``tests/testContratos.m``)."""

from analizador.config import default_config, mensajes
from analizador.core import power_from_vi
from analizador.modules.potencia_compleja import load_power_from_z, solve_carga
from analizador.modules.sistemas_trifasicos import solve_three_phase_load
from analizador.services import (service_corregir_fp, service_flujo_dos_fuentes)

from .conftest import verificar_campos


def test_estructura_carga():
    campos_carga = {"V", "I", "S", "P", "Q", "Sabs", "fp", "phi_deg", "type"}
    campos_base = {"S", "P", "Q", "Sabs", "fp", "phi_deg", "type"}
    r1 = power_from_vi(200, 4 - 8j)
    verificar_campos(r1, campos_carga)
    r2 = load_power_from_z(200, 10 + 20j)
    verificar_campos(r2, campos_carga)
    r3 = solve_carga("PF", 1200, 0.6, "inductiva")
    verificar_campos(r3, campos_base)


def test_estructura_correccion_fp():
    campos = {"Q1", "Q2", "Qc", "Xc", "C_F", "C_uF", "fp_corregido", "type"}
    r4 = service_corregir_fp(1200, 0.6, 0.8, 200, 60)
    verificar_campos(r4, campos)


def test_estructura_flujo():
    campos = {"I12", "S12", "P12", "Q12"}
    r5 = service_flujo_dos_fuentes(1, 30, 1, 0, 1j * 0.1)
    verificar_campos(r5, campos)


def test_estructura_trifasica():
    campos = {"VL", "Vf", "If", "IL", "S", "P", "Q", "fp", "type"}
    r6 = solve_three_phase_load(120 * (3 ** 0.5), "Y", 24 + 0j)
    verificar_campos(r6, campos)


def test_bloque_meta():
    r4 = service_corregir_fp(1200, 0.6, 0.8, 200, 60)
    r5 = service_flujo_dos_fuentes(1, 30, 1, 0, 1j * 0.1)
    assert hasattr(r4, "meta")
    assert hasattr(r5, "meta")
    assert hasattr(r4.meta, "formulas") and isinstance(r4.meta.formulas, list)


def test_catalogo_mensajes():
    cat = mensajes()
    assert isinstance(cat, dict)
    assert "analizador:core:fpInvalido" in cat
    assert "analizador:correccionFP:QcCero" in cat
    assert "analizador:sistemasTrifasicos:conexionInvalida" in cat


def test_configuracion():
    cfg = default_config()
    assert "frequency" in cfg
    assert cfg["frequency"] > 0
    assert cfg["tolerance"] > 0
