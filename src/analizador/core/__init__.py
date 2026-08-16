"""Paquete core: lógica matemática y de dominio puro del analizador.

Re-exporta las funciones elementales de ``base.py`` y los componentes
principales de modelado/resolución para mantener compatibilidad con los
imports absolutos existentes (``from analizador.core import ...``).
"""

from .base import (
    admittance_from_impedance,
    apparent_power,
    balance_potencias,
    complex_power,
    complex_to_polar,
    current_from_power,
    current_from_voltage_impedance,
    deg2rad,
    impedance_from_admittance,
    impedance_from_power,
    polar_to_complex,
    power_factor,
    power_from_vi,
    rad2deg,
    validate_input,
    voltage_from_current_impedance,
)
from .circuito import CircuitoMonofasico, CircuitoTrifasico
from .exercises import (
    exercise01,
    exercise02,
    exercise03,
    exercise04,
    exercise05,
    menu_ejercicios,
    menu_ejemplos,
)
from .resolver import resolver_calculo

__all__ = [
    "admittance_from_impedance",
    "apparent_power",
    "balance_potencias",
    "complex_power",
    "complex_to_polar",
    "current_from_power",
    "current_from_voltage_impedance",
    "deg2rad",
    "impedance_from_admittance",
    "impedance_from_power",
    "polar_to_complex",
    "power_factor",
    "power_from_vi",
    "rad2deg",
    "validate_input",
    "voltage_from_current_impedance",
    "CircuitoMonofasico",
    "CircuitoTrifasico",
    "exercise01",
    "exercise02",
    "exercise03",
    "exercise04",
    "exercise05",
    "menu_ejercicios",
    "menu_ejemplos",
    "resolver_calculo",
]
