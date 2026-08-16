"""Asistente guiado y consola de comandos para el entorno de circuito trifásico.

Dos interfaces sobre la misma clase ``CircuitoTrifasico``:
  - ``asistente()`` : asistente (wizard) paso a paso: Fuente → Linea →
    Cargas → Resultados.
  - ``consola()``  : REPL con comandos naturales (``add delta 10+5j``,
    ``solve``, ``reporte``, ...).
"""

import difflib
import re

import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from prompt_toolkit import prompt

from ..core.circuito import CircuitoMonofasico, CircuitoTrifasico
from ..errors import AnalizadorError, error_analizador
from ..utils import input_helpers


_consola = Console()


# ---------------------------------------------------------------------------
# Parser de números complejos e impedancias
# ---------------------------------------------------------------------------
def parse_complejo(texto):
    """Interpreta un número complejo.

    Formatos aceptados:
      - Rectangular: ``R+jX``, ``R-jX``, ``jX``, ``10``, ``10 + j5``.
      - Polar (angulos en grados):
          ``M angulo A``   ej. ``30 angulo 53.13``
          ``M/A``          ej. ``50/30``
          ``M∠A``          ej. ``30∠53.13``  (simbolo angulo)
          ``M<A``          ej. ``30<53.13``
          ``M exp(A)``     ej. ``50 exp(30)``  (tambien e^, cis)
      - El angulo puede llevar sufijo ``deg`` o ``°``.
    Lanza ``analizador:circuito:complejoInvalido`` si no puede interpretarlo.
    """
    t = texto.strip().lower().replace("°", "").replace("deg", "")
    t_sin = t.replace(" ", "")

    # forma polar con separadores: "M/A", "M∠A", "M<A", "M@A", "M a A"
    # (la "a" de angulo no se confunde con "angulo", que va mas abajo)
    m = re.fullmatch(r"([+-]?[\d.]+(?:e[+-]?\d+)?)[/∠<@a]([+-]?[\d.]+(?:e[+-]?\d+)?)", t_sin)
    if m:
        return _polar(float(m.group(1)), float(m.group(2)), texto)

    # forma polar con palabra "angulo": "M angulo A"
    m = re.fullmatch(r"([+-]?[\d.]+(?:e[+-]?\d+)?)angulo([+-]?[\d.]+(?:e[+-]?\d+)?)", t_sin)
    if m:
        return _polar(float(m.group(1)), float(m.group(2)), texto)

    # forma exponencial: "M exp(A)", "M e^(A)", "M cis(A)"
    m = re.fullmatch(
        r"([+-]?[\d.]+(?:e[+-]?\d+)?)(?:exp|e\^|cis)\(?\s*([+-]?[\d.]+(?:e[+-]?\d+)?)\s*\)?",
        t_sin)
    if m:
        return _polar(float(m.group(1)), float(m.group(2)), texto)

    # forma polar con corchetes: "M[angulo]"  (ej. 200[30], 200[-30])
    m = re.fullmatch(
        r"([+-]?[\d.]+(?:e[+-]?\d+)?)\s*\[\s*([+-]?[\d.]+(?:e[+-]?\d+)?)\s*\]",
        t.replace(" ", ""))
    if m:
        return _polar(float(m.group(1)), float(m.group(2)), texto)

    # --- formatos rectangulares: aqui si convertimos i -> j ---
    s = t.replace("i", "j").replace(" ", "")
    try:
        return complex(s)
    except ValueError:
        pass
    # forma R + jX  (la j delante de la parte imaginaria)
    m = re.fullmatch(r"([+-]?[\d.]+(?:e[+-]?\d+)?)([+-])j([\d.]+(?:e[+-]?\d+)?)", s)
    if m:
        r = float(m.group(1))
        x = float(m.group(3))
        signo = -1 if m.group(2) == "-" else 1
        return r + 1j * signo * x
    # jX puro con la j al inicio (j5) o al final (5j)
    m = re.fullmatch(r"([+-]?)j([\d.]+(?:e[+-]?\d+)?)", s)
    if m:
        signo = -1 if m.group(1) == "-" else 1
        return 1j * signo * _a_float(m.group(2), texto)
    if s.endswith("j"):
        parte = s[:-1]
        if parte in ("", "+"):
            parte = "1"
        elif parte == "-":
            parte = "-1"
        return 1j * _a_float(parte, texto)
    error_analizador("circuito", "complejoInvalido",
                     "Error: no pude interpretar el numero complejo. Use R+jX (ej. 10+5j), polar 'M angulo A' (ej. 30 angulo 53.13) o 'M/A' (ej. 30/53.13). Valor: {0}", texto)


def _polar(mag, ang, original):
    from ..core.base import polar_to_complex
    return polar_to_complex(mag, ang)


def _tiene_angulo(texto):
    """True si el texto parece un fasor con angulo (polar) o imaginario."""
    t = texto.strip().lower()
    return any(marca in t for marca in ("angulo", "/", "∠", "<", "@",
                                        "exp", "cis", "e^", "j", "i"))


def parse_impedancia(args):
    """Interpreta una impedancia desde los argumentos del comando.

    ``args`` es una lista de cadenas. Acepta:
      - un solo valor complejo (rectangular o polar): ``10+5j``,
        ``30 angulo 53.13``.
      - dos números: R y X por separado: ``10 20``, ``-0.2 0.05``.
    """
    if len(args) == 1:
        return parse_complejo(args[0])
    if len(args) >= 2:
        try:
            r = float(args[0])
            x = float(args[1])
            return r + 1j * x
        except ValueError:
            pass
        return parse_complejo(" ".join(args))
    error_analizador("circuito", "argumentos",
                     "Error: indique la impedancia como R+jX, 'M angulo A' o 'R X'.")


