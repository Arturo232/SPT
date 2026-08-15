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
from .errors import AnalizadorError, error_analizador
from .utils import input_helpers


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

    # forma polar con separadores: "M/A", "M∠A", "M<A" (con la i de "cis"
    # intacta: no convertimos a j en este paso)
    m = re.fullmatch(r"([+-]?[\d.]+(?:e[+-]?\d+)?)[/∠<]([+-]?[\d.]+(?:e[+-]?\d+)?)", t_sin)
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
    from .core import polar_to_complex
    return polar_to_complex(mag, ang)


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
    from .circuito import _fmt_complex
    return _fmt_complex(z)


def _fasor(z):
    """Fasor en forma rectangular + polar."""
    from .core import rad2deg
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
FORMATO DE IMPEDANCIAS Y FASORES (en cualquier comando):
  Rectangular : R+jX  (ej. 10+5j, 2-8j, 4j, j5)  o  R+iX (tambien con i)
  Polar       : M angulo A  |  M/A  |  M∠A  |  M<A  |  M exp(A)  |  M cis(A)
                (angulos en grados, con o sin sufijo deg/°)
                ej. 30 angulo 53.13, 50/30, 30∠53.13, 30<53.13, 50 exp(30)
  R y X sueltos: dos numeros (ej. 10 20)

DEFINICION DEL CIRCUITO
  fuente <magnitud> [linea|fase] [angulo]
                     Define la tension de la fuente. Por defecto se
                     interpreta como tension de LINEA (VL); use 'fase' si
                     el dato es la tension de fase (Vf).
                     Ej: fuente 208  |  fuente 120 fase  |  fuente 120 f 0
  corriente <I>      Define la corriente de la fuente como dato (I_L o I_f);
                     la fuente se deriva.  Ej: corriente 30-40j
  vcarga <V>         Define la tension en la CARGA como dato; la fuente y
                     la corriente se derivan.  Ej: vcarga 110-20j
  linea <Z>          Define la impedancia de linea (serie).
  carga <Y|Delta> <Z>
                     Agrega una carga en paralelo (conversion D->Y
                     automatica).  Ej: carga Delta 30+40j | carga Y 50/30
  pcarga <Y|Delta> <S> [V_nominal]
                     Agrega una carga por su POTENCIA compleja total
                     (se convierte a impedancia con la tension nominal).
                     Ej: pcarga Y 1200+1600j
  add <Y|D> <Z>      Igual que 'carga'.
  cargas             Muestra las cargas definidas.
  limpiar            Elimina todas las cargas.

RESOLUCION
  resolver | solve   Resuelve el circuito y muestra el reporte completo.
  variables | todo   Muestra el reporte completo de todas las variables.

CONSULTA DE VARIABLES (tras resolver)
  vl                 Tensiones de linea (fuente y carga).
  vf                 Tensiones de fase (fuente y carga).
  il                 Corriente de linea.
  if                 Corrientes de fase de cada carga.
  s | potencia       S, P, Q, |S|, FP y phi totales.
  detalle <n>        Todas las variables de la carga n.

OTROS
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
        try:
            _ejecutar_comando(circuito, linea)
        except AnalizadorError as err:
            print("  ERROR: %s" % err.mensaje)
            print("  Tip: escriba 'ayuda' para ver los comandos, o 'ver' para revisar el estado.")
        except Exception as err:
            print("  ERROR inesperado: %s" % err)
            print("  Tip: escriba 'ayuda' para ver los comandos.")


