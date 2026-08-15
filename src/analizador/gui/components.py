"""Componentes reutilizables de la GUI.

Solo vista: no contienen lógica de negocio (esa vive en ``services``,
``resolver`` y ``circuito``). Aquí se define la apariencia (cards,
entradas con placeholder, barra de estado con feedback visual) y las
validaciones básicas de entrada.
"""

import customtkinter as ctk

# Colores de estado (independientes del tema claro/oscuro)
_OK = "#2fa572"
_ERROR = "#e5534b"
_NEUTRO = "gray60"


class Card(ctk.CTkFrame):
    """Tarjeta (CTkFrame secundario) con borde redondeado y contraste leve.

    Uso: ``card = Card(master, titulo="Entradas")`` y colocar los controles
    dentro de ``card.cuerpo`` con ``grid()``.
    """

    def __init__(self, master, titulo=None, **kwargs):
        super().__init__(master, corner_radius=12, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        fila = 0
        if titulo:
            ctk.CTkLabel(
                self, text=titulo, anchor="w",
                font=ctk.CTkFont(size=15, weight="bold"),
            ).grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
            fila = 1
        self.cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        self.cuerpo.grid(row=fila, column=0, sticky="nsew", padx=16,
                         pady=(0, 16))
        self.cuerpo.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(fila, weight=1)


class LabeledEntry(ctk.CTkFrame):
    """Etiqueta + campo de texto (CTkEntry) con placeholder y unidad.

    La unidad se muestra entre corchetes al lado de la etiqueta
    (p. ej. ``P [W]``) para que siempre esté visible.
    """

    def __init__(self, master, etiqueta, placeholder="", unidad=""):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        texto = etiqueta + ("  [%s]" % unidad if unidad else "")
        ctk.CTkLabel(self, text=texto, anchor="w",
                     font=ctk.CTkFont(size=12),
                     text_color=_NEUTRO).grid(row=0, column=0, sticky="w",
                                              pady=(0, 2))
        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder)
        self.entry.grid(row=1, column=0, sticky="ew")

    def get(self):
        return self.entry.get().strip()


def leer_float(valor, nombre):
    """Valida y convierte una entrada a float.

    Lanza ``ValueError`` con un mensaje claro para el usuario (se muestra
    en la barra de estado como alerta visual).
    """
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise ValueError("%s debe ser un numero (recibido: '%s')"
                         % (nombre, valor))


def leer_float_opcional(valor, nombre, por_defecto=0.0):
    """Como ``leer_float`` pero acepta vacio (usa el valor por defecto)."""
    if valor == "":
        return por_defecto
    return leer_float(valor, nombre)


class StatusFeedback(ctk.CTkFrame):
    """Barra de estado: mensaje coloreado + barra de progreso.

    Feedback visual inmediato: verde con check para exito, rojo con X para
    error, y una barra de progreso que se llena al completar el calculo.
    """

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.label = ctk.CTkLabel(self, text="Listo.", anchor="w",
                                  font=ctk.CTkFont(size=12))
        self.label.grid(row=0, column=0, sticky="w")
        self.progress = ctk.CTkProgressBar(self, height=6)
        self.progress.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self.progress.set(0)

    def reset(self):
        """Estado de carga: se muestra al iniciar un calculo."""
        self.label.configure(text="Calculando...", text_color=_NEUTRO)
        self.progress.set(0.15)

    def ok(self, mensaje):
        self.label.configure(text="OK  %s" % mensaje, text_color=_OK)
        self.progress.set(1.0)

    def error(self, mensaje):
        self.label.configure(text="ERROR  %s" % mensaje, text_color=_ERROR)
        self.progress.set(0)
