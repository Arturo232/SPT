"""Vista: Potencia compleja (flujos 'Desde P y FP' y 'Desde V y Z').

Desacoplamiento: esta vista solo construye un ``SimpleNamespace`` con los
datos de entrada y llama a ``resolver_calculo`` (backend).
"""

from types import SimpleNamespace

import customtkinter as ctk

from ..components import Card, LabeledEntry, StatusFeedback, leer_float
from ...core.resolver import resolver_calculo

_TIPOS = {"Inductiva (atraso)": "inductiva",
          "Capacitiva (adelanto)": "capacitiva",
          "Resistiva": "resistiva"}


class PotenciaView(ctk.CTkFrame):
    titulo = "Potencia compleja"

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Potencia compleja", anchor="w",
                     font=ctk.CTkFont(size=22, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, sticky="w",
                            padx=24, pady=(18, 4))

        # ------------------ tarjeta: entradas ------------------
        card_in = Card(self, titulo="Entradas")
        card_in.grid(row=1, column=0, sticky="nsew", padx=(24, 8), pady=8)
        self.flujo = ctk.CTkSegmentedButton(
            card_in.cuerpo, values=["Desde P y FP", "Desde V y Z"],
            command=self._cambiar_flujo)
        self.flujo.set("Desde P y FP")
        self.flujo.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        # flujo A: P, FP y tipo
        self.frame_pf = ctk.CTkFrame(card_in.cuerpo, fg_color="transparent")
        self.frame_pf.grid(row=1, column=0, sticky="nsew")
        self.frame_pf.grid_columnconfigure(0, weight=1)
        self.pf_p = LabeledEntry(self.frame_pf, "P", "ej. 250000", "W")
        self.pf_p.grid(row=0, column=0, sticky="ew", pady=4)
        self.pf_fp = LabeledEntry(self.frame_pf, "FP", "0 a 1", "-")
        self.pf_fp.grid(row=1, column=0, sticky="ew", pady=4)
        ctk.CTkLabel(self.frame_pf, text="Tipo de carga", anchor="w",
                     font=ctk.CTkFont(size=12), text_color="gray60"
                     ).grid(row=2, column=0, sticky="w", pady=(6, 2))
        self.pf_tipo = ctk.CTkOptionMenu(self.frame_pf,
                                         values=list(_TIPOS.keys()))
        self.pf_tipo.grid(row=3, column=0, sticky="ew")

        # flujo B: V, angulo, R, X
        self.frame_vz = ctk.CTkFrame(card_in.cuerpo, fg_color="transparent")
        self.frame_vz.grid(row=1, column=0, sticky="nsew")
        self.frame_vz.grid_remove()
        self.frame_vz.grid_columnconfigure(0, weight=1)
        self.vz_mag = LabeledEntry(self.frame_vz, "V (magnitud)", "ej. 200", "V")
        self.vz_mag.grid(row=0, column=0, sticky="ew", pady=4)
        self.vz_ang = LabeledEntry(self.frame_vz, "Angulo de V", "0", "deg")
        self.vz_ang.grid(row=1, column=0, sticky="ew", pady=4)
        self.vz_r = LabeledEntry(self.frame_vz, "R", "ej. 10", "ohm")
        self.vz_r.grid(row=2, column=0, sticky="ew", pady=4)
        self.vz_x = LabeledEntry(self.frame_vz, "X", "ej. 20", "ohm")
        self.vz_x.grid(row=3, column=0, sticky="ew", pady=4)

        self.btn_calcular = ctk.CTkButton(
            card_in.cuerpo, text="Calcular", height=34,
            command=self._calcular)
        self.btn_calcular.grid(row=2, column=0, sticky="ew", pady=(14, 8))
        self.status = StatusFeedback(card_in.cuerpo)
        self.status.grid(row=3, column=0, sticky="ew")

        # ------------------ tarjeta: resultados ------------------
        card_out = Card(self, titulo="Resultados")
        card_out.grid(row=1, column=1, sticky="nsew", padx=(8, 24), pady=8)
        self.texto = ctk.CTkTextbox(card_out.cuerpo, wrap="word")
        self.texto.grid(row=0, column=0, sticky="nsew")
        card_out.cuerpo.grid_rowconfigure(0, weight=1)
        self._escribir("Ingrese los datos y presione Calcular.")

    # ------------------------------------------------------------------
    def _cambiar_flujo(self, valor):
        if valor == "Desde P y FP":
            self.frame_vz.grid_remove()
            self.frame_pf.grid()
        else:
            self.frame_pf.grid_remove()
            self.frame_vz.grid()

    def _calcular(self):
        try:
            self.status.reset()
            self.update_idletasks()
            if self.flujo.get() == "Desde P y FP":
                datos = SimpleNamespace(
                    P=leer_float(self.pf_p.get(), "P"),
                    fp=leer_float(self.pf_fp.get(), "FP"),
                    tipo=_TIPOS[self.pf_tipo.get()],
                )
                texto, _ = resolver_calculo("potenciaPF", datos)
            else:
                datos = SimpleNamespace(
                    Vmag=leer_float(self.vz_mag.get(), "V"),
                    Vang=leer_float_opcional(self.vz_ang.get(), "Angulo"),
                    R=leer_float(self.vz_r.get(), "R"),
                    X=leer_float(self.vz_x.get(), "X"),
                )
                texto, _ = resolver_calculo("cargaVZ", datos)
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
