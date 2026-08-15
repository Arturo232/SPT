"""Fixtures y helpers compartidos de las pruebas."""

import numpy as np
import pytest

from analizador.errors import AnalizadorError


@pytest.fixture
def tol():
    return 1e-9


def verificar_campos(result, campos):
    """Verifica que el resultado contenga todos los campos exigidos."""
    actual = set(result.__dict__.keys())
    for campo in campos:
        assert campo in actual, "Falta el campo %s" % campo


def raises_codigo(fn, codigo):
    """Chequea que ``fn`` lance un ``AnalizadorError`` con el código dado."""
    with pytest.raises(AnalizadorError) as exc:
        fn()
    assert exc.value.codigo == codigo, (
        "Se esperaba la excepcion %s y se obtuvo %s"
        % (codigo, exc.value.codigo))
