"""Sistema por unidad (equivalente a ``modules/perUnit/*.m``)."""

import math
from types import SimpleNamespace

from ..core import validate_input
from ..errors import error_analizador


def _verificar_base(base, campo):
    """Verifica que la estructura de base contenga un campo requerido."""
    if not isinstance(base, SimpleNamespace) or not hasattr(base, campo):
        error_analizador("perUnit", "baseIncompleta",
                         "Error: la base no contiene el campo {0}.", campo)


def per_unit_base(sbase, vbase, fases="monofasico"):
    """Magnitudes base de un sistema por unidad.

    Monofásico: ``Ibase = Sbase/Vbase``, ``Zbase = Vbase^2/Sbase``.
    Trifásico: ``Ibase = Sbase/(sqrt(3)*Vbase)`` (Vbase línea-línea).
    Regresa ``{fases, Sbase, Vbase, Ibase, Zbase, Ybase}``.
    """
    validate_input("positive", sbase, "Sbase")
    validate_input("positive", vbase, "Vbase")
    c = fases.lower()
    if c in ("monofasico", "mono", "1f", "single"):
        fases_out = "monofasico"
    elif c in ("trifasico", "tri", "3f", "three"):
        fases_out = "trifasico"
    else:
        error_analizador("perUnit", "fasesInvalida",
                         "Error: numero de fases no reconocido: {0}. Use 'monofasico' o 'trifasico'.", fases)
    base = SimpleNamespace()
    base.fases = fases_out
    base.Sbase = sbase
    base.Vbase = vbase
    if fases_out == "trifasico":
        base.Ibase = sbase / (math.sqrt(3) * vbase)
    else:
        base.Ibase = sbase / vbase
    base.Zbase = (vbase ** 2) / sbase
    base.Ybase = 1 / base.Zbase
    return base


def to_per_unit(valor, base, tipo):
    """Convierte un valor real a p.u. (``V/I/S/Z`` por campo ``tipo``)."""
    validate_input("numeric", valor, "valor")
    t = tipo.upper()
    if t == "V":
        _verificar_base(base, "Vbase")
        return valor / base.Vbase
    if t == "I":
        _verificar_base(base, "Ibase")
        return valor / base.Ibase
    if t == "S":
        _verificar_base(base, "Sbase")
        return valor / base.Sbase
    if t == "Z":
        _verificar_base(base, "Zbase")
        return valor / base.Zbase
    error_analizador("perUnit", "tipoInvalido",
                     "Error: tipo no valido: {0}. Use V, I, S o Z.", tipo)


def from_per_unit(pu, base, tipo):
    """Convierte un valor en p.u. a su equivalente real."""
    validate_input("numeric", pu, "pu")
    t = tipo.upper()
    if t == "V":
        _verificar_base(base, "Vbase")
        return pu * base.Vbase
    if t == "I":
        _verificar_base(base, "Ibase")
        return pu * base.Ibase
    if t == "S":
        _verificar_base(base, "Sbase")
        return pu * base.Sbase
    if t == "Z":
        _verificar_base(base, "Zbase")
        return pu * base.Zbase
    error_analizador("perUnit", "tipoInvalido",
                     "Error: tipo no valido: {0}. Use V, I, S o Z.", tipo)


def change_of_base(z_pu_viejo, sbase_viejo, vbase_viejo, sbase_nuevo, vbase_nuevo):
    """Cambio de base de una impedancia en p.u.

    ``Zpu_nuevo = Zpu_viejo * (Sbase_nuevo/Sbase_viejo) * (Vbase_viejo/Vbase_nuevo)^2``
    """
    validate_input("numeric", z_pu_viejo, "zPuViejo")
    validate_input("positive", sbase_viejo, "SbaseViejo")
    validate_input("positive", vbase_viejo, "VbaseViejo")
    validate_input("positive", sbase_nuevo, "SbaseNuevo")
    validate_input("positive", vbase_nuevo, "VbaseNuevo")
    return z_pu_viejo * (sbase_nuevo / sbase_viejo) * (vbase_viejo / vbase_nuevo) ** 2
