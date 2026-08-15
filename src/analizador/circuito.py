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

    # ------------------------------------------------------------------
    # Configuración del estado
    # ------------------------------------------------------------------
    def set_fuente(self, v_linea, angulo_deg=0.0):
        """Define la tensión de línea de la fuente [V]."""
        validate_input("positive", v_linea, "VL")
        self.v_linea = v_linea
        self.v_fuente_fase = polar_to_complex(v_linea / math.sqrt(3), angulo_deg)
        return self

    def set_linea(self, z_linea):
        """Define la impedancia de línea en serie [ohm]."""
        validate_input("numeric", z_linea, "Zlinea")
        self.z_linea = z_linea
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
        })
        # invalidar resultados previos
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

        Regresa ``SimpleNamespace`` con:
          z_eq, z_total, i_linea, v_carga (fase), v_carga_linea,
          s_fase, s3f, P, Q, Sabs, fp, type, phi_deg y el detalle de cada carga.
        """
        if not hasattr(self, "v_fuente_fase") or self.v_linea is None:
            error_analizador("circuito", "sinFuente",
                             "Error: defina la tension de la fuente (VL) antes de resolver.")
        if len(self.cargas) == 0:
            error_analizador("circuito", "sinCargas",
                             "Error: agregue al menos una carga antes de resolver.")

        z_eq = self.impedancia_equivalente()
        z_total = self.z_linea + z_eq
        self.z_total = z_total

        v_fase = self.v_fuente_fase
        i_linea = v_fase / z_total
        v_carga = i_linea * z_eq
        s_fase = complex_power(v_fase, i_linea)
        s3f = 3 * s_fase
        fp_info = power_factor(s3f)

        detalle = []
        for k, carga in enumerate(self.cargas, start=1):
            i_carga = v_carga / carga["z_y"]
            s_carga_fase = complex_power(v_carga, i_carga)
            detalle.append({
                "id": k,
                "conexion": carga["conexion"],
                "z_fase": carga["z_fase"],
                "z_y": carga["z_y"],
                "i_fase": i_carga,
                "s_fase": s_carga_fase,
                "s3f": 3 * s_carga_fase,
                "P": np.real(3 * s_carga_fase),
                "Q": np.imag(3 * s_carga_fase),
            })

        result = SimpleNamespace(
            v_linea=self.v_linea,
            v_fuente_fase=v_fase,
            z_linea=self.z_linea,
            z_eq=z_eq,
            z_total=z_total,
            i_linea=i_linea,
            v_carga=v_carga,
            v_carga_linea=abs(v_carga) * math.sqrt(3),
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
        """Texto legible con los resultados del circuito resuelto."""
        r = self.resultado
        if r is None:
            error_analizador("circuito", "sinResolver",
                             "Error: resuelva el circuito antes de generar el reporte.")
        lineas = [
            "",
            "===== REPORTE DEL CIRCUITO TRIFASICO =====",
            "Fuente:  VL = %g V, fase a = %.4f V (referencia)"
            % (r.v_linea, abs(r.v_fuente_fase)),
            "Linea:   Z = %s" % _fmt_complex(r.z_linea),
            "--------------------------------------------",
            "Cargas en paralelo (equivalente por fase en Y):",
        ]
        for k, c in enumerate(r.cargas, start=1):
            lineas.append(
                "  C%d: %-6s Z_fase = %s  ->  Z_Y = %s"
                % (k, c["conexion"], _fmt_complex(c["z_fase"]), _fmt_complex(c["z_y"])))
        lineas += [
            "--------------------------------------------",
            "Impedancia equivalente de la carga:  Z_eq = %s" % _fmt_complex(r.z_eq),
            "Impedancia total (linea + carga):    Z_total = %s" % _fmt_complex(r.z_total),
            "Corriente de linea:                  I_L = %s  (|I| = %.4f A)"
            % (_fmt_complex(r.i_linea), abs(r.i_linea)),
            "Tension en la carga (fase):          V_f = %s  (|V| = %.4f V)"
            % (_fmt_complex(r.v_carga), abs(r.v_carga)),
            "Tension de linea en la carga:        V_L = %.4f V" % r.v_carga_linea,
            "--------------------------------------------",
            "Potencia compleja total:  S = %s" % _fmt_complex(r.s3f),
            "  P   = %.4f W" % r.P,
            "  Q   = %.4f var" % r.Q,
            "  |S| = %.4f VA" % r.Sabs,
            "  FP  = %.4f (%s)" % (r.fp, _estado(r.type)),
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
