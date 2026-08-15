"""Entorno de modelado y resolución de circuitos trifásicos balanceados.

Clase ``CircuitoTrifasico`` que mantiene el estado de la red (fuente,
impedancia de línea y cargas en paralelo, cada una en Y o Delta) y resuelve
el circuito de forma transparente, sin que el usuario anote valores
intermedios.

El equivalente por fase toma la fase "a" como referencia (ángulo 0):
  V_fase = VL / sqrt(3)      (fuente)
  Z_Y = Z_Delta / 3          (conversión por carga)
  Y_eq = sum(1/Z_Y_k)  →  Z_eq = 1/Y_eq        (cargas en paralelo)
  Z_total = Z_linea + Z_eq
  I_L = V_fase / Z_total
  V_carga = I_L * Z_eq
  S3f = 3 * V_fase * conj(I_L)
"""

import math
from types import SimpleNamespace

import numpy as np

from .core import (complex_power, polar_to_complex, power_factor,
                   rad2deg, validate_input)
from .errors import error_analizador
from .modules.sistemas_trifasicos import normalizar_conexion


class CircuitoTrifasico:
    """Modelo con estado de un circuito trifásico balanceado.

    Estado:
      v_linea          : tensión de línea de la fuente [V] (o None)
      z_linea          : impedancia de línea en serie [ohm] (0 por defecto)
      cargas           : lista de dicts {conexion, z_fase}
      z_eq             : impedancia equivalente de las cargas (tras resolver)
      z_total          : z_linea + z_eq (tras resolver)
    """

    def __init__(self, v_linea=None, z_linea=0j):
        self.v_linea = v_linea
        self.z_linea = z_linea
        self.cargas = []
        self.z_eq = None
        self.z_total = None
        self.resultado = None
        self.v_fuente_fase = None
        self.i_fuente = None        # corriente de fuente conocida (fasor)
        self.v_carga_dato = None    # tension en la carga conocida (fasor)

    # ------------------------------------------------------------------
    # Configuración del estado
    # ------------------------------------------------------------------
    def set_fuente(self, v, angulo_deg=0.0, dato="linea"):
        """Define la tensión de la fuente.

        Parámetros:
          v       : magnitud de la tensión [V]
          angulo_deg : ángulo de la fase a [grados] (por defecto 0)
          dato    : 'linea' (V_L, por defecto) o 'fase' (V_f)

        Si ``dato='fase'``, se deriva ``V_L = sqrt(3) * V_f``.
        Internamente se conserva siempre ``v_linea`` y el fasor de fase.
        """
        validate_input("positive", v, "V")
        d = str(dato).lower()
        if d in ("linea", "l", "line", "vl"):
            v_linea = v
            v_fase = v / math.sqrt(3)
        elif d in ("fase", "f", "phase", "vf"):
            v_linea = v * math.sqrt(3)
            v_fase = v
        else:
            error_analizador("circuito", "datoFuenteInvalido",
                             "Error: el tipo de dato debe ser 'linea' o 'fase'. Valor: {0}", dato)
        self.v_linea = v_linea
        self.v_fuente_fase = polar_to_complex(v_fase, angulo_deg)
        self.i_fuente = None
        self.v_carga_dato = None
        self.z_eq = None
        self.z_total = None
        return self

    def set_corriente(self, i_fuente):
        """Define la corriente de la fuente como dato (fasor, ej. ``30-40j``
        o ``50 angulo -53.13``). La fuente y las tensiones se derivan."""
        validate_input("numeric", i_fuente, "I")
        validate_input("nonzero", i_fuente, "I")
        self.i_fuente = i_fuente
        self.v_fuente_fase = None
        self.v_linea = None
        self.v_carga_dato = None
        self.z_eq = None
        self.z_total = None
        return self

    def set_v_carga(self, v_carga):
        """Define la tensión en la carga como dato (fasor). La corriente y
        la fuente se derivan del circuito."""
        validate_input("numeric", v_carga, "Vcarga")
        validate_input("nonzero", v_carga, "Vcarga")
        self.v_carga_dato = v_carga
        self.i_fuente = None
        self.v_fuente_fase = None
        self.v_linea = None
        self.z_eq = None
        self.z_total = None
        return self

    def set_linea(self, z_linea):
        """Define la impedancia de línea en serie [ohm]."""
        validate_input("numeric", z_linea, "Zlinea")
        self.z_linea = z_linea
        self.z_eq = None
        self.z_total = None
        return self

    def agregar_carga(self, conexion, z_fase):
        """Agrega una carga en paralelo.

        ``conexion`` es 'Y' o 'Delta'; ``z_fase`` es la impedancia por fase
        [ohm]. La conversión Delta→Y es transparente: se guarda siempre el
        equivalente en Y.
        """
        validate_input("numeric", z_fase, "Zfase")
        validate_input("nonzero", z_fase, "Zfase")
        c = normalizar_conexion(conexion)
        z_y = z_fase / 3 if c == "Delta" else z_fase
        self.cargas.append({
            "conexion": c,
            "z_fase": z_fase,
            "z_y": z_y,
            "por_potencia": False,
        })
        # invalidar resultados previos
        self.z_eq = None
        self.z_total = None
        return self

    def agregar_carga_por_potencia(self, conexion, s_total, v_nominal=None):
        """Agrega una carga definida por su potencia compleja total.

        ``conexion`` es 'Y' o 'Delta'; ``s_total`` es la potencia trifásica
        [VA]; ``v_nominal`` es la tensión de línea nominal de la carga [V]
        (por defecto se usa la tensión de la fuente, o la tensión en la
        carga si fue definida). Se convierte a impedancia equivalente:
          Z_fase = |V_fase|^2 / conj(S_fase)
        """
        validate_input("numeric", s_total, "S")
        validate_input("nonzero", s_total, "S")
        c = normalizar_conexion(conexion)
        if v_nominal is None:
            if self.v_carga_dato is not None:
                v_nominal = abs(self.v_carga_dato) * math.sqrt(3)
            elif self.v_linea is not None:
                v_nominal = self.v_linea
            else:
                error_analizador("circuito", "sinTension",
                                 "Error: defina la tension de la fuente o el voltaje nominal de la carga antes de usar potencia.")
        s_fase = s_total / 3
        if c == "Y":
            v_fase = v_nominal / math.sqrt(3)
        else:
            v_fase = v_nominal
        z_fase = (abs(v_fase) ** 2) / np.conjugate(s_fase)
        self.cargas.append({
            "conexion": c,
            "z_fase": z_fase,
            "z_y": z_fase / 3 if c == "Delta" else z_fase,
            "por_potencia": True,
            "s_total": s_total,
            "v_nominal": v_nominal,
        })
        self.z_eq = None
        self.z_total = None
        return self

    def limpiar_cargas(self):
        """Elimina todas las cargas."""
        self.cargas = []
        self.z_eq = None
        self.z_total = None

    # ------------------------------------------------------------------
    # Cálculo
    # ------------------------------------------------------------------
    def impedancia_equivalente(self):
        """Impedancia equivalente de todas las cargas en paralelo [ohm].

        ``Y_eq = sum(1/Z_Y_k)``; ``Z_eq = 1/Y_eq``.
        """
        if len(self.cargas) == 0:
            error_analizador("circuito", "sinCargas",
                             "Error: agregue al menos una carga antes de resolver.")
        y_eq = sum(1 / c["z_y"] for c in self.cargas)
        z_eq = 1 / y_eq
        self.z_eq = z_eq
        return z_eq

    def resolver(self):
        """Resuelve el circuito completo.

        Regresa ``SimpleNamespace`` con todas las variables del circuito
        trifásico balanceado:

        Fuente: v_fuente_linea, v_fuente_fase, v_linea
        Línea : z_linea, v_caida_linea
        Carga : v_carga (fase), v_carga_linea, z_eq, z_total
        Corrientes: i_linea (fasor) y su magnitud
        Potencias: s_fase, s3f, P, Q, Sabs, fp, type, phi_deg
        Detalle por carga: v_fase, v_linea, i_fase, i_linea, s_fase,
                           s3f, P, Q, Sabs, fp, type, phi_deg, z_fase, z_y
        """
        if len(self.cargas) == 0:
            error_analizador("circuito", "sinCargas",
                             "Error: agregue al menos una carga antes de resolver.")

        z_eq = self.impedancia_equivalente()
        z_total = self.z_linea + z_eq
        self.z_total = z_total

        # Determinar el modo de resolución según el dato disponible:
        #   1) fuente definida  -> I = V_fuente / Z_total
        #   2) corriente dada   -> V_fuente = I * Z_total
        #   3) tensión en la carga dada -> I = V_carga / Z_eq ; V_fuente = V_carga + I*Z_linea
        if self.v_carga_dato is not None:
            i_linea = self.v_carga_dato / z_eq
            v_fase = self.v_carga_dato + i_linea * self.z_linea
        elif self.i_fuente is not None:
            i_linea = self.i_fuente
            v_fase = i_linea * z_total
        elif self.v_fuente_fase is not None:
            v_fase = self.v_fuente_fase
            i_linea = v_fase / z_total
        else:
            error_analizador("circuito", "sinDatos",
                             "Error: defina al menos uno de: tension de la fuente, corriente, o tension en la carga.")

        v_carga = i_linea * z_eq                    # Vf en la carga (fase a)
        v_caida = i_linea * self.z_linea            # caída en la línea
        s_fase = complex_power(v_fase, i_linea)
        s3f = 3 * s_fase
        fp_info = power_factor(s3f)
        v_linea_fuente = abs(v_fase) * math.sqrt(3)

        detalle = []
        for k, carga in enumerate(self.cargas, start=1):
            i_rama = v_carga / carga["z_y"]         # IL que alimenta esa carga
            v_linea_carga = abs(v_carga) * math.sqrt(3)
            if carga["conexion"] == "Y":
                i_fase_carga = i_rama               # IL = If
                v_fase_carga = v_carga
                v_linea_carga_fasor = v_carga * math.sqrt(3)
            else:  # Delta
                # If = IL*exp(j30)/sqrt(3) ; Vf = VL (tension de linea,
                # adelanta 30° a la fase de referencia)
                i_fase_carga = i_rama * np.exp(1j * math.radians(30)) / math.sqrt(3)
                v_fase_carga = v_carga * math.sqrt(3) * np.exp(1j * math.radians(30))
                v_linea_carga_fasor = v_carga * math.sqrt(3) * np.exp(1j * math.radians(30))
            s_carga_fase = complex_power(v_fase_carga, i_fase_carga)
            s_carga_3f = 3 * s_carga_fase
            fp_carga = power_factor(s_carga_3f)
            detalle.append({
                "id": k,
                "conexion": carga["conexion"],
                "z_fase": carga["z_fase"],
                "z_y": carga["z_y"],
                "v_fase": v_fase_carga,
                "v_linea": v_linea_carga,
                "v_linea_fasor": v_linea_carga_fasor,
                "i_fase": i_fase_carga,
                "i_linea": i_rama,
                "s_fase": s_carga_fase,
                "s3f": s_carga_3f,
                "P": np.real(s_carga_3f),
                "Q": np.imag(s_carga_3f),
                "Sabs": fp_carga.Sabs,
                "fp": fp_carga.fp,
                "type": fp_carga.type,
                "phi_deg": rad2deg(np.angle(s_carga_3f)),
            })

        result = SimpleNamespace(
            # fuente
            v_linea=v_linea_fuente,
            v_fuente_linea=polar_to_complex(v_linea_fuente,
                                            rad2deg(np.angle(v_fase))),
            v_fuente_fase=v_fase,
            # línea
            z_linea=self.z_linea,
            v_caida_linea=v_caida,
            # carga
            v_carga=v_carga,
            v_carga_linea=abs(v_carga) * math.sqrt(3),
            z_eq=z_eq,
            z_total=z_total,
            # corrientes
            i_linea=i_linea,
            # potencias
            s_fase=s_fase,
            s3f=s3f,
            P=np.real(s3f),
            Q=np.imag(s3f),
            Sabs=fp_info.Sabs,
            fp=fp_info.fp,
            type=fp_info.type,
            phi_deg=rad2deg(np.angle(s3f)),
            cargas=detalle,
        )
        self.resultado = result
        return result

    # ------------------------------------------------------------------
    # Reporte
    # ------------------------------------------------------------------
    def reporte(self):
        """Texto legible con todas las variables del circuito resuelto.

        Muestra cada fasor en forma rectangular y polar, el detalle de cada
        carga (Vf, VL, If, IL, S, P, Q, FP según su conexión) y los totales.
        """
        r = self.resultado
        if r is None:
            error_analizador("circuito", "sinResolver",
                             "Error: resuelva el circuito antes de generar el reporte.")
        lineas = [
            "",
            "===== REPORTE DEL CIRCUITO TRIFASICO (BALANCEADO) =====",
            "",
            "--- FUENTE ---",
            "  Tension de linea   V_L   = %s" % _fmt_fasor(r.v_fuente_linea),
            "  Tension de fase    V_f   = %s" % _fmt_fasor(r.v_fuente_fase),
            "",
            "--- LINEA DE TRANSMISION ---",
            "  Impedancia serie   Z_L   = %s" % _fmt_complex(r.z_linea),
            "  Caida de tension   dV_L  = %s" % _fmt_fasor(r.v_caida_linea),
            "",
            "--- CARGAS EN PARALELO (detalle) ---",
        ]
        for k, c in enumerate(r.cargas, start=1):
            lineas.append(
                "  C%d (%s): Z_fase = %s  ->  Z_Y = %s"
                % (k, c["conexion"], _fmt_complex(c["z_fase"]), _fmt_complex(c["z_y"])))
            lineas.append(
                "      V_f = %s ;  V_L = %s"
                % (_fmt_fasor(c["v_fase"]), _fmt_fasor(c["v_linea_fasor"])))
            lineas.append(
                "      I_f = %s ;  I_L = %s"
                % (_fmt_fasor(c["i_fase"]), _fmt_fasor(c["i_linea"])))
            lineas.append(
                "      S   = %s  (P = %.4f W, Q = %.4f var, |S| = %.4f VA)"
                % (_fmt_complex(c["s3f"]), c["P"], c["Q"], c["Sabs"]))
            lineas.append(
                "      FP  = %.4f (%s), phi = %.4f deg"
                % (c["fp"], _estado(c["type"]), c["phi_deg"]))
        lineas += [
            "",
            "--- CIRCUITO EQUIVALENTE ---",
            "  Impedancia equivalente de la carga   Z_eq     = %s"
            % _fmt_complex(r.z_eq),
            "  Impedancia total (linea + carga)     Z_total  = %s"
            % _fmt_complex(r.z_total),
            "",
            "--- CORRIENTES ---",
            "  Corriente de linea     I_L = %s  (|I| = %.4f A)"
            % (_fmt_fasor(r.i_linea), abs(r.i_linea)),
            "",
            "--- TENSIONES EN LA CARGA ---",
            "  Tension de fase        V_f = %s  (|V| = %.4f V)"
            % (_fmt_fasor(r.v_carga), abs(r.v_carga)),
            "  Tension de linea       V_L = %.4f V" % r.v_carga_linea,
            "",
            "--- POTENCIA (trifasica total) ---",
            "  S = %s" % _fmt_complex(r.s3f),
            "  P   = %.4f W" % r.P,
            "  Q   = %.4f var" % r.Q,
            "  |S| = %.4f VA" % r.Sabs,
            "  FP  = %.4f (%s)" % (r.fp, _estado(r.type)),
            "  phi = %.4f deg" % r.phi_deg,
            "",
        ]
        return "\n".join(lineas)


def _estado(tipo):
    if tipo == "inductiva":
        return "ATRASO (inductivo)"
    if tipo == "capacitiva":
        return "ADELANTO (capacitivo)"
    return "RESISTIVO"


def _fmt_complex(z):
    a = np.real(z)
    b = np.imag(z)
    if abs(b) < 1e-12 * max(1, abs(z)):
        return "%.4g" % a
    if abs(a) < 1e-12 * max(1, abs(z)):
        return "%.4gj" % b
    if b >= 0:
        return "%.4g + j%.4g" % (a, b)
    return "%.4g - j%.4g" % (a, -b)


def _fmt_fasor(z):
    """Fasor en forma rectangular + polar: 'a+jb | M angulo theta deg'."""
    ang = rad2deg(np.angle(z))
    return "%s | %.4g angulo %.4g deg" % (_fmt_complex(z), abs(z), ang)