def _a_float(texto, original):
    try:
        return float(texto)
    except ValueError:
        error_analizador("circuito", "complejoInvalido",
                         "Error: no pude interpretar el numero complejo. Valor: {0}", original)


def _fmt(z):
    from ..core.circuito import _fmt_complex
    return _fmt_complex(z)


def _fasor(z):
    """Fasor en forma rectangular + polar."""
    from ..core.base import rad2deg
    ang = rad2deg(np.angle(z))
    return "%s | %.4g angulo %.4g deg" % (_fmt(z), abs(z), ang)


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
    tipo_dato = input_helpers("choice", "¿Que dato tiene?",
                              ["Tension de linea (VL)",
                               "Tension de fase (Vf)",
                               "Corriente de la fuente (I)",
                               "Tension en la carga (V_carga)"])
    if tipo_dato in (1, 2):
        dato = "linea" if tipo_dato == 1 else "fase"
        etiqueta = "VL (V)" if dato == "linea" else "Vf (V)"
        v = input_helpers("positive", "Magnitud de la tension %s: " % etiqueta)
        angulo = input_helpers("number", "Angulo de la fase a (grados, 0 por defecto): ")
        circuito.set_fuente(v, angulo, dato)
        print("  Fuente: V_L = %.4g V | V_f = %.4g V"
              % (circuito.v_linea, abs(circuito.v_fuente_fase)))
    elif tipo_dato == 3:
        print("  Corriente de la fuente (fasor).")
        i_mag = input_helpers("positive", "  Magnitud de I (A): ")
        i_ang = input_helpers("number", "  Angulo de I (grados): ")
        circuito.set_corriente(polar_to_complex(i_mag, i_ang))
        print("  Corriente: I = %s" % _fasor(circuito.i_fuente))
    else:
        print("  Tension en la carga (fasor, fase a).")
        v_mag = input_helpers("positive", "  Magnitud de V_carga (V): ")
        v_ang = input_helpers("number", "  Angulo de V_carga (grados): ")
        circuito.set_v_carga(polar_to_complex(v_mag, v_ang))
        print("  Tension en la carga: V_f = %s" % _fasor(circuito.v_carga_dato))

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
        dato_carga = input_helpers("choice", "¿Como la define?",
                                   ["Por impedancia (R, X)",
                                    "Por potencia compleja (S)"])
        if dato_carga == 1:
            r_c = input_helpers("number", "R de la impedancia por fase (ohm): ")
            x_c = input_helpers("number", "X de la impedancia por fase (ohm): ")
            circuito.agregar_carga(conexiones[conexion - 1], r_c + 1j * x_c)
            print("  Carga %d agregada (%s, Z = %s)."
                  % (len(circuito.cargas), conexiones[conexion - 1],
                     _fmt(r_c + 1j * x_c)))
        else:
            print("  Potencia compleja total S (W + j var):")
            p_c = input_helpers("number", "  P (W): ")
            q_c = input_helpers("number", "  Q (var): ")
            circuito.agregar_carga_por_potencia(conexiones[conexion - 1],
                                                p_c + 1j * q_c)
            c = circuito.cargas[-1]
            print("  Carga %d agregada (%s, S = %s -> Z = %s)."
                  % (len(circuito.cargas), conexiones[conexion - 1],
                     _fmt(p_c + 1j * q_c), _fmt(c["z_fase"])))
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
    from ..utils import export_results
    resultado = circuito.resultado
    nombre = input("  Archivo (sin extension, se guardara en resultados/): ").strip()
    formato = input_helpers("choice", "Formato:", ["TXT", "JSON", "CSV"])
    formatos = ["txt", "json", "csv"]
    archivo = export_results(resultado, nombre, formatos[formato - 1])
    print("  Exportado: %s" % archivo)


