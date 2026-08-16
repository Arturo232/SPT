"""Vista: Correccion de factor de potencia.

Desacoplamiento: llama a ``resolver_calculo('correccionFP', datos)``.
"""

from types import SimpleNamespace

import customtkinter as ctk

from ..components import Card, LabeledEntry, StatusFeedback, leer_float
from ...core.resolver import resolver_calculo


class CorreccionView(ctk.CTkFrame):
    titulo = "Correccion de FP"

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Correccion de factor de potencia", anchor="w",
                     font=ctk.CTkFont(size=22, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, sticky="w",
                            padx=24, pady=(18, 4))

        # ------------------ tarjeta: entradas ------------------
        card_in = Card(self, titulo="Entradas")
        card_in.grid(row=1, column=0, sticky="nsew", padx=(24, 8), pady=8)
        self.in_p = LabeledEntry(card_in.cuerpo, "P", "ej. 1200", "W")
        self.in_p.grid(row=0, column=0, sticky="ew", pady=4)
        self.in_fp1 = LabeledEntry(card_in.cuerpo, "FP inicial", "ej. 0.6", "-")
        self.in_fp1.grid(row=1, column=0, sticky="ew", pady=4)
        self.in_fp2 = LabeledEntry(card_in.cuerpo, "FP objetivo", "ej. 0.9", "-")
        self.in_fp2.grid(row=2, column=0, sticky="ew", pady=4)
        self.in_v = LabeledEntry(card_in.cuerpo, "V", "ej. 200", "V")
        self.in_v.grid(row=3, column=0, sticky="ew", pady=4)
        self.in_f = LabeledEntry(card_in.cuerpo, "f", "60", "Hz")
        self.in_f.grid(row=4, column=0, sticky="ew", pady=4)

        self.btn = ctk.CTkButton(card_in.cuerpo, text="Calcular", height=34,
                                 command=self._calcular)
        self.btn.grid(row=5, column=0, sticky="ew", pady=(14, 8))
        self.status = StatusFeedback(card_in.cuerpo)
        self.status.grid(row=6, column=0, sticky="ew")

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
                P=leer_float(self.in_p.get(), "P"),
                fp1=leer_float(self.in_fp1.get(), "FP inicial"),
                fp2=leer_float(self.in_fp2.get(), "FP objetivo"),
                V=leer_float(self.in_v.get(), "V"),
                f=leer_float(self.in_f.get(), "f"),
            )
            texto, _ = resolver_calculo("correccionFP", datos)
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
