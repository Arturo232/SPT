"""Asistente guiado y consola de comandos para el entorno de circuito trifásico.

Dos interfaces sobre la misma clase ``CircuitoTrifasico``:
  - ``asistente()`` : asistente (wizard) paso a paso: Fuente → Linea →
    Cargas → Resultados.
  - ``consola()``  : REPL con comandos naturales (``add delta 10+5j``,
    ``solve``, ``reporte``, ...).
"""

import re

import numpy as np

from .circuito import CircuitoTrifasico
from .errors import error_analizador
from .utils import input_helpers


# ---------------------------------------------------------------------------
# Parser de números complejos en formato R+jX
# ---------------------------------------------------------------------------
def parse_complejo(texto):
    """Interpreta un número complejo escrito como ``R+jX``, ``R-jX``, ``jX``.

    Ejemplos: ``10+5j``, ``2-8j``, ``-0.2+0.05j``, ``4j``, ``10``,
    ``10 + j5`` (j delante de la parte imaginaria).
    Lanza ``analizador:circuito:complejoInvalido`` si no puede interpretarlo.
    """
    t = texto.strip().lower().replace("i", "j")
    try:
        return complex(t.replace(" ", ""))
    except ValueError:
        pass
    # forma R + jX  (la j delante de la parte imaginaria)
    s = t.replace(" ", "")
    m = re.fullmatch(r"([+-]?[\d.]+(?:e[+-]?\d+)?)([+-])j([\d.]+(?:e[+-]?\d+)?)", s)
    if m:
        r = float(m.group(1))
        x = float(m.group(3))
        signo = -1 if m.group(2) == "-" else 1
        return r + 1j * signo * x
    # jX puro (solo parte imaginaria), p. ej. "j5" o "4j"
    if t.endswith("j"):
        parte = t[:-1]
        if parte in ("", "+"):
            parte = "1"
        elif parte == "-":
            parte = "-1"
        return 1j * _a_float(parte, texto)
    error_analizador("circuito", "complejoInvalido",
                     "Error: no pude interpretar el numero complejo. Use R+jX (ej. 10+5j). Valor: {0}", texto)


def _a_float(texto, original):
    try:
        return float(texto)
    except ValueError:
        error_analizador("circuito", "complejoInvalido",
                         "Error: no pude interpretar el numero complejo. Valor: {0}", original)


def _fmt(z):
    from .circuito import _fmt_complex
    return _fmt_complex(z)


# ---------------------------------------------------------------------------
# Asistente guiado (wizard)
# ---------------------------------------------------------------------------
def asistente():
    """Asistente paso a paso para resolver un circuito trifásico balanceado."""
    print("\n===== ASISTENTE DE CIRCUITO TRIFASICO =====")
    print("Vamos a armar el circuito por etapas: Fuente, Linea y Cargas.\n")

    circuito = CircuitoTrifasico()

    # 1) Fuente
    print("1) FUENTE")
    v_linea = input_helpers("positive", "Tension de linea de la fuente VL (V): ")
    angulo = input_helpers("number", "Angulo de la fase a (grados, 0 por defecto): ")
    circuito.set_fuente(v_linea, angulo)

    # 2) Linea
    print("\n2) LINEA DE TRANSMISION (impedancia serie, 0 si es directa)")
    r_linea = input_helpers("number", "R de la linea (ohm): ")
    x_linea = input_helpers("number", "X de la linea (ohm): ")
    circuito.set_linea(r_linea + 1j * x_linea)

    # 3) Cargas
    print("\n3) CARGAS EN PARALELO")
    while True:
        print("\nNueva carga:")
        conexion = input_helpers("choice", "Conexion:", ["Estrella (Y)", "Delta"])
        conexiones = ["Y", "Delta"]
        r_c = input_helpers("number", "R de la impedancia por fase (ohm): ")
        x_c = input_helpers("number", "X de la impedancia por fase (ohm): ")
        circuito.agregar_carga(conexiones[conexion - 1], r_c + 1j * x_c)
        print("  Carga %d agregada (%s, Z = %s)."
              % (len(circuito.cargas), conexiones[conexion - 1],
                 _fmt(r_c + 1j * x_c)))
        if input_helpers("choice", "¿Agregar otra carga?", ["No", "Si"]) == 1:
            break

    # 4) Resultados
    print("\n4) RESOLVIENDO...")
    circuito.resolver()
    print(circuito.reporte())

    _ofrecer_exportar(circuito)


def _ofrecer_exportar(circuito):
    if input_helpers("choice", "¿Exportar el reporte?", ["No", "Si"]) == 1:
        return
    from .utils import export_results
    resultado = circuito.resultado
    nombre = input("  Archivo (sin extension): ").strip()
    formato = input_helpers("choice", "Formato:", ["TXT", "JSON", "CSV"])
    formatos = ["txt", "json", "csv"]
    archivo = export_results(resultado, nombre, formatos[formato - 1])
    print("  Exportado: %s" % archivo)


