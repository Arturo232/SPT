"""Vista: Sistema por unidad (p.u.).

Desacoplamiento: llama a ``resolver_calculo('perUnit', datos)``.
"""

from types import SimpleNamespace

import customtkinter as ctk

from ..components import Card, LabeledEntry, StatusFeedback, leer_float
from ...core.resolver import resolver_calculo


class PerUnitView(ctk.CTkFrame):
    titulo = "Sistema p.u."

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Sistema por unidad (p.u.)", anchor="w",
                     font=ctk.CTkFont(size=22, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, sticky="w",
                            padx=24, pady=(18, 4))

        # ------------------ tarjeta: entradas ------------------
        card_in = Card(self, titulo="Entradas")
        card_in.grid(row=1, column=0, sticky="nsew", padx=(24, 8), pady=8)

        self.fases = ctk.CTkSegmentedButton(card_in.cuerpo,
                                            values=["Monofasico", "Trifasico"])
        self.fases.set("Trifasico")
        self.fases.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.in_s = LabeledEntry(card_in.cuerpo, "Sbase", "ej. 100e6", "VA")
        self.in_s.grid(row=1, column=0, sticky="ew", pady=4)
        self.in_v = LabeledEntry(card_in.cuerpo, "Vbase", "ej. 13.8e3", "V")
        self.in_v.grid(row=2, column=0, sticky="ew", pady=4)
        self.in_valor = LabeledEntry(card_in.cuerpo, "Valor real", "ej. 13.8e3", "-")
        self.in_valor.grid(row=3, column=0, sticky="ew", pady=4)

        ctk.CTkLabel(card_in.cuerpo, text="Tipo de magnitud", anchor="w",
                     font=ctk.CTkFont(size=12), text_color="gray60"
                     ).grid(row=4, column=0, sticky="w", pady=(6, 2))
        self.tipo = ctk.CTkOptionMenu(card_in.cuerpo, values=["V", "I", "S", "Z"])
        self.tipo.grid(row=5, column=0, sticky="ew")

        self.btn = ctk.CTkButton(card_in.cuerpo, text="Calcular", height=34,
                                 command=self._calcular)
        self.btn.grid(row=6, column=0, sticky="ew", pady=(14, 8))
        self.status = StatusFeedback(card_in.cuerpo)
        self.status.grid(row=7, column=0, sticky="ew")

        # ------------------ tarjeta: resultados ------------------
        card_out = Card(self, titulo="Resultados")
        card_out.grid(row=1, column=1, sticky="nsew", padx=(8, 24), pady=8)
        self.texto = ctk.CTkTextbox(card_out.cuerpo, wrap="word")
        self.texto.grid(row=0, column=0, sticky="nsew")
        card_out.cuerpo.grid_rowconfigure(0, weight=1)
        self._escribir("Ingrese los datos y presione Calcular.")

    def _calcular(self):
        try:
            self.status.reset()
            self.update_idletasks()
            datos = SimpleNamespace(
                Sbase=leer_float(self.in_s.get(), "Sbase"),
                Vbase=leer_float(self.in_v.get(), "Vbase"),
                fases="trifasico" if self.fases.get() == "Trifasico" else "monofasico",
                valor=leer_float(self.in_valor.get(), "Valor real"),
                tipoMag=self.tipo.get(),
            )
            texto, _ = resolver_calculo("perUnit", datos)
            if texto.startswith("ERROR"):
                self.status.error(texto.replace("ERROR\n", "", 1))
            else:
                self._escribir(texto)
                self.status.ok("Calculo realizado")
        except ValueError as err:
            self.status.error(str(err))

    def _escribir(self, texto):
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", texto)
        self.texto.configure(state="disabled")
