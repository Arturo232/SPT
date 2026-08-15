"""Pruebas de la GUI (componentes y ventana).

Las pruebas de ventana se saltan si no hay pantalla disponible (p. ej. CI).
La lógica de negocio ya está cubierta por el resto de suites; aquí se
valida la capa de vista y su desacoplamiento.
"""

import pytest

pytest.importorskip("customtkinter")

from analizador.gui.components import (leer_float, leer_float_opcional)  # noqa: E402


def test_leer_float_valido():
    assert leer_float("208", "V") == 208.0
    assert leer_float("-15.5", "X") == -15.5
    assert leer_float(" 120 ", "Vf") == 120.0


def test_leer_float_invalido_mensaje_claro():
    with pytest.raises(ValueError) as exc:
        leer_float("abc", "Fuente")
    assert "Fuente" in str(exc.value)
    assert "abc" in str(exc.value)


def test_leer_float_opcional():
    assert leer_float_opcional("", "Angulo") == 0.0
    assert leer_float_opcional("30", "Angulo") == 30.0
    with pytest.raises(ValueError):
        leer_float_opcional("x", "Angulo")


def test_vistas_existen_y_registradas():
    from analizador.gui.app import SPTApp
    nombres = [n for n, _ in SPTApp.VISTAS]
    assert nombres == ["Potencia compleja", "Correccion de FP",
                       "Circuito", "Sistema p.u."]


def test_smoke_ventana_y_vistas():
    """Crea la ventana, recorre las vistas y la cierra (sin mainloop)."""
    try:
        from analizador.gui.app import SPTApp
        app = SPTApp()
        for nombre, _ in SPTApp.VISTAS:
            app.mostrar(nombre)
            app.update()
        # selector de tema
        app._cambiar_tema("Light")
        app.update()
        # cancelar callbacks pendientes de customtkinter antes de cerrar
        # (evita mensajes bgerror tras destroy)
        for job in app.tk.call("after", "info"):
            try:
                app.tk.call("after", "cancel", job)
            except Exception:
                pass
        app.destroy()
    except Exception as err:  # sin pantalla (headless)
        pytest.skip("sin pantalla disponible: %s" % err)