# ---------------------------------------------------------------------------
# Consola de comandos (parser natural)
# ---------------------------------------------------------------------------
_AYUDA = """
COMANDOS DEL ENTORNO DE CIRCUITO TRIFASICO
--------------------------------------------
  fuente <VL> [angulo]     Define la tension de linea de la fuente.
  linea <R+jX>             Define la impedancia de linea (serie).
  carga <Y|Delta> <R+jX>   Agrega una carga en paralelo (conversion D->Y
                           automatica).
  add <Y|D> <R+jX>         Igual que 'carga'.
  cargas                   Muestra las cargas definidas.
  limpiar                  Elimina todas las cargas.
  resolver | solve         Resuelve el circuito y muestra el reporte.
  reporte                  Muestra el ultimo reporte generado.
  ver                      Muestra el estado actual del circuito.
  ayuda | help             Muestra esta ayuda.
  salir | exit | quit      Termina la consola.

Ejemplos:
  fuente 208
  linea 0.1+0.05j
  carga Delta 30+40j
  carga Y 20-15j
  resolver
"""


def consola():
    """Consola interactiva con comandos naturales."""
    circuito = CircuitoTrifasico()
    print("\n===== ENTORNO DE CIRCUITO TRIFASICO (CONSOLA) =====")
    print("Escriba 'ayuda' para ver los comandos y ejemplos. Escriba 'salir' para terminar.")

    while True:
        try:
            linea = input("circuito> ").strip()
        except EOFError:
            print()
            break
        if not linea:
            continue
        if linea.lower() in ("salir", "exit", "quit", "q"):
            print("Fin del entorno de circuito.")
            break
        _ejecutar_comando(circuito, linea)


def _ejecutar_comando(circuito, linea):
    """Ejecuta una línea de comando y devuelve True si se continuó con éxito."""
    partes = linea.split()
    cmd = partes[0].lower()
    args = partes[1:]

    if cmd in ("ayuda", "help", "?"):
        print(_AYUDA)
        return

    if cmd in ("fuente", "vfuente", "set-fuente"):
        if len(args) < 1:
            error_analizador("circuito", "argumentos", "Uso: fuente <VL> [angulo]")
        v_linea = float(args[0])
        angulo = float(args[1]) if len(args) > 1 else 0.0
        circuito.set_fuente(v_linea, angulo)
        print("  Fuente: VL = %g V, fase a = %s"
              % (v_linea, _fmt(circuito.v_fuente_fase)))
        return

    if cmd in ("linea", "zlinea", "set-linea"):
        if len(args) < 1:
            error_analizador("circuito", "argumentos", "Uso: linea <R+jX>")
        z = parse_complejo(" ".join(args))
        circuito.set_linea(z)
        print("  Linea: Z = %s" % _fmt(z))
        return

    if cmd in ("carga", "add", "agregar"):
        if len(args) < 2:
            error_analizador("circuito", "argumentos",
                             "Uso: carga <Y|Delta> <R+jX>")
        conexion = args[0]
        z = parse_complejo(" ".join(args[1:]))
        circuito.agregar_carga(conexion, z)
        n = len(circuito.cargas)
        c = circuito.cargas[-1]
        print("  Carga %d (%s): Z_fase = %s -> Z_Y = %s"
              % (n, c["conexion"], _fmt(c["z_fase"]), _fmt(c["z_y"])))
        return

    if cmd in ("cargas", "list"):
        if len(circuito.cargas) == 0:
            print("  No hay cargas definidas.")
            return
        for c in circuito.cargas:
            print("  %-4s Z_fase = %s  Z_Y = %s"
                  % (c["conexion"], _fmt(c["z_fase"]), _fmt(c["z_y"])))
        return

    if cmd in ("limpiar", "reset", "clear"):
        circuito.limpiar_cargas()
        print("  Cargas eliminadas.")
        return

    if cmd in ("resolver", "solve"):
        try:
            circuito.resolver()
            print(circuito.reporte())
        except Exception as err:
            print("  ERROR: %s" % err)
        return

    if cmd in ("reporte", "report"):
        try:
            print(circuito.reporte())
        except Exception as err:
            print("  ERROR: %s" % err)
        return

    if cmd in ("ver", "estado", "show"):
        v = getattr(circuito, "v_fuente_fase", None)
        print("  Fuente: %s" % ("VL = %g V, fase a = %s"
                                % (circuito.v_linea, _fmt(v)) if v is not None
                                else "no definida"))
        print("  Linea:  Z = %s" % _fmt(circuito.z_linea))
        print("  Cargas: %d" % len(circuito.cargas))
        for c in circuito.cargas:
            print("    %-4s Z_fase = %s" % (c["conexion"], _fmt(c["z_fase"])))
        if circuito.z_eq is not None:
            print("  Z_eq calculada = %s" % _fmt(circuito.z_eq))
        return

    error_analizador("circuito", "comandoDesconocido",
                     "Error: comando no reconocido: {0}. Escriba 'ayuda'.", cmd)