# ---------------------------------------------------------------------------
# Consola de comandos (parser natural)
# ---------------------------------------------------------------------------
_AYUDA = """
COMANDOS DE LA CONSOLA DE CIRCUITOS (MONOFASICO Y TRIFASICO)
-------------------------------------------------------------
MODOS DE TRABAJO
  modo               Muestra el modo actual (mono o tri).
  modo mono          Cambia a circuito monofasico (1f).
  modo tri           Cambia a circuito trifasico balanceado (3f).
  resolver mono      Resuelve como monofasico (cambia de modo si hace falta).
  resolver tri       Resuelve como trifasico.
  Cada modo guarda su propio circuito (fuente, linea y cargas).

FORMATO DE IMPEDANCIAS Y FASORES (en cualquier comando):
  Rectangular : R+jX  (ej. 10+5j, 2-8j, 4j, j5)  o  R+iX (tambien con i)
  Polar       : M angulo A  |  M/A  |  M∠A  |  M<A  |  M exp(A)  |  M cis(A)
                Si no tiene el simbolo de angulo, use:
                  M@A  (arroba)   ej. 30@53.13
                  M a A (letra a) ej. 30a53.13   o   30 a 53.13
                (angulos en grados, con o sin sufijo deg/°)
                ej. 30 angulo 53.13, 50/30, 30∠53.13, 30<53.13, 50 exp(30)
  R y X sueltos: dos numeros (ej. 10 20)

DEFINICION DEL CIRCUITO
  fuente <magnitud> [linea|fase] [angulo]
                     Define la tension de la fuente.
                     - En modo TRIFASICO: por defecto es tension de LINEA
                       (VL); use 'fase' si el dato es Vf.
                     - En modo MONOFASICO: es la unica tension V.
                     Tambien acepta el fasor completo con angulo:
                       fuente 120@30        fuente 120 angulo 30
                       fuente 120/30        fuente 96.4+64.3j
                     Ej: fuente 208  |  fuente 120 fase  |  fuente 120 f 0
  corriente <I>      Define la corriente de la fuente como dato;
                     la fuente se deriva.  Ej: corriente 30-40j
  vcarga <V>         Define la tension en la CARGA como dato; la fuente y
                     la corriente se derivan.  Ej: vcarga 110-20j
  linea <Z>          Define la impedancia de linea (serie).
  carga <Z>          (MODO MONO) Agrega una carga en paralelo.  Ej: carga 10+20j
  carga <Y|Delta> <Z>
                     (MODO TRI) Agrega una carga (conversion D->Y automatica).
                     Ej: carga Delta 30+40j | carga Y 50/30
  pcarga <S> [Vnom]  (MODO MONO) Carga por su POTENCIA total.
  pcarga <Y|Delta> <S> [Vnom]
                     (MODO TRI) Carga por potencia con su conexion.
                     Ej: pcarga Y 1200+1600j
  add ...            Igual que 'carga' (en el modo actual).
  cargas             Muestra las cargas definidas del modo actual.
  limpiar            Elimina todas las cargas del modo actual.

RESOLUCION
  resolver | solve   Resuelve el circuito y muestra el reporte completo.
  variables | todo   Muestra el reporte completo de todas las variables.

CONSULTA DE VARIABLES (tras resolver)
  vl                 Tensiones de linea (fuente y carga).
  vf                 Tensiones de fase (fuente y carga).
  il                 Corriente de linea.
  if                 Corrientes de fase de cada carga.
  s | potencia       S, P, Q, |S|, FP y phi totales.
  exportar [fmt] [nom] Exporta el reporte del circuito a TXT, JSON o CSV.
                     Ej: exportar json | exportar csv mi_circuito.csv
  grafica [fasores|potencia]
                     Muestra el diagrama fasorial polar o triangulo P-Q.
                     Ej: grafica | grafica potencia
  ver                Muestra el estado actual del circuito y que falta.
  reporte            Muestra el ultimo reporte generado.
  ayuda | help       Muestra esta ayuda.
  salir | exit | quit  Termina la consola.

MENSAJES DE ERROR
  Si un comando esta mal escrito o le faltan datos, la consola avisa con un
  mensaje claro y no se detiene. Si falta un dato para resolver, use 'ver'
  para ver que falta, o 'ayuda' para ver los comandos.

Ejemplos:
  fuente 208
  linea 0.1+0.05j
  carga Delta 30+40j
  carga Y 20-15j
  resolver
  vf
  if
  detalle 1
  s

  # Variantes de datos:
  fuente 120 fase            # tiene V_f en vez de V_L
  corriente 30-40j           # tiene la corriente medida
  vcarga 110-20j             # tiene la tension en la carga
  linea 30 angulo 53.13      # impedancia en polar
  carga Y 10 20              # impedancia por R y X
  pcarga Y 1200+1600j        # carga por potencia
"""


class SesionConsola:
    """Estado de la consola: modo activo (mono/tri) y ambos circuitos."""

    def __init__(self, modo="tri"):
        self.mono = CircuitoMonofasico()
        self.tri = CircuitoTrifasico()
        self.modo = modo

    @property
    def circuito(self):
        return self.mono if self.modo == "mono" else self.tri

    def cambiar_modo(self, modo):
        m = modo.lower()
        if m in ("mono", "monofasico", "1", "1f"):
            self.modo = "mono"
        elif m in ("tri", "trifasico", "3", "3f"):
            self.modo = "tri"
        else:
            error_analizador("circuito", "argumentos",
                             "Modo no valido: '{0}'. Use 'mono' o 'tri'.".format(modo))
        return self.modo


def consola(modo="tri"):
    """Consola interactiva con comandos naturales (REPL moderno).

    Trabaja en modo monofasico o trifasico; se elige con 'modo mono'/'modo
    tri' o al resolver con 'resolver mono'/'resolver tri'. Usa prompt_toolkit
    (edicion con flechas e historial) y rich para la presentacion.
    """
    sesion = SesionConsola(modo=modo)
    _consola.print(
        Panel(
            "Consola de circuitos (monofasico y trifasico)\n"
            f"[bold cyan]Modo actual:[/] {sesion.modo}  "
            f"[dim](cambie con 'modo mono' o 'modo tri')[/]\n"
            "[dim]Escriba 'ayuda' para ver los comandos y ejemplos. "
            "Escriba 'salir' para terminar.[/]",
            title="Circuito",
            border_style="cyan",
        )
    )

    while True:
        try:
            linea = prompt("circuito> ").strip()
        except (EOFError, KeyboardInterrupt):
            _consola.print("\n[bold]Fin del entorno de circuito.[/]")
            break
        if not linea:
            continue
        if linea.lower() in ("salir", "exit", "quit", "q"):
            _consola.print("[bold]Fin del entorno de circuito.[/]")
            break
        comando = linea.split()[0].lower()
        if comando not in _COMANDOS_VALIDOS:
            sugerencia = _sugerir_comando(comando)
            if sugerencia:
                _consola.print(
                    Panel(
                        f"No reconozco '[bold]{comando}[/]'. "
                        f"\n\n[bold yellow]¿Quisiste decir '{sugerencia}'?[/]",
                        title="Comando no reconocido",
                        border_style="yellow",
                    )
                )
            else:
                _consola.print(
                    Panel(
                        f"No reconozco '[bold]{comando}[/]'. "
                        "Escriba 'ayuda' para ver los comandos.",
                        title="Comando no reconocido",
                        border_style="yellow",
                    )
                )
            continue
        try:
            _ejecutar_comando(sesion, linea)
        except AnalizadorError as err:
            _consola.print(
                Panel(
                    f"[bold red]{err.mensaje}[/]\n\n"
                    "[dim]Tip: escriba 'ayuda' para ver los comandos, o "
                    "'ver' para revisar el estado.[/]",
                    title="Error",
                    border_style="red",
                )
            )
        except Exception as err:
            _consola.print(
                Panel(
                    f"[bold red]Error inesperado:[/] {err}\n\n"
                    "[dim]Tip: escriba 'ayuda' para ver los comandos.[/]",
                    title="Error",
                    border_style="red",
                )
            )