def _diagnostico(circuito):
    """Devuelve una lista de datos que faltan para poder resolver.

    La resolución necesita: al menos un dato de excitación (fuente,
    corriente o tensión en la carga) y al menos una carga.
    """
    faltan = []
    if circuito.v_fuente_fase is None and circuito.i_fuente is None \
            and circuito.v_carga_dato is None:
        faltan.append("defina la fuente ('fuente <VL>' o 'fuente <Vf> fase'), "
                      "la corriente ('corriente <I>') o la tension en la carga "
                      "('vcarga <V>').")
    if len(circuito.cargas) == 0:
        faltan.append("agregue al menos una carga ('carga <Y|Delta> <Z>' o "
                      "'pcarga <Y|Delta> <S>').")
    return faltan


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
            error_analizador("circuito", "argumentos",
                             "Uso: fuente <magnitud> [linea|fase] [angulo]")
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
        circuito.set_fuente(v, angulo, dato)
        print("  Fuente: V_L = %.4g V | V_f = %.4g V (fase a = %s)"
              % (circuito.v_linea, abs(circuito.v_fuente_fase),
                 _fasor(circuito.v_fuente_fase)))
        return

    if cmd in ("linea", "zlinea", "set-linea"):
        if len(args) < 1:
            error_analizador("circuito", "argumentos",
                             "Uso: linea <R+jX | M angulo A | R X>")
        z = parse_impedancia(args)
        circuito.set_linea(z)
        print("  Linea: Z = %s" % _fmt(z))
        return

    if cmd in ("carga", "add", "agregar"):
        if len(args) < 2:
            error_analizador("circuito", "argumentos",
                             "Uso: carga <Y|Delta> <R+jX | M angulo A | R X>")
        conexion = args[0]
        z = parse_impedancia(args[1:])
        circuito.agregar_carga(conexion, z)
        n = len(circuito.cargas)
        c = circuito.cargas[-1]
        print("  Carga %d (%s): Z_fase = %s -> Z_Y = %s"
              % (n, c["conexion"], _fmt(c["z_fase"]), _fmt(c["z_y"])))
        return

    if cmd in ("pcarga", "p-carga", "potencia-carga"):
        # carga definida por su potencia total S (ej. "pcarga Y 1200+1600j"
        # o "pcarga Delta 5000 angulo 36.87" o "pcarga Y 1000 1000")
        if len(args) < 2:
            error_analizador("circuito", "argumentos",
                             "Uso: pcarga <Y|Delta> <S | M angulo A> [V_nominal]")
        conexion = args[0]
        s = parse_complejo(" ".join(args[1:]))
        v_nominal = None
        circuito.agregar_carga_por_potencia(conexion, s, v_nominal)
        n = len(circuito.cargas)
        c = circuito.cargas[-1]
        print("  Carga %d (%s) por potencia: S = %s -> Z_fase = %s"
              % (n, c["conexion"], _fmt(s), _fmt(c["z_fase"])))
        return

    if cmd in ("corriente", "ifuente", "corriente-fuente"):
        if len(args) < 1:
            error_analizador("circuito", "argumentos",
                             "Uso: corriente <I | M angulo A | R X>")
        i = parse_complejo(" ".join(args))
        circuito.set_corriente(i)
        print("  Corriente de la fuente: I = %s" % _fasor(i))
        return

    if cmd in ("vcarga", "v-carga", "tension-carga"):
        if len(args) < 1:
            error_analizador("circuito", "argumentos",
                             "Uso: vcarga <V | M angulo A | R X>")
        v = parse_complejo(" ".join(args))
        circuito.set_v_carga(v)
        print("  Tension en la carga: V_f = %s" % _fasor(v))
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
        faltan = _diagnostico(circuito)
        if faltan:
            print("  No se puede resolver el circuito todavia:")
            for linea in faltan:
                print("    - %s" % linea)
            return
        try:
            circuito.resolver()
            print(circuito.reporte())
        except Exception as err:
            print("  ERROR: %s" % err)
            print("  Tip: escriba 'ver' para revisar el estado del circuito.")
        return

    if cmd in ("reporte", "report"):
        try:
            print(circuito.reporte())
        except Exception as err:
            print("  ERROR: %s" % err)
            print("  Tip: resuelva primero con 'resolver'.")
        return

    if cmd in ("ver", "estado", "show"):
        v = getattr(circuito, "v_fuente_fase", None)
        if v is not None:
            print("  Fuente: VL = %g V, fase a = %s"
                  % (circuito.v_linea, _fasor(v)))
        else:
            print("  Fuente: no definida (use 'fuente', 'corriente' o 'vcarga')")
        if circuito.i_fuente is not None:
            print("  Corriente de fuente (dato): I = %s" % _fasor(circuito.i_fuente))
        if circuito.v_carga_dato is not None:
            print("  Tension en la carga (dato): V_f = %s" % _fasor(circuito.v_carga_dato))
        print("  Linea:  Z = %s" % _fmt(circuito.z_linea))
        print("  Cargas: %d" % len(circuito.cargas))
        for c in circuito.cargas:
            if c.get("por_potencia"):
                print("    %-4s S = %s (por potencia) -> Z_fase = %s"
                      % (c["conexion"], _fmt(c.get("s_total", 0)), _fmt(c["z_fase"])))
            else:
                print("    %-4s Z_fase = %s" % (c["conexion"], _fmt(c["z_fase"])))
        if circuito.z_eq is not None:
            print("  Z_eq calculada = %s" % _fmt(circuito.z_eq))
        faltan = _diagnostico(circuito)
        if faltan:
            print("  ---")
            print("  Faltan datos para resolver:")
            for linea in faltan:
                print("    - %s" % linea)
        else:
            print("  Listo para resolver: escriba 'resolver'.")
        return

    # --- comandos de consulta de variables del circuito resuelto ---
    if cmd in ("variables", "todo", "reporte-completo"):
        if circuito.resultado is None:
            print("  ERROR: resuelva el circuito primero con 'resolver'.")
            return
        print(circuito.reporte())
        return

    if cmd in ("vl", "vlinea", "tension-linea"):
        if circuito.resultado is None:
            print("  ERROR: resuelva el circuito primero con 'resolver'.")
            return
        r = circuito.resultado
        print("  V_L fuente = %s" % _fasor(r.v_fuente_linea))
        print("  V_L carga  = %s" % _fasor(r.v_carga * (3 ** 0.5)))
        return

    if cmd in ("vf", "vfase", "tension-fase"):
        if circuito.resultado is None:
            print("  ERROR: resuelva el circuito primero con 'resolver'.")
            return
        r = circuito.resultado
        print("  V_f fuente = %s" % _fasor(r.v_fuente_fase))
        print("  V_f carga  = %s" % _fasor(r.v_carga))
        return

    if cmd in ("il", "icorriente-linea", "corriente-linea"):
        if circuito.resultado is None:
            print("  ERROR: resuelva el circuito primero con 'resolver'.")
            return
        print("  I_L = %s  (|I| = %.4f A)" % (_fasor(circuito.resultado.i_linea),
                                              abs(circuito.resultado.i_linea)))
        return

    if cmd in ("if", "corriente-fase", "ifase"):
        if circuito.resultado is None:
            print("  ERROR: resuelva el circuito primero con 'resolver'.")
            return
        r = circuito.resultado
        print("  Corrientes de fase por carga:")
        for c in r.cargas:
            print("    C%d (%s): I_f = %s  (|I| = %.4f A)"
                  % (c["id"], c["conexion"], _fasor(c["i_fase"]), abs(c["i_fase"])))
        return

    if cmd in ("s", "potencia", "poder"):
        if circuito.resultado is None:
            print("  ERROR: resuelva el circuito primero con 'resolver'.")
            return
        r = circuito.resultado
        print("  S    = %s" % _fmt(r.s3f))
        print("  P    = %.4f W" % r.P)
        print("  Q    = %.4f var" % r.Q)
        print("  |S|  = %.4f VA" % r.Sabs)
        print("  FP   = %.4f" % r.fp)
        print("  phi  = %.4f deg" % r.phi_deg)
        return

    if cmd in ("detalle", "carga-detalle", "dcarga"):
        # consultar el detalle de una carga específica
        if circuito.resultado is None:
            print("  ERROR: resuelva el circuito primero con 'resolver'.")
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
            print("  C%d (%s): Z_fase = %s -> Z_Y = %s"
                  % (c["id"], c["conexion"], _fmt(c["z_fase"]), _fmt(c["z_y"])))
            print("    V_f = %s" % _fasor(c["v_fase"]))
            print("    V_L = %s" % _fasor(c["v_linea_fasor"]))
            print("    I_f = %s  (|I| = %.4f A)" % (_fasor(c["i_fase"]), abs(c["i_fase"])))
            print("    I_L = %s  (|I| = %.4f A)" % (_fasor(c["i_linea"]), abs(c["i_linea"])))
            print("    S   = %s" % _fmt(c["s3f"]))
            print("    P   = %.4f W ;  Q = %.4f var ;  |S| = %.4f VA"
                  % (c["P"], c["Q"], c["Sabs"]))
            print("    FP  = %.4f (%s), phi = %.4f deg"
                  % (c["fp"], c["type"], c["phi_deg"]))
            return
        print("  Uso: detalle <n>  (numero de carga, 1..%d)" % len(r.cargas))
        return

    # sugerir comandos parecidos si el usuario se equivoco de tipeo
    sugerencia = _sugerir_comando(cmd)
    if sugerencia:
        error_analizador("circuito", "comandoDesconocido",
                         "Error: comando no reconocido: '{0}'. Quizas quiso decir: {1}. Escriba 'ayuda' para la lista completa.", cmd, sugerencia)
    error_analizador("circuito", "comandoDesconocido",
                     "Error: comando no reconocido: '{0}'. Escriba 'ayuda' para ver la lista de comandos.", cmd)


_COMANDOS_VALIDOS = [
    "fuente", "corriente", "vcarga", "linea", "carga", "add", "pcarga",
    "cargas", "limpiar", "resolver", "solve", "reporte", "variables",
    "vl", "vf", "il", "if", "s", "potencia", "detalle", "ver", "ayuda",
    "salir", "exit", "quit",
]


def _sugerir_comando(escrito):
    """Devuelve el comando valido mas parecido al texto escrito (o None)."""
    import difflib
    similares = difflib.get_close_matches(escrito, _COMANDOS_VALIDOS, n=1, cutoff=0.5)
    return similares[0] if similares else None
