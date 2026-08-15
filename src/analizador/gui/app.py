"""Ventana principal de la GUI: sidebar + area de trabajo dinamica.

Arquitectura del layout:
  - Sidebar (CTkFrame fijo a la izquierda, ancho constante): titulo,
    botones de navegacion con hover y selector de tema (Dark/Light/System).
  - Main canvas (derecha): area dinamica que intercambia la vista segun
    la opcion seleccionada en el sidebar.
Las vistas (cards) solo invocan funciones del backend; aqui no hay
logica de negocio.
"""

import customtkinter as ctk

from .views.circuito import CircuitoView
from .views.correccion import CorreccionView
from .views.per_unit import PerUnitView
from .views.potencia import PotenciaView

_ANCHO_SIDEBAR = 220


class SPTApp(ctk.CTk):
    """Ventana principal del SPT."""

    VISTAS = [
        ("Potencia compleja", PotenciaView),
        ("Correccion de FP", CorreccionView),
        ("Circuito", CircuitoView),
        ("Sistema p.u.", PerUnitView),
    ]

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("SPT — Sistemas de Potencia en Terminal")
        self.geometry("1060x680")
        self.minsize(900, 580)

        # grid responsivo: col 0 sidebar fija, col 1 area principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._crear_sidebar()
        self.canvas = ctk.CTkFrame(self, fg_color="transparent")
        self.canvas.grid(row=0, column=1, sticky="nsew")
        self.canvas.grid_columnconfigure(0, weight=1)
        self.canvas.grid_rowconfigure(0, weight=1)

        self.vista_actual = None
        self._marcar_activo(self.VISTAS[0][0])
        self.mostrar(self.VISTAS[0][0])

    # ------------------------------------------------------------------
    def _crear_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=_ANCHO_SIDEBAR, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sidebar, text="SPT", anchor="w",
                     font=ctk.CTkFont(size=26, weight="bold")
                     ).grid(row=0, column=0, sticky="ew", padx=20,
                            pady=(24, 0))
        ctk.CTkLabel(sidebar, text="Sistemas de Potencia", anchor="w",
                     font=ctk.CTkFont(size=12), text_color="gray60"
                     ).grid(row=1, column=0, sticky="ew", padx=20,
                            pady=(0, 18))

        # botones de navegacion (hover nativo de CTkButton)
        self.botones = {}
        fila = 2
        for nombre, _ in self.VISTAS:
            btn = ctk.CTkButton(
                sidebar, text=nombre, anchor="w", height=38,
                fg_color="transparent", hover_color=("gray70", "gray28"),
                command=lambda n=nombre: self.mostrar(n))
            btn.grid(row=fila, column=0, sticky="ew", padx=12, pady=3)
            self.botones[nombre] = btn
            fila += 1

        # selector de tema (al final del sidebar)
        ctk.CTkLabel(sidebar, text="Tema", anchor="w",
                     font=ctk.CTkFont(size=12), text_color="gray60"
                     ).grid(row=fila + 1, column=0, sticky="w", padx=20,
                            pady=(24, 4))
        self.tema = ctk.CTkSegmentedButton(
            sidebar, values=["Dark", "Light", "System"],
            command=self._cambiar_tema, height=28)
        self.tema.set("Dark")
        self.tema.grid(row=fila + 2, column=0, sticky="ew", padx=16)

    def _cambiar_tema(self, valor):
        ctk.set_appearance_mode(valor.lower())

    def _marcar_activo(self, nombre):
        """Resalta el boton activo del sidebar."""
        for n, btn in self.botones.items():
            if n == nombre:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")

    def mostrar(self, nombre):
        """Intercambia la vista del main canvas."""
        if self.vista_actual is not None:
            self.vista_actual.destroy()
        clase = dict(self.VISTAS)[nombre]
        self.vista_actual = clase(self.canvas)
        self.vista_actual.grid(row=0, column=0, sticky="nsew")
        self._marcar_activo(nombre)


def main():
    """Punto de entrada de la GUI (``analizador-gui``)."""
    app = SPTApp()
    app.mainloop()


if __name__ == "__main__":
    main()