def _diagnostico(circuito):
    """Devuelve una lista de datos que faltan para poder resolver.

    La resolución necesita: al menos un dato de excitación (fuente,
    corriente o tensión en la carga) y al menos una carga. Funciona para
    ``CircuitoMonofasico`` y ``CircuitoTrifasico``.
    """
    faltan = []
    if isinstance(circuito, CircuitoMonofasico):
        tiene_fuente = circuito.v_fuente is not None
        cmd_fuente = "'fuente <V>'"
        cmd_carga = "'carga <Z>' o 'pcarga <S>'"
    else:
        tiene_fuente = circuito.v_fuente_fase is not None
        cmd_fuente = "'fuente <VL>' o 'fuente <Vf> fase'"
        cmd_carga = "'carga <Y|Delta> <Z>' o 'pcarga <Y|Delta> <S>'"
    if not tiene_fuente and circuito.i_fuente is None \
            and circuito.v_carga_dato is None:
        faltan.append("defina la fuente (%s), la corriente ('corriente <I>') "
                      "o la tension en la carga ('vcarga <V>')." % cmd_fuente)
    if len(circuito.cargas) == 0:
        faltan.append("agregue al menos una carga (%s)." % cmd_carga)
    return faltan


def _normalizar_sesion(entrada):
    """Convierte la entrada a una ``SesionConsola``.

    Acepta una ``SesionConsola`` o directamente un ``CircuitoTrifasico`` /
    ``CircuitoMonofasico`` (para compatibilidad en pruebas).
    """
    if isinstance(entrada, SesionConsola):
        return entrada
    if isinstance(entrada, CircuitoMonofasico):
        sesion = SesionConsola(modo="mono")
        sesion.mono = entrada
        return sesion
    if isinstance(entrada, CircuitoTrifasico):
        sesion = SesionConsola(modo="tri")
        sesion.tri = entrada
        return sesion
    error_analizador("circuito", "argumentos",
                     "Se esperaba una SesionConsola o un circuito.")


def _es_mono(circuito):
    return isinstance(circuito, CircuitoMonofasico)


def _set_fuente(circuito, v, angulo, dato="linea"):
    if _es_mono(circuito):
        circuito.set_fuente(v, angulo)
    else:
        circuito.set_fuente(v, angulo, dato)


def _mostrar_fuente(circuito):
    tabla = Table(title="Fuente", border_style="cyan", box=None)
    tabla.add_column("Variable", style="bold")
    tabla.add_column("Valor", style="green")
    if _es_mono(circuito):
        tabla.add_row("V (tension)", _fasor(circuito.v_fuente))
    else:
        tabla.add_row("V_L (tension de linea)", f"{circuito.v_linea:.4g} V")
        tabla.add_row("V_f (fase a)", _fasor(circuito.v_fuente_fase))
    _consola.print(tabla)


