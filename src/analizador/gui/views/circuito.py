"""Vista: Circuito (monofasico o trifasico balanceado) con estado de cargas.

Desacoplamiento: la vista solo recolecta las entradas y construye un
``CircuitoTrifasico`` / ``CircuitoMonofasico`` (backend en ``circuito.py``);
el calculo y el reporte provienen del backend.
"""

import customtkinter as ctk

from ..components import (Card, LabeledEntry, StatusFeedback, leer_float,
                          leer_float_opcional)
from ...circuito import CircuitoMonofasico, CircuitoTrifasico
from ...errors import AnalizadorError


class CircuitoView(ctk.CTkFrame):
    titulo = "Circuito"

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.cargas = []  # [{"conexion": str|None, "R": float, "X": float}]

        ctk.CTkLabel(self, text="Circuito (fuente + linea + cargas)", anchor="w",
                     font=ctk.CTkFont(size=22, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, sticky="w",
                            padx=24, pady=(18, 4))

        # ------------------ tarjeta: definicion ------------------
        card_in = Card(self, titulo="Definicion del circuito")
        card_in.grid(row=1, column=0, sticky="nsew", padx=(24, 8), pady=8)

        self.modo = ctk.CTkSegmentedButton(
            card_in.cuerpo, values=["Trifasico", "Monofasico"],
            command=self._cambiar_modo)
        self.modo.set("Trifasico")
        self.modo.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # fuente
        self.fuente_mag = LabeledEntry(card_in.cuerpo, "Fuente (magnitud)",
                                       "ej. 207.8", "V")
        self.fuente_mag.grid(row=1, column=0, sticky="ew", pady=4)
        self.fuente_ang = LabeledEntry(card_in.cuerpo, "Angulo de la fuente",
                                       "0", "deg")
        self.fuente_ang.grid(row=2, column=0, sticky="ew", pady=4)
        self.fuente_tipo = ctk.CTkOptionMenu(
            card_in.cuerpo, values=["Linea (VL)", "Fase (Vf)"])
        self.fuente_tipo.grid(row=3, column=0, sticky="ew", pady=(4, 10))

        # linea
        self.linea_r = LabeledEntry(card_in.cuerpo, "R de linea", "ej. 2", "ohm")
        self.linea_r.grid(row=4, column=0, sticky="ew", pady=4)
        self.linea_x = LabeledEntry(card_in.cuerpo, "X de linea", "ej. 4", "ohm")
        self.linea_x.grid(row=5, column=0, sticky="ew", pady=(4, 10))

        # cargas
        ctk.CTkLabel(card_in.cuerpo, text="Cargas en paralelo", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=6, column=0, sticky="w")
        self.conexion = ctk.CTkOptionMenu(card_in.cuerpo, values=["Y", "Delta"])
        self.conexion.grid(row=7, column=0, sticky="ew", pady=(4, 6))
        self.carga_r = LabeledEntry(card_in.cuerpo, "R de la carga", "ej. 30", "ohm")
        self.carga_r.grid(row=8, column=0, sticky="ew", pady=4)
        self.carga_x = LabeledEntry(card_in.cuerpo, "X de la carga", "ej. 40", "ohm")
        self.carga_x.grid(row=9, column=0, sticky="ew", pady=4)

        fila_btn = ctk.CTkFrame(card_in.cuerpo, fg_color="transparent")
        fila_btn.grid(row=10, column=0, sticky="ew", pady=(8, 4))
        fila_btn.grid_columnconfigure(0, weight=1)
        fila_btn.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(fila_btn, text="Agregar carga", height=30,
                      command=self._agregar_carga
                      ).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkButton(fila_btn, text="Limpiar", height=30, fg_color="gray40",
                      hover_color="gray25", command=self._limpiar_cargas
                      ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.lista = ctk.CTkTextbox(card_in.cuerpo, height=90)
        self.lista.grid(row=11, column=0, sticky="ew", pady=(6, 8))
        self._render_lista()

        self.btn = ctk.CTkButton(card_in.cuerpo, text="Resolver circuito",
                                 height=34, command=self._resolver)
        self.btn.grid(row=12, column=0, sticky="ew", pady=(6, 8))
        self.status = StatusFeedback(card_in.cuerpo)
        self.status.grid(row=13, column=0, sticky="ew")

        # ------------------ tarjeta: reporte ------------------
        card_out = Card(self, titulo="Reporte")
        card_out.grid(row=1, column=1, sticky="nsew", padx=(8, 24), pady=8)
        self.texto = ctk.CTkTextbox(card_out.cuerpo, wrap="word")
        self.texto.grid(row=0, column=0, sticky="nsew")
        card_out.cuerpo.grid_rowconfigure(0, weight=1)
        self._escribir("Defina fuente, linea y cargas, luego presione Resolver.")

    # ------------------------------------------------------------------
    def _cambiar_modo(self, valor):
        if valor == "Monofasico":
            self.fuente_tipo.configure(state="disabled")
        else:
            self.fuente_tipo.configure(state="normal")

    def _agregar_carga(self):
        try:
            r = leer_float(self.carga_r.get(), "R de la carga")
            x = leer_float(self.carga_x.get(), "X de la carga")
            conexion = self.conexion.get() if self.modo.get() == "Trifasico" else None
            self.cargas.append({"conexion": conexion, "R": r, "X": x})
            self._render_lista()
            self.status.ok("Carga %d agregada" % len(self.cargas))
        except ValueError as err:
            self.status.error(str(err))

    def _limpiar_cargas(self):
        self.cargas = []
        self._render_lista()
        self.status.ok("Cargas eliminadas")

    def _render_lista(self):
        self.lista.configure(state="normal")
        self.lista.delete("1.0", "end")
        if not self.cargas:
            self.lista.insert("1.0", "(sin cargas)")
        else:
            lineas = []
            for k, c in enumerate(self.cargas, start=1):
                z = "%.4g%+.4gj" % (c["R"], c["X"])
                if c["conexion"]:
                    lineas.append("C%d: %-6s Z = %s" % (k, c["conexion"], z))
                else:
                    lineas.append("C%d: Z = %s" % (k, z))
            self.lista.insert("1.0", "\n".join(lineas))
        self.lista.configure(state="disabled")

    def _resolver(self):
        try:
            self.status.reset()
            self.update_idletasks()
            mag = leer_float(self.fuente_mag.get(), "Fuente")
            ang = leer_float_opcional(self.fuente_ang.get(), "Angulo")
            r_l = leer_float(self.linea_r.get(), "R de linea")
            x_l = leer_float(self.linea_x.get(), "X de linea")
            if not self.cargas:
                raise ValueError("agregue al menos una carga")

            if self.modo.get() == "Trifasico":
                circuito = CircuitoTrifasico()
                dato = "fase" if "Fase" in self.fuente_tipo.get() else "linea"
                circuito.set_fuente(mag, ang, dato)
                circuito.set_linea(r_l + 1j * x_l)
                for c in self.cargas:
                    circuito.agregar_carga(c["conexion"], c["R"] + 1j * c["X"])
            else:
                circuito = CircuitoMonofasico()
                circuito.set_fuente(mag, ang)
                circuito.set_linea(r_l + 1j * x_l)
                for c in self.cargas:
                    circuito.agregar_carga(c["R"] + 1j * c["X"])

            circuito.resolver()
            self._escribir(circuito.reporte())
            self.status.ok("Circuito resuelto")
        except ValueError as err:
            self.status.error(str(err))
        except AnalizadorError as err:
            self.status.error(err.mensaje)

    def _escribir(self, texto):
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", texto)
        self.texto.configure(state="disabled")