def _ejecutar_comando(sesion, linea):
    """Ejecuta una línea de comando y devuelve True si se continuó con éxito."""
    sesion = _normalizar_sesion(sesion)
    circuito = sesion.circuito
    partes = linea.split()
    cmd = partes[0].lower()
    args = partes[1:]

    if cmd in ("ayuda", "help", "?"):
        _consola.print(Panel(_AYUDA, title="Ayuda", border_style="blue"))
        return

    if cmd in ("modo", "tipo"):
        if len(args) < 1:
            _consola.print(
                f"[bold cyan]Modo actual:[/] {sesion.modo}  "
                "[dim]('modo mono' o 'modo tri')[/]"
            )
            return
        nuevo = sesion.cambiar_modo(args[0])
        circuito = sesion.circuito
        _consola.print(f"[bold green]Modo:[/] {nuevo}")
        return

    if cmd in ("fuente", "vfuente", "set-fuente"):
        if len(args) < 1:
            error_analizador("circuito", "argumentos",
                             "Uso: fuente <magnitud> [linea|fase] [angulo]  |  fuente <fasor>")
        # Detectar la palabra 'angulo' como separador: fuente 208 angulo 45
        if "angulo" in [a.lower() for a in args]:
            partes_txt = " ".join(args)
            m = re.fullmatch(r"([+-]?[\d.]+)\s+angulo\s+([+-]?[\d.]+)(?:\s+(fase|linea|f|l))?",
                             partes_txt, re.IGNORECASE)
            if m:
                mag = float(m.group(1))
                angulo = float(m.group(2))
                dato = "fase" if m.group(3) and m.group(3).lower() in ("fase", "f") else "linea"
                _set_fuente(circuito, mag, angulo, dato)
                _mostrar_fuente(circuito)
                return
        # Si el primer argumento es un fasor con angulo o imaginario:
        # fuente 120@30, fuente 120/30, fuente 120<30, fuente 96.4+64.3j
        if _tiene_angulo(args[0]):
            try:
                v_fasor = parse_complejo(args[0])
            except AnalizadorError:
                error_analizador("circuito", "argumentos",
                                 "El valor de la fuente debe ser un numero o un fasor (ej. 'fuente 208', 'fuente 120 fase', 'fuente 120@30'). Valor: '{0}'", args[0])
            mag = abs(v_fasor)
            angulo = np.rad2deg(np.angle(v_fasor))
            dato = "linea"
            if len(args) > 1 and args[1].lower() in ("fase", "f", "phase", "vf"):
                dato = "fase"
            _set_fuente(circuito, mag, angulo, dato)
            _mostrar_fuente(circuito)
            return
        try:
            v = float(args[0])
        except ValueError:
            error_analizador("circuito", "argumentos",
                             "El valor de la fuente debe ser un numero (ej. 'fuente 208' o 'fuente 120 fase'). Valor: '{0}'", args[0])
        dato = "linea"
        angulo = 0.0
        try:
            if len(args) >= 2:
                if args[1].lower() in ("linea", "l", "line", "vl"):
                    dato = "linea"
                    angulo = float(args[2]) if len(args) > 2 else 0.0
                elif args[1].lower() in ("fase", "f", "phase", "vf"):
                    dato = "fase"
                    angulo = float(args[2]) if len(args) > 2 else 0.0
                else:
                    # el segundo argumento es el angulo (compatibilidad)
                    angulo = float(args[1])
        except ValueError:
            error_analizador("circuito", "argumentos",
                             "El angulo debe ser un numero en grados (ej. 'fuente 208 15').")
        _set_fuente(circuito, v, angulo, dato)
        _mostrar_fuente(circuito)
        return

    if cmd in ("linea", "zlinea", "set-linea"):
        if len(args) < 1:
            error_analizador("circuito", "argumentos",
                             "Uso: linea <R+jX | M angulo A | R X>")
        z = parse_impedancia(args)
        circuito.set_linea(z)
        _consola.print(f"[bold cyan]Linea:[/] Z = [green]{_fmt(z)}[/]")
        return

    if cmd in ("carga", "add", "agregar"):
        if len(args) < 1:
            error_analizador("circuito", "argumentos",
                             "Uso: carga <R+jX | M angulo A | R X>"
                             if _es_mono(circuito) else
                             "Uso: carga <Y|Delta> <R+jX | M angulo A | R X>")
        if _es_mono(circuito):
            # en mono no hay conexion Y/Delta
            if args[0].lower() in ("y", "delta", "estrella", "d"):
                z = parse_impedancia(args[1:])
            else:
                z = parse_impedancia(args)
            circuito.agregar_carga(z)
            n = len(circuito.cargas)
            _consola.print(
                f"[bold green]Carga {n}:[/] Z = [yellow]{_fmt(circuito.cargas[-1])}[/]"
            )
            return
        if len(args) < 2:
            error_analizador("circuito", "argumentos",
                             "Uso: carga <Y|Delta> <R+jX | M angulo A | R X>")
        conexion = args[0]
        z = parse_impedancia(args[1:])
        circuito.agregar_carga(conexion, z)
        n = len(circuito.cargas)
        c = circuito.cargas[-1]
        _consola.print(
            f"[bold green]Carga {n} ({c['conexion']}):[/] "
            f"Z_fase = [yellow]{_fmt(c['z_fase'])}[/] -> "
            f"Z_Y = [yellow]{_fmt(c['z_y'])}[/]"
        )
        return

    if cmd in ("pcarga", "p-carga", "potencia-carga"):
        # carga definida por su potencia S. En tri: pcarga <Y|Delta> <S> [V_nominal].
        # En mono: pcarga <S> [V_nominal].
        if len(args) < 1:
            error_analizador("circuito", "argumentos",
                             "Uso: pcarga <S | M angulo A> [V_nominal]"
                             if _es_mono(circuito) else
                             "Uso: pcarga <Y|Delta> <S | M angulo A> [V_nominal]")
        if _es_mono(circuito):
            v_nominal = None
            if len(args) >= 2 and not _tiene_angulo(args[-1]):
                try:
                    v_nominal = float(args[-1])
                    s = parse_complejo(" ".join(args[:-1]))
                except Exception:
                    v_nominal = None
                    s = parse_complejo(" ".join(args))
            else:
                s = parse_complejo(" ".join(args))
            circuito.agregar_carga_por_potencia(s, v_nominal)
            n = len(circuito.cargas)
            _consola.print(
                f"[bold green]Carga {n} por potencia:[/] "
                f"S = [yellow]{_fmt(s)}[/] -> Z = [yellow]{_fmt(circuito.cargas[-1])}[/]"
            )
            return
        if len(args) < 2:
            error_analizador("circuito", "argumentos",
                             "Uso: pcarga <Y|Delta> <S | M angulo A> [V_nominal]")
        conexion = args[0]
        v_nominal = None
        if len(args) >= 3 and not _tiene_angulo(args[-1]):
            try:
                v_nominal = float(args[-1])
                s = parse_complejo(" ".join(args[1:-1]))
            except Exception:
                v_nominal = None
                s = parse_complejo(" ".join(args[1:]))
        else:
            s = parse_complejo(" ".join(args[1:]))
        circuito.agregar_carga_por_potencia(conexion, s, v_nominal)
        n = len(circuito.cargas)
        c = circuito.cargas[-1]
        _consola.print(
            f"[bold green]Carga {n} ({c['conexion']}) por potencia:[/] "
            f"S = [yellow]{_fmt(s)}[/] -> Z_fase = [yellow]{_fmt(c['z_fase'])}[/]"
        )
        return

    if cmd in ("corriente", "ifuente", "corriente-fuente"):
        if len(args) < 1:
            error_analizador("circuito", "argumentos",
                             "Uso: corriente <I | M angulo A | R X>")
        i = parse_complejo(" ".join(args))
        circuito.set_corriente(i)
        _consola.print(
            f"[bold cyan]Corriente de la fuente:[/] I = [green]{_fasor(i)}[/]"
        )
        return

    if cmd in ("vcarga", "v-carga", "tension-carga"):
        if len(args) < 1:
            error_analizador("circuito", "argumentos",
                             "Uso: vcarga <V | M angulo A | R X>")
        v = parse_complejo(" ".join(args))
        circuito.set_v_carga(v)
        _consola.print(
            f"[bold cyan]Tension en la carga:[/] V_f = [green]{_fasor(v)}[/]"
        )
        return

    if cmd in ("cargas", "list"):
        if len(circuito.cargas) == 0:
            _consola.print("[yellow]No hay cargas definidas.[/]")
            return
        tabla = Table(title="Cargas", border_style="cyan")
        if _es_mono(circuito):
            tabla.add_column("#", style="bold")
            tabla.add_column("Z", style="green")
            for i, c in enumerate(circuito.cargas, start=1):
                tabla.add_row(str(i), _fmt(c))
        else:
            tabla.add_column("#", style="bold")
            tabla.add_column("Conexion", style="cyan")
            tabla.add_column("Z_fase", style="green")
            tabla.add_column("Z_Y", style="green")
            for i, c in enumerate(circuito.cargas, start=1):
                tabla.add_row(str(i), c["conexion"], _fmt(c["z_fase"]),
                              _fmt(c["z_y"]))
        _consola.print(tabla)
        return

    if cmd in ("limpiar", "reset", "clear"):
        circuito.limpiar_cargas()
        _consola.print("[green]Cargas eliminadas.[/]")
        return

    if cmd in ("resolver", "solve"):
        # resolver [mono|tri]: permite elegir el modo al resolver
        if len(args) >= 1 and args[0].lower() in ("mono", "monofasico", "1", "1f"):
            sesion.cambiar_modo("mono")
            circuito = sesion.circuito
        elif len(args) >= 1 and args[0].lower() in ("tri", "trifasico", "3", "3f"):
            sesion.cambiar_modo("tri")
            circuito = sesion.circuito
        faltan = _diagnostico(circuito)
        if faltan:
            _consola.print(
                Panel(
                    f"No se puede resolver el circuito ({sesion.modo}) todavia:\n"
                    + "\n".join(f"  - {linea}" for linea in faltan),
                    title="Faltan datos",
                    border_style="yellow",
                )
            )
            return
        try:
            circuito.resolver()
            _consola.print(
                Panel(circuito.reporte(), title="Resultado", border_style="green")
            )
        except Exception as err:
            _consola.print(
                Panel(
                    f"[bold red]{err}[/]\n\n"
                    "[dim]Tip: escriba 'ver' para revisar el estado del circuito.[/]",
                    title="Error",
                    border_style="red",
                )
            )
        return

    if cmd in ("reporte", "report"):
        try:
            _consola.print(
                Panel(circuito.reporte(), title="Reporte", border_style="green")
            )
        except Exception as err:
            _consola.print(
                Panel(
                    f"[bold red]{err}[/]\n\n"
                    "[dim]Tip: resuelva primero con 'resolver'.[/]",
                    title="Error",
                    border_style="red",
                )
            )
        return

    if cmd in ("ver", "estado", "show"):
        tabla = Table(title=f"Estado (modo {sesion.modo})", border_style="cyan")
        tabla.add_column("Variable", style="bold")
        tabla.add_column("Valor", style="green")
        if _es_mono(circuito):
            v = circuito.v_fuente
            tabla.add_row("Fuente V", _fasor(v) if v is not None
                          else "no definida")
        else:
            v = circuito.v_fuente_fase
            tabla.add_row("Fuente VL",
                          f"{circuito.v_linea:g} V, fase a = {_fasor(v)}"
                          if v is not None else "no definida")
        if circuito.i_fuente is not None:
            tabla.add_row("Corriente (dato)", _fasor(circuito.i_fuente))
        if circuito.v_carga_dato is not None:
            tabla.add_row("V en carga (dato)", _fasor(circuito.v_carga_dato))
        tabla.add_row("Linea Z", _fmt(circuito.z_linea))
        for i, c in enumerate(circuito.cargas, start=1):
            if _es_mono(circuito):
                tabla.add_row(f"Carga {i} Z", _fmt(c))
            elif c.get("por_potencia"):
                tabla.add_row(
                    f"Carga {i} ({c['conexion']})",
                    f"S = {_fmt(c.get('s_total', 0))} (por potencia) -> "
                    f"Z_fase = {_fmt(c['z_fase'])}",
                )
            else:
                tabla.add_row(f"Carga {i} ({c['conexion']})",
                              f"Z_fase = {_fmt(c['z_fase'])}")
        if circuito.z_eq is not None:
            tabla.add_row("Z_eq calculada", _fmt(circuito.z_eq))
        _consola.print(tabla)
        faltan = _diagnostico(circuito)
        if faltan:
            _consola.print(
                Panel(
                    "\n".join(f"  - {linea}" for linea in faltan),
                    title="Faltan datos para resolver",
                    border_style="yellow",
                )
            )
        else:
            _consola.print("[bold green]Listo para resolver:[/] escriba 'resolver'.")
        return

    # --- comandos de consulta de variables del circuito resuelto ---
    if cmd in ("variables", "todo", "reporte-completo"):
        if circuito.resultado is None:
            _consola.print(
                Panel("[red]Resuelva el circuito primero con 'resolver'.[/]",
                      title="Error", border_style="red")
            )
            return
        _consola.print(
            Panel(circuito.reporte(), title="Reporte completo", border_style="green")
        )
        return

    if cmd in ("vl", "vlinea", "tension-linea"):
        if _es_mono(circuito):
            _consola.print(
                "[yellow]En modo monofasico no hay tension de linea/fase; "
                "use 'vf'.[/]"
            )
            return
        if circuito.resultado is None:
            _consola.print(
                Panel("[red]Resuelva el circuito primero con 'resolver'.[/]",
                      title="Error", border_style="red")
            )
            return
        r = circuito.resultado
        _consola.print(f"[bold cyan]V_L fuente:[/] {_fasor(r.v_fuente_linea)}")
        _consola.print(f"[bold cyan]V_L carga:[/]  {_fasor(r.v_carga * (3 ** 0.5))}")
        return

    if cmd in ("vf", "vfase", "tension-fase"):
        if circuito.resultado is None:
            _consola.print(
                Panel("[red]Resuelva el circuito primero con 'resolver'.[/]",
                      title="Error", border_style="red")
            )
            return
        r = circuito.resultado
        if _es_mono(circuito):
            _consola.print(f"[bold cyan]V fuente:[/] {_fasor(r.v_fuente)}")
            _consola.print(f"[bold cyan]V carga:[/]  {_fasor(r.v_carga)}")
        else:
            _consola.print(f"[bold cyan]V_f fuente:[/] {_fasor(r.v_fuente_fase)}")
            _consola.print(f"[bold cyan]V_f carga:[/]  {_fasor(r.v_carga)}")
        return

    if cmd in ("il", "icorriente-linea", "corriente-linea"):
        if circuito.resultado is None:
            _consola.print(
                Panel("[red]Resuelva el circuito primero con 'resolver'.[/]",
                      title="Error", border_style="red")
            )
            return
        _consola.print(
            f"[bold cyan]I:[/] {_fasor(circuito.resultado.i_linea)}  "
            f"[dim](|I| = {abs(circuito.resultado.i_linea):.4f} A)[/]"
        )
        return

    if cmd in ("if", "corriente-fase", "ifase"):
        if circuito.resultado is None:
            _consola.print(
                Panel("[red]Resuelva el circuito primero con 'resolver'.[/]",
                      title="Error", border_style="red")
            )
            return
        r = circuito.resultado
        tabla = Table(title="Corrientes por carga", border_style="cyan")
        tabla.add_column("#", style="bold")
        tabla.add_column("Conexion", style="cyan")
        tabla.add_column("I", style="green")
        tabla.add_column("|I| (A)", style="green")
        for c in r.cargas:
            if _es_mono(circuito):
                tabla.add_row(str(c["id"]), "-", _fasor(c["i"]),
                              f"{abs(c['i']):.4f}")
            else:
                tabla.add_row(str(c["id"]), c["conexion"], _fasor(c["i_fase"]),
                              f"{abs(c['i_fase']):.4f}")
        _consola.print(tabla)
        return

    if cmd in ("s", "potencia", "poder"):
        if circuito.resultado is None:
            _consola.print(
                Panel("[red]Resuelva el circuito primero con 'resolver'.[/]",
                      title="Error", border_style="red")
            )
            return
        r = circuito.resultado
        s_total = r.s if _es_mono(circuito) else r.s3f
        tabla = Table(title="Potencia", border_style="cyan", box=None)
        tabla.add_column("Magnitud", style="bold")
        tabla.add_column("Valor", style="green")
        tabla.add_row("S", _fmt(s_total))
        tabla.add_row("P (W)", f"{r.P:.4f}")
        tabla.add_row("Q (var)", f"{r.Q:.4f}")
        tabla.add_row("|S| (VA)", f"{r.Sabs:.4f}")
        tabla.add_row("FP", f"{r.fp:.4f}")
        tabla.add_row("phi (deg)", f"{r.phi_deg:.4f}")
        _consola.print(tabla)
        return

    if cmd in ("detalle", "carga-detalle", "dcarga"):
        # consultar el detalle de una carga específica
        if circuito.resultado is None:
            _consola.print(
                Panel("[red]Resuelva el circuito primero con 'resolver'.[/]",
                      title="Error", border_style="red")
            )
            return
        r = circuito.resultado
        if len(args) >= 1:
            try:
                idx = int(args[0])
            except ValueError:
                error_analizador("circuito", "argumentos",
                                 "Uso: detalle <n>  (numero de carga, 1..%d)" % len(r.cargas))
            if idx < 1 or idx > len(r.cargas):
                error_analizador("circuito", "argumentos",
                                 "Uso: detalle <n>  (numero de carga, 1..%d)" % len(r.cargas))
            c = r.cargas[idx - 1]
            tabla = Table(title=f"Carga {c['id']}", border_style="cyan", box=None)
            tabla.add_column("Variable", style="bold")
            tabla.add_column("Valor", style="green")
            if _es_mono(circuito):
                tabla.add_row("Z", _fmt(c["z"]))
                tabla.add_row("V", _fasor(c["v"]))
                tabla.add_row("I", f"{_fasor(c['i'])}  (|I| = {abs(c['i']):.4f} A)")
                tabla.add_row("S", _fmt(c["s"]))
                tabla.add_row("P", f"{c['P']:.4f} W")
                tabla.add_row("Q", f"{c['Q']:.4f} var")
                tabla.add_row("|S|", f"{c['Sabs']:.4f} VA")
                tabla.add_row("FP", f"{c['fp']:.4f} ({c['type']}), phi = {c['phi_deg']:.4f} deg")
            else:
                tabla.add_row("Z_fase", _fmt(c["z_fase"]))
                tabla.add_row("Z_Y", _fmt(c["z_y"]))
                tabla.add_row("V_f", _fasor(c["v_fase"]))
                tabla.add_row("V_L", _fasor(c["v_linea_fasor"]))
                tabla.add_row("I_f", f"{_fasor(c['i_fase'])}  (|I| = {abs(c['i_fase']):.4f} A)")
                tabla.add_row("I_L", f"{_fasor(c['i_linea'])}  (|I| = {abs(c['i_linea']):.4f} A)")
                tabla.add_row("S", _fmt(c["s3f"]))
                tabla.add_row("P", f"{c['P']:.4f} W")
                tabla.add_row("Q", f"{c['Q']:.4f} var")
                tabla.add_row("|S|", f"{c['Sabs']:.4f} VA")
                tabla.add_row("FP", f"{c['fp']:.4f} ({c['type']}), phi = {c['phi_deg']:.4f} deg")
            _consola.print(tabla)
            return
        _consola.print(
            f"[yellow]Uso: detalle <n>  (numero de carga, 1..{len(r.cargas)})[/]"
        )
        return

    if cmd in ("exportar", "export", "guardar"):
        if circuito.resultado is None:
            _consola.print("[red]Resuelva el circuito primero con 'resolver'.[/]")
            return
        formato = "txt"
        archivo = None
        if len(args) >= 1:
            if args[0].lower() in ("txt", "json", "csv", "xlsx"):
                formato = args[0].lower()
                if len(args) >= 2:
                    archivo = " ".join(args[1:])
            else:
                archivo = " ".join(args)
                import os
                ext = os.path.splitext(archivo)[1].lower().replace(".", "")
                if ext in ("txt", "json", "csv", "xlsx"):
                    formato = ext
        if not archivo:
            modo = sesion.modo
            archivo = "circuito_%s" % modo
        from ..utils import export_results, resolve_export_path
        try:
            if formato == "txt":
                ruta = resolve_export_path(archivo)
                ruta_creada = str(ruta)
                import os
                if not os.path.splitext(ruta_creada)[1]:
                    ruta_creada = ruta_creada + ".txt"
                with open(ruta_creada, "w", encoding="utf-8") as fh:
                    fh.write(circuito.reporte())
            else:
                ruta_creada = export_results(circuito.resultado, archivo, formato)
            _consola.print(f"[green]Reporte exportado exitosamente a:[/] {ruta_creada}")
        except Exception as err:
            _consola.print("[red]ERROR al exportar:[/] %s" % err)
        return

    if cmd in ("grafica", "graficar", "plot", "diagrama"):
        if circuito.resultado is None:
            _consola.print("[red]Resuelva el circuito primero con 'resolver'.[/]")
            return
        tipo_grafica = "fasores"
        if len(args) >= 1 and args[0].lower() in ("potencia", "triangulo", "p", "s"):
            tipo_grafica = "potencia"
        import matplotlib.pyplot as plt
        from ..gui.viz import phasor_plot, power_triangle
        try:
            r = circuito.resultado
            if tipo_grafica == "potencia":
                p_val = r.P
                q_val = r.Q
                ax = power_triangle(p_val, q_val, titulo="Triangulo de Potencia - Circuito %s" % sesion.modo.capitalize())
            else:
                if _es_mono(circuito):
                    fasores = [r.v_fuente, r.i_linea, r.v_carga]
                    etiquetas = ["V_fuente", "I_linea", "V_carga"]
                else:
                    fasores = [r.v_fuente_fase, r.i_linea, r.v_carga]
                    etiquetas = ["Vf_fuente", "I_linea", "Vf_carga"]
                ax = phasor_plot(fasores, etiquetas=etiquetas, titulo="Diagrama Fasorial - Circuito %s" % sesion.modo.capitalize())
            plt.show()
            _consola.print("[green]Grafica generada correctamente.[/]")
        except Exception as err:
            _consola.print("[red]ERROR al generar grafica:[/] %s" % err)
        return

    # sugerir comandos parecidos si el usuario se equivoco de tipeo
    sugerencia = _sugerir_comando(cmd)
    if sugerencia:
        error_analizador("circuito", "comandoDesconocido",
                         "Error: comando no reconocido: '{0}'. Quizas quiso decir: {1}. Escriba 'ayuda' para la lista completa.", cmd, sugerencia)
    error_analizador("circuito", "comandoDesconocido",
                     "Error: comando no reconocido: '{0}'. Escriba 'ayuda' para ver la lista de comandos.", cmd)


_COMANDOS_VALIDOS = [
    "modo", "fuente", "corriente", "vcarga", "linea", "carga", "add",
    "pcarga", "cargas", "limpiar", "resolver", "solve", "reporte",
    "variables", "vl", "vf", "il", "if", "s", "potencia", "detalle", "ver",
    "exportar", "export", "guardar", "grafica", "graficar", "plot", "diagrama",
    "ayuda", "salir", "exit", "quit",
]


def _sugerir_comando(escrito):
    """Devuelve el comando valido mas parecido al texto escrito (o None)."""
    import difflib
    similares = difflib.get_close_matches(escrito, _COMANDOS_VALIDOS, n=1, cutoff=0.5)
    return similares[0] if similares else None
