"""Bucle interactivo (REPL) e intérprete de comandos de la nueva consola.

Punto de entrada por defecto de la aplicación. Usa ``prompt_toolkit`` para
el autocompletado y la navegación de historial, y ``rich`` para la
presentación de banners, paneles, tablas y formularios didácticos.

Características de UX:
  - Los comandos desconocidos se corrigen con ``difflib`` (sugerencia).
  - Los formularios de cálculo son guiados, con explicaciones y unidades, y
    reintentan ante entradas inválidas sin abortar la sesión.
  - Los resultados se presentan en paneles estructurados con interpretación.
  - Navegación por contextos: ``exit``/``salir``/``volver`` cancelan el
    contexto actual (pila) y regresan al prompt principal ``SEP>``.
  - Gramática por niveles para ``trifasico``/``monofasico`` (sistema ->
    componente -> banderas) con errores sintácticos educativos, que convive
    con la sintaxis CLI legada (``--fuente``/``--cargas``).
"""

import difflib
import functools
from types import SimpleNamespace

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import InMemoryHistory

from analizador import __version__
from analizador.cli.banner import mostrar_banner


# ---------------------------------------------------------------------------
# Interpretación pedagógica de resultados por tema
# ---------------------------------------------------------------------------
_NOTAS = {
    "potenciaCompleja": (
        "La potencia compleja S = P + jQ agrupa la energia util (P, en W) y "
        "la energia reactiva (Q, en var). Si Q > 0 la carga es inductiva "
        "(FP en atraso); si Q < 0 es capacitiva (FP en adelanto)."
    ),
    "correccionFP": (
        "Corregir el factor de potencia reduce la corriente de linea y las "
        "perdidas, sin cambiar la potencia activa. Se agrega un banco de "
        "capacitores que aporta Qc negativa para compensar la reactiva "
        "inductiva de la carga."
    ),
    "flujoPotencia": (
        "El flujo de potencia entre dos fuentes depende del desfase de "
        "tensiones: la potencia activa fluye de la barra con angulo mayor a "
        "la de menor angulo, y la reactiva fluye de la de mayor tension."
    ),
    "perUnit": (
        "El sistema por unidad normaliza tensiones, corrientes e impedancias "
        "respecto de valores base, facilitando comparaciones entre "
        "distintos niveles de tension."
    ),
    "sistemasTrifasicos": (
        "En un sistema trifasico balanceado en Y: V_fase = VL/sqrt(3) e "
        "I_fase = I_linea. La potencia trifasica es S3f = 3 * V_fase * conj(I)."
    ),
}


# ---------------------------------------------------------------------------
# Helpers de captura de datos (didacticos, con reintento)
# ---------------------------------------------------------------------------
def _explicar(consola: Console, nombre: str, descripcion: str,
              unidad: str, ejemplo: str) -> None:
    """Muestra una breve explicacion de una variable antes de pedirla."""
    texto = Text()
    texto.append(f"[bold cyan]{nombre}[/]")
    if unidad:
        texto.append(f"  [dim][{unidad}][/]")
    texto.append("\n")
    texto.append(descripcion)
    texto.append("\n[dim]Ejemplo: ")
    texto.append(ejemplo, style="yellow")
    texto.append("[/]")
    consola.print(texto)


def _prompt_linea(prompt_texto: str, default: str = "") -> str | None:
    """Pide una linea con ``prompt_toolkit`` (edicion con flechas e historial).

    Regresa la linea ingresada, o ``None`` si el usuario cancela con
    ``Ctrl-C`` o cierra con ``Ctrl-D`` (EOF).
    """
    try:
        return prompt(prompt_texto, default=default).strip()
    except (KeyboardInterrupt, EOFError):
        return None


def _pedir_numero(consola: Console, nombre: str, descripcion: str,
                  unidad: str = "", ejemplo: str = "",
                  rango: tuple | None = None, convertir=float):
    """Pide un numero con explicacion, validacion y reintento.

    Parámetros:
        rango: tupla (min, max) inclusive, o None para sin rango.
        convertir: funcion de conversion (float, int).

    Regresa el valor ya convertido.
    """
    while True:
        _explicar(consola, nombre, descripcion, unidad, ejemplo)
        texto = _prompt_linea(f"[bold]{nombre}[/]")
        if texto is None:
            consola.print("\n[dim]Operacion cancelada.[/]")
            return None
        try:
            valor = convertir(texto)
        except (ValueError, TypeError):
            consola.print(
                f"[bold red]Valor invalido:[/] '{texto}' no es un numero. "
                "Intentemos de nuevo."
            )
            continue
        if rango is not None:
            minimo, maximo = rango
            if not (minimo <= valor <= maximo):
                consola.print(
                    f"[bold red]Fuera de rango:[/] {nombre} debe estar entre "
                    f"{minimo} y {maximo}. Recibido: {valor}. Intentemos de nuevo."
                )
                continue
        return valor


def _normalizar_opcion(texto: str) -> str:
    """Normaliza la entrada de una seleccion: minusculas y sin espacios."""
    return texto.strip().lower().replace(" ", "")


def _pedir_seleccion(consola: Console, titulo: str,
                     opciones: dict, default: str | None = None,
                     sinonimos: dict | None = None) -> str:
    """Pide una seleccion de menu aceptando numero, sigla o palabra clave.

    Parámetros:
        opciones: dict {clave: (etiqueta, descripcion)}.
            La clave es lo que se devuelve. ``etiqueta`` es lo que se muestra.
        default: clave por defecto si el usuario presiona Enter.
        sinonimos: dict {palabra_clave: clave} adicionales para la opcion.

    Regresa la clave seleccionada.
    """
    etiquetas = list(opciones.values())
    # construye mapa de alias: numero, clave normalizada y etiqueta normalizada
    alias: dict[str, str] = {}
    for idx, clave in enumerate(opciones, start=1):
        etiqueta, _ = opciones[clave]
        alias[str(idx)] = clave
        alias[_normalizar_opcion(clave)] = clave
        alias[_normalizar_opcion(etiqueta)] = clave
    # sinonimos contextuales: {palabra_clave: clave}
    for palabra, clave in (sinonimos or {}).items():
        if clave in opciones:
            alias[_normalizar_opcion(palabra)] = clave

    tabla = Table(title=titulo, border_style="cyan", box=None)
    tabla.add_column("#", style="bold yellow")
    tabla.add_column("Opcion", style="bold cyan")
    tabla.add_column("Descripcion", style="dim")
    for idx, clave in enumerate(opciones, start=1):
        etiqueta, desc = opciones[clave]
        tabla.add_row(str(idx), etiqueta, desc)
    consola.print(tabla)

    predeterminado = default
    while True:
        texto = _prompt_linea(
            "Elija un numero o una opcion",
            default=predeterminado or "",
        )
        if texto is None:
            consola.print("\n[dim]Operacion cancelada.[/]")
            return default or next(iter(opciones))
        if not texto.strip() and predeterminado:
            return predeterminado
        clave = alias.get(_normalizar_opcion(texto))
        if clave is not None:
            return clave
        consola.print(
            f"[bold red]Opcion invalida:[/] '{texto}'. "
            "Elija un numero (1, 2, ...) o una de las opciones mostradas."
        )


def _pedir_complejo(consola: Console, nombre: str, descripcion: str,
                    unidad: str = "", ejemplo: str = ""):
    """Pide un numero complejo (R + jX, polar M[ang] o real) con reintento."""
    from analizador.errors import AnalizadorError
    from analizador.services.asistente import parse_complejo

    while True:
        _explicar(consola, nombre, descripcion, unidad, ejemplo)
        texto = _prompt_linea(f"[bold]{nombre}[/]")
        if texto is None:
            consola.print("\n[dim]Operacion cancelada.[/]")
            return None
        try:
            return parse_complejo(texto)
        except (AnalizadorError, ValueError):
            consola.print(
                Panel(
                    "Valor no reconocido.\n\n"
                    "Formatos aceptados:\n"
                    "  • Polar       -> 200[30]  (magnitud[angulo])\n"
                    "  • Rectangular -> 2+5j  o  3+j7\n"
                    "  • Real        -> 200",
                    title="Entrada invalida",
                    border_style="red",
                )
            )
            continue


# ---------------------------------------------------------------------------
# Parser de argumentos de redes (trifasico / monofasico)
# ---------------------------------------------------------------------------
def _parse_complejo_valor(texto: str):
    """Convierte un token a complejo usando ``parse_complejo`` (rectangular
    flexible ``a+jb`` y polar ``M[ángulo]``)."""
    from analizador.errors import AnalizadorError
    from analizador.services.asistente import parse_complejo

    try:
        return parse_complejo(texto)
    except (AnalizadorError, ValueError) as err:
        raise ValueError(f"valor complejo invalido: '{texto}'") from err


def _parse_carga_token(token: str):
    """Interpreta un token de carga ``Tipo:Valor`` (tipo por defecto 'Y').

    Regresa ``(tipo, z)`` donde ``tipo`` es 'Y' o 'Delta'.
    """
    token = token.strip()
    if not token:
        raise ValueError("token de carga vacio")
    if ":" in token:
        tipo_txt, valor_txt = token.split(":", 1)
        tipo = tipo_txt.strip().upper()
        if tipo in ("Y", "ESTRELLA", "STAR"):
            tipo = "Y"
        elif tipo in ("D", "DELTA"):
            tipo = "Delta"
        else:
            raise ValueError(
                f"tipo de conexion no reconocido en '{token}'. Use 'Y:' o 'D:'.")
    else:
        tipo = "Y"
        valor_txt = token
    z = _parse_complejo_valor(valor_txt)
    return tipo, z


def _parse_fuente_token(token: str):
    """Interpreta un token de fuente ``Tipo:Valor``.

    Tipos aceptados:
      - ``L:`` tensión de línea (V_LL).
      - ``F:`` tensión de fase (V_LN).
      - Sin prefijo: se asume línea (L) por defecto.

    El valor complejo acepta rectangular ``a+jb`` o polar ``M[ángulo]``.
    Regresa ``(tipo, complejo)`` donde ``tipo`` es 'L' o 'F'.
    """
    token = token.strip()
    if not token:
        raise ValueError("token de fuente vacio")
    if token[0] in "lLfF" and len(token) > 1 and token[1] == ":":
        tipo_txt = token[0].upper()
        valor_txt = token[2:]
        tipo = "L" if tipo_txt == "L" else "F"
    else:
        tipo = "L"
        valor_txt = token
    z = _parse_complejo_valor(valor_txt)
    return tipo, z


def _parse_red_args(args: list[str]):
    """Interpreta los argumentos de línea de comando de una red.

    Opciones aceptadas:
      --fuente <Tipo:Valor>    Tensión de la fuente [V]. Puede llevar el
                               prefijo ``L:`` (línea, V_LL) o ``F:`` (fase,
                               V_LN). Sin prefijo se asume Línea.
      --cargas <Tipo:Valor>... Lista dinámica de 'N' cargas (1, 2 o N).
      --linea <Z>              Un tramo de impedancia de línea.
      --lineas <Z>...          Varios tramos de impedancia de línea (se suman).
      --paralelo               Bandera documentada: las cargas ya se reducen
                               en paralelo (no altera el cálculo).
      --taller                 Desglose académico inciso por inciso.
      --resolver-incisos       Alias de ``--taller``.
      --carga-fp <n>           Índice de la carga a corregir en FP (default 1).
      --fp <objetivo>          FP objetivo en atraso para la corrección
                               (default 0.8).

    Cada valor complejo acepta rectangular ``a+jb`` o polar ``M[ángulo]``.
    Regresa ``SimpleNamespace(fuente, fuente_tipo, cargas, lineas, paralelo,
    taller, carga_fp, fp_objetivo)``.
    """
    fuente = None
    fuente_tipo = "L"
    cargas: list[tuple[str, complex]] = []
    lineas: list[complex] = []
    paralelo = False
    taller = False
    carga_fp = 1
    fp_objetivo = 0.8

    i = 0
    n = len(args)
    while i < n:
        tok = args[i]
        if tok.startswith("--"):
            nombre = tok.lower()
            if nombre in ("--fuente", "-f"):
                if i + 1 >= n:
                    raise ValueError("falta el valor de --fuente")
                fuente_tipo, fuente = _parse_fuente_token(args[i + 1])
                i += 2
            elif nombre in ("--cargas", "-c"):
                # recoge todos los tokens siguientes que no sean una opcion
                j = i + 1
                if j >= n or args[j].startswith("--"):
                    raise ValueError("falta la lista de cargas en --cargas")
                while j < n and not args[j].startswith("--"):
                    cargas.append(_parse_carga_token(args[j]))
                    j += 1
                if not cargas:
                    raise ValueError("--cargas requiere al menos una carga")
                i = j
            elif nombre in ("--linea", "-l"):
                if i + 1 >= n:
                    raise ValueError("falta el valor de --linea")
                lineas.append(_parse_complejo_valor(args[i + 1]))
                i += 2
            elif nombre in ("--lineas", "-L"):
                j = i + 1
                if j >= n or args[j].startswith("--"):
                    raise ValueError("falta la lista de lineas en --lineas")
                while j < n and not args[j].startswith("--"):
                    lineas.append(_parse_complejo_valor(args[j]))
                    j += 1
                if not lineas:
                    raise ValueError("--lineas requiere al menos un tramo")
                i = j
            elif nombre == "--paralelo":
                paralelo = True
                i += 1
            elif nombre in ("--taller", "--resolver-incisos"):
                taller = True
                i += 1
            elif nombre == "--carga-fp":
                if i + 1 >= n:
                    raise ValueError("falta el valor de --carga-fp")
                try:
                    carga_fp = int(args[i + 1])
                except ValueError:
                    raise ValueError("--carga-fp debe ser un indice entero")
                if carga_fp < 1:
                    raise ValueError("--carga-fp debe ser >= 1")
                i += 2
            elif nombre == "--fp":
                if i + 1 >= n:
                    raise ValueError("falta el valor de --fp")
                try:
                    fp_objetivo = float(args[i + 1])
                except ValueError:
                    raise ValueError("--fp debe ser un numero")
                if not (0.0 < fp_objetivo <= 1.0):
                    raise ValueError("--fp debe estar entre 0 y 1")
                i += 2
            else:
                raise ValueError(f"opcion desconocida: '{tok}'")
        else:
            raise ValueError(f"argumento inesperado: '{tok}'. "
                             "Use --fuente, --cargas, --linea/--lineas.")
    return SimpleNamespace(fuente=fuente, fuente_tipo=fuente_tipo,
                           cargas=cargas, lineas=lineas, paralelo=paralelo,
                           taller=taller, carga_fp=carga_fp,
                           fp_objetivo=fp_objetivo)


def _aplicar_fuente(circuito, fuente: complex, fuente_tipo: str) -> dict:
    """Aplica la tensión de la fuente al circuito aplicando las conversiones.

    Regresa un dict con información de la conversión para el panel:
      ``{tipo, mag_entrada, ang_entrada, mag_fase, ang_fase, v_linea}``.

    Convenciones:
      - ``L`` (línea, V_LL):  V_LN = V_LL/sqrt(3) y, según la convención
        estándar, el fasor de fase 'a' se deriva restando 30° al ángulo de
        línea: ``v_fase_ang = ang_L - 30``.
      - ``F`` (fase, V_LN):   V_LL = sqrt(3)*V_LN; el ángulo es directamente
        el de la fase 'a'.
    """
    mag = abs(fuente)
    ang = _angulo_grados(fuente)
    tipo = fuente_tipo.upper() if fuente_tipo else "L"

    if tipo == "F":
        ang_fase = ang
        circuito.set_fuente(mag, ang_fase, "fase")
        info = {
            "tipo": "F",
            "mag_entrada": mag,
            "ang_entrada": ang,
            "mag_fase": mag,
            "ang_fase": ang_fase,
            "v_linea": circuito.v_linea,
        }
    else:  # L (por defecto)
        ang_fase = ang - 30.0
        circuito.set_fuente(mag, ang_fase, "linea")
        info = {
            "tipo": "L",
            "mag_entrada": mag,
            "ang_entrada": ang,
            "mag_fase": circuito.v_linea / _sqrt3(),
            "ang_fase": ang_fase,
            "v_linea": circuito.v_linea,
        }
    return info


def _angulo_grados(z) -> float:
    import math
    return math.degrees(math.atan2(z.imag, z.real))


def _sqrt3() -> float:
    import math
    return math.sqrt(3)


def _potencia_3f_por_linea(v_ll, i_l):
    """``S_3f = sqrt(3) * V_LL * conj(I_L)`` (valores de línea)."""
    return _sqrt3() * v_ll * (i_l.conjugate() if hasattr(i_l, "conjugate") else i_l)


def _admitancia_equivalente(z_eq):
    """Admitancia equivalente ``Y = 1/Z = G + jB`` [S].

    Regresa ``(Y, G, B)``.
    """
    if z_eq == 0:
        raise ValueError("impedancia equivalente cero")
    y = 1 / z_eq
    return y, y.real, y.imag


def _potencia_linea(v_caida, i_linea):
    """Potencia disipada en la línea: ``S = V_caida * conj(I)``."""
    return v_caida * (i_linea.conjugate() if hasattr(i_linea, "conjugate") else i_linea)


def _eficiencia(p_cargas, p_fuente):
    """Eficiencia de transmisión: ``eta = P_cargas / P_fuente * 100``."""
    if abs(p_fuente) < 1e-12:
        return float("nan")
    return p_cargas / p_fuente * 100.0


def _regulacion_voltaje(v_carga_linea, v_fuente_linea):
    """Regulación de voltaje en bornes: ``RV = (V_sin_carga - V_plena)/V_plena``.

    Aquí ``V_sin_carga`` se aproxima con la tensión de la fuente en vacío
    (``v_fuente_linea``) y ``V_plena`` con la de la carga.
    """
    if abs(v_carga_linea) < 1e-12:
        return float("nan")
    return (abs(v_fuente_linea) - abs(v_carga_linea)) / abs(v_carga_linea) * 100.0


# ---------------------------------------------------------------------------
# Renderizado estandarizado de redes (trifasico / monofasico)
# ---------------------------------------------------------------------------
def _fmt_complejo(z) -> str:
    from analizador.utils import format_complex

    rect, polar = format_complex(z)
    return f"{rect}  ({polar})"


def _fmt_estado(tipo: str) -> str:
    if tipo == "inductiva":
        return "inductivo (atraso)"
    if tipo == "capacitiva":
        return "capacitivo (adelanto)"
    return "resistivo"


def _renderizar_red(consola: Console, circuito, res, modo: str,
                    fuente_tipo: str = "L") -> None:
    """Renderiza las 4 componentes visuales de un circuito resuelto.

    Los paneles y tablas usan ``expand=True`` para adaptarse dinámicamente al
    ancho de la terminal (redimensionado automático).
    """
    es_tri = modo == "trifasico"

    # --- Panel 1: Datos de entrada ------------------------------------
    datos = Text()
    if es_tri:
        if fuente_tipo == "F":
            datos.append("Fuente (fase): V_f = ", style="bold")
        else:
            datos.append("Fuente (linea): V_L = ", style="bold")
        datos.append(f"{circuito.v_linea:g} V", style="yellow")
        datos.append("\n")
    else:
        datos.append("Fuente: V = ", style="bold")
        datos.append(f"{circuito.v:g} V", style="yellow")
        datos.append("\n")
    if circuito.z_linea:
        datos.append("Linea(s): Z_linea = ", style="bold")
        datos.append(_fmt_complejo(circuito.z_linea), style="green")
        datos.append("\n")
    for k, c in enumerate(circuito.cargas, start=1):
        datos.append(f"Carga C{k}: ", style="bold")
        if es_tri:
            datos.append(
                f"{c['conexion']}  Z = {_fmt_complejo(c['z_fase'])}",
                style="green")
        else:
            datos.append(f"Z = {_fmt_complejo(c)}", style="green")
        datos.append("\n")
    consola.print(Panel(datos, title="1. Datos de entrada",
                        border_style="cyan", expand=True))

    # --- Tabla 2: Proceso de reduccion ---------------------------------
    reduccion = Table(
        title="2. Proceso de reduccion (equivalente por fase)",
        border_style="blue", box=None, expand=True)
    reduccion.add_column("Carga", style="bold cyan")
    reduccion.add_column("Conexion", style="yellow")
    reduccion.add_column("Z_fase", style="green")
    reduccion.add_column("Z_Y equivalente", style="green")
    for k, c in enumerate(circuito.cargas, start=1):
        etiq = f"C{k}"
        if es_tri:
            z_fase = c["z_fase"]
            z_y = c["z_y"]
            if c["conexion"] == "Delta":
                reduccion.add_row(
                    etiq, "Delta", _fmt_complejo(z_fase),
                    f"{_fmt_complejo(z_y)}   (Z_Delta/3)")
            else:
                reduccion.add_row(etiq, "Y", _fmt_complejo(z_fase),
                                  _fmt_complejo(z_y))
        else:
            reduccion.add_row(etiq, "-", _fmt_complejo(c), _fmt_complejo(c))
    reduccion.add_section()
    reduccion.add_row("[bold]Z_cargas_eq[/]", "", "",
                      _fmt_complejo(res.z_eq), style="bold")
    reduccion.add_row("[bold]Z_total (linea + carga)[/]", "", "",
                      _fmt_complejo(res.z_total), style="bold")
    consola.print(reduccion)

    # --- Panel 3: Variables de estado ----------------------------------
    estado = Text()
    estado.append("Corriente de linea  I_L = ", style="bold")
    estado.append(_fmt_complejo(res.i_linea), style="green")
    estado.append(f"   (|I| = {abs(res.i_linea):.4g} A)")
    estado.append("\n")
    if es_tri:
        estado.append("Tension de fase en la carga  V_f = ", style="bold")
        estado.append(_fmt_complejo(res.v_carga), style="green")
        estado.append(f"   (|V| = {abs(res.v_carga):.4g} V)")
        estado.append("\n")
        estado.append("Tension de linea en la carga  V_L = ", style="bold")
        estado.append(f"{res.v_carga_linea:.4g} V", style="green")
        estado.append("\n")
    else:
        estado.append("Tension en la carga  V = ", style="bold")
        estado.append(_fmt_complejo(res.v_carga), style="green")
        estado.append(f"   (|V| = {abs(res.v_carga):.4g} V)")
        estado.append("\n")
    consola.print(Panel(estado, title="3. Variables de estado",
                        border_style="magenta", expand=True))

    # --- Tabla 4: Balance de potencia ----------------------------------
    balance = Table(
        title="4. Balance de potencia", border_style="green", box=None,
        expand=True)
    balance.add_column("Carga", style="bold cyan")
    balance.add_column("P [kW]", justify="right")
    balance.add_column("Q [kVAR]", justify="right")
    balance.add_column("S [kVA]", justify="right")
    balance.add_column("fp", justify="right")
    for k, c in enumerate(res.cargas, start=1):
        balance.add_row(
            f"C{k}",
            f"{c['P'] / 1000:.4g}",
            f"{c['Q'] / 1000:.4g}",
            f"{c['Sabs'] / 1000:.4g}",
            f"{c['fp']:.4g} ({_fmt_estado(c['type'])})",
        )
    balance.add_section()
    balance.add_row(
        "[bold]Total[/]",
        f"[bold]{res.P / 1000:.4g}[/]",
        f"[bold]{res.Q / 1000:.4g}[/]",
        f"[bold]{res.Sabs / 1000:.4g}[/]",
        f"[bold]{res.fp:.4g}[/] ({_fmt_estado(res.type)})",
    )
    consola.print(balance)

    # --- Tabla 5: Desglose trifasico por carga (solo trifasico) ---------
    if es_tri:
        _renderizar_desglose_trifasico(consola, res)

    # --- Panel 6: Interpretacion tecnica ---------------------------------
    _renderizar_panel_interpretativo(
        consola, circuito, res, es_tri, fuente_tipo)


def _fasores_abc(z):
    """Devuelve los tres fasores balanceados (a, b, c) desde la fase 'a'.

    ``b`` y ``c`` se rotan -120° y +120° respectivamente.
    """
    import math

    return (z,
            z * complex(math.cos(math.radians(-120)),
                         math.sin(math.radians(-120))),
            z * complex(math.cos(math.radians(120)),
                        math.sin(math.radians(120))))


def _renderizar_desglose_trifasico(consola: Console, res) -> None:
    """Renderiza la tabla 5: desglose trifásico completo (3 hilos) por carga.

    - Cargas en Estrella (Y): tensiones fase-neutro ``V_an, V_bn, V_cn`` y
      corrientes de línea ``I_a, I_b, I_c``.
    - Cargas en Delta (D): tensiones de línea ``V_ab, V_bc, V_ca`` y
      corrientes de fase de malla ``I_ab, I_bc, I_ca``.
    """
    tabla = Table(
        title="5. Desglose trifasico por carga (3 hilos)",
        border_style="yellow", box=None, expand=True)
    tabla.add_column("Carga", style="bold cyan")
    tabla.add_column("Magnitud", style="bold")
    tabla.add_column("Fase a", style="green")
    tabla.add_column("Fase b", style="green")
    tabla.add_column("Fase c", style="green")

    for k, c in enumerate(res.cargas, start=1):
        if c["conexion"] == "Y":
            van, vbn, vcn = _fasores_abc(c["v_fase"])
            ia, ib, ic = _fasores_abc(c["i_linea"])
            tabla.add_row(
                f"C{k} (Y)", "V_an/V_bn/V_cn [V]",
                _fmt_complejo(van), _fmt_complejo(vbn), _fmt_complejo(vcn))
            tabla.add_row(
                f"C{k} (Y)", "I_a/I_b/I_c [A]",
                _fmt_complejo(ia), _fmt_complejo(ib), _fmt_complejo(ic))
        else:  # Delta
            vab, vbc, vca = _fasores_abc(c["v_linea_fasor"])
            iab, ibc, ica = _fasores_abc(c["i_fase"])
            tabla.add_row(
                f"C{k} (D)", "V_ab/V_bc/V_ca [V]",
                _fmt_complejo(vab), _fmt_complejo(vbc), _fmt_complejo(vca))
            tabla.add_row(
                f"C{k} (D)", "I_ab/I_bc/I_ca [A]",
                _fmt_complejo(iab), _fmt_complejo(ibc), _fmt_complejo(ica))
    consola.print(tabla)


def _renderizar_panel_interpretativo(consola: Console, circuito, res,
                                     es_tri: bool, fuente_tipo: str) -> None:
    """Renderiza el panel explicativo con la interpretación técnica.

    Incluye:
      - La conversión línea/fase aplicada.
      - Diagnóstico del sistema según ``Q`` total.
      - Evaluación del factor de potencia global.
    """
    if not es_tri:
        return

    contenido = Text()

    # 1) Conversión línea/fase aplicada
    contenido.append("Conversión aplicada\n", style="bold underline")
    if fuente_tipo == "F":
        v_fase = circuito.v_linea / _sqrt3()
        contenido.append(
            "Se ingresó tensión de FASE. Se convirtió a línea con "
            f"[yellow]V_LL = sqrt(3)·V_LN = {circuito.v_linea:.4g} V[/] "
            f"(V_LN = {v_fase:.4g} V). "
            "El ángulo dado es el de la fase 'a'.\n"
        )
    else:
        v_fase = circuito.v_linea / _sqrt3()
        contenido.append(
            "Se ingresó tensión de LÍNEA. Se convirtió a fase con "
            f"[yellow]V_LN = V_LL/sqrt(3) = {v_fase:.4g} V[/] "
            f"(V_LL = {circuito.v_linea:.4g} V). "
            "El fasor de fase 'a' se obtuvo restando 30° al ángulo de línea "
            "(convención estándar).\n"
        )

    # 2) Diagnóstico del sistema
    contenido.append("\nDiagnóstico del sistema\n", style="bold underline")
    q = res.Q
    if abs(q) < 1e-6:
        diag = "RESISTIVO"
        color = "yellow"
        nota = "La potencia reactiva total es casi nula."
    elif q > 0:
        diag = "PREDOMINANTEMENTE INDUCTIVO"
        color = "red"
        nota = ("Q > 0: la carga consume reactiva (bobinas). "
                "Para mejorar el FP se compensaría con capacitores.")
    else:
        diag = "PREDOMINANTEMENTE CAPACITIVO"
        color = "cyan"
        nota = ("Q < 0: la carga entrega reactiva (capacitores). "
                "Sistema en adelanto.")
    contenido.append(f"{diag}\n", style=f"bold {color}")
    contenido.append(f"Q_total = {q / 1000:.4g} kVAR. {nota}\n")

    # 3) Evaluación del factor de potencia
    contenido.append("\nFactor de potencia global\n", style="bold underline")
    fp = res.fp
    fp_pct = fp * 100
    contenido.append(f"FP = {fp:.4g}  ({fp_pct:.1f}%)  ")
    if fp >= 0.95:
        contenido.append("[green]Excelente:[/] pérdidas y caídas por reactiva son mínimas.\n")
    elif fp >= 0.85:
        contenido.append("[yellow]Aceptable:[/] se podría mejorar con corrección si la instalación es grande.\n")
    else:
        contenido.append(
            "[red]Bajo:[/] se recomienda corrección del factor de potencia "
            "(banco de capacitores) para reducir corriente y pérdidas.\n"
        )

    consola.print(
        Panel(contenido, title="6. Interpretación técnica",
              border_style="bright_magenta", expand=True)
    )


def _bloque_inciso(consola, letra: str, titulo: str, formula: str,
                   sustitucion: str, resultado_rect, resultado_polar) -> None:
    """Renderiza un inciso académico en un panel rich independiente."""
    cuerpo = Text()
    cuerpo.append(f"Fórmula:  ", style="bold")
    cuerpo.append(formula, style="italic cyan")
    cuerpo.append("\n")
    cuerpo.append(f"Sustitución:  ", style="bold")
    cuerpo.append(sustitucion, style="yellow")
    cuerpo.append("\n")
    cuerpo.append(f"Resultado:  ", style="bold")
    cuerpo.append(resultado_rect, style="green")
    cuerpo.append(f"   =   {resultado_polar}", style="dim")
    consola.print(
        Panel(cuerpo, title=f"Inciso ({letra}) — {titulo}",
              border_style="blue", expand=True))


def _bloque_texto(consola, titulo: str, cuerpo: str, border="blue") -> None:
    """Renderiza un bloque de texto/interpretación en un panel rich."""
    consola.print(
        Panel(cuerpo, title=titulo, border_style=border, expand=True))


# Estado de sesión: último circuito resuelto (para comandos como graficar).
_ULTIMO_RESULTADO: dict | None = None


def _guardar_ultimo_resultado(circuito, res, es_tri, datos=None) -> None:
    """Guarda el último circuito resuelto para reutilizarlo después."""
    global _ULTIMO_RESULTADO
    _ULTIMO_RESULTADO = {
        "circuito": circuito, "res": res, "es_tri": es_tri, "datos": datos,
    }


def _ultimo_resultado(consola):
    """Devuelve el último resultado guardado o muestra un error si no hay."""
    if _ULTIMO_RESULTADO is None:
        consola.print(
            "[red]No hay resultado previo. Resuelva un circuito primero con "
            "'trifasico' o 'monofasico'.[/]")
        return None
    return _ULTIMO_RESULTADO


def _graficar_fasores(consola, etiquetas, fasores, titulo) -> None:
    """Prepara un diagrama fasorial sin abrir ventana emergente.

    Solo notifica que el diagrama quedó listo; el usuario lo visualiza con
    el comando ``graficar``/``fasores`` (evita bloquear la resolución).
    """
    try:
        from analizador.gui.viz import phasor_plot

        phasor_plot(fasores, etiquetas=etiquetas, titulo=titulo)
        consola.print(
            f"[dim]Diagrama '{titulo}' preparado. Use 'graficar' o 'fasores' "
            "para visualizarlo.[/]"
        )
        import matplotlib.pyplot as plt
        plt.close("all")
    except Exception as err:
        consola.print(f"[red]No se pudo preparar el diagrama: {err}[/]")


def _resolver_academico(consola, circuito, res, es_tri: bool, datos) -> None:
    """Desglose académico inciso por inciso (a)-(j) + análisis extendido.

    ``datos`` es el ``SimpleNamespace`` devuelto por ``_parse_red_args``
    (contiene ``carga_fp`` y ``fp_objetivo``).
    """
    consola.print(
        Panel("[bold]Resolución académica inciso por inciso[/]",
              title="Modo taller", border_style="bright_cyan", expand=True)
    )

    if es_tri:
        _incisos_trifasico(consola, circuito, res, datos)
    else:
        _incisos_monofasico(consola, circuito, res, datos)

    _analisis_extendido(consola, circuito, res, es_tri)


def _incisos_trifasico(consola, circuito, res, datos) -> None:
    """Incisos (a)-(j) para el sistema trifásico balanceado."""
    import numpy as np
    import math

    # (a) Corriente de la fuente
    i_l = res.i_linea
    _bloque_inciso(
        consola, "a", "Corriente de la fuente",
        "I_L = V_fuente / Z_total",
        f"V_fuente = {_fmt_complejo(res.v_fuente_fase)} ; "
        f"Z_total = {_fmt_complejo(res.z_total)}",
        _fmt_complejo(i_l), _fmt_polar(i_l),
    )

    # (b) Potencia compleja por valores de fase
    s3f_fase = res.s3f  # ya es 3*V_f*conj(I_f)
    _bloque_inciso(
        consola, "b", "Potencia compleja total (valores de fase)",
        "S_3f = 3 * V_f * conj(I_f)",
        f"3 * {_fmt_complejo(res.v_fuente_fase)} * conj({_fmt_complejo(i_l)})",
        _fmt_complejo(s3f_fase), _fmt_polar(s3f_fase),
    )

    # (c) Potencia compleja por valores de línea
    v_ll_fasor = res.v_fuente_linea
    s3f_linea = _potencia_3f_por_linea(v_ll_fasor, i_l)
    _bloque_inciso(
        consola, "c", "Potencia compleja total (valores de línea)",
        "S_3f = sqrt(3) * V_L * conj(I_L)",
        f"sqrt(3) * {_fmt_complejo(v_ll_fasor)} * conj({_fmt_complejo(i_l)})",
        _fmt_complejo(s3f_linea), _fmt_polar(s3f_linea),
    )

    # (d) Tensión de línea en el nodo de las cargas
    v_ll_carga = res.v_carga_linea
    _bloque_inciso(
        consola, "d", "Tensión de línea en el nodo de cargas",
        "V_LL_carga = |V_f_carga| * sqrt(3)",
        f"|{_fmt_complejo(res.v_carga)}| * sqrt(3)",
        f"{v_ll_carga:.4g} V", f"{v_ll_carga:.4g} V rms",
    )

    # (e) Fasorial de tensiones en Estrella (por carga, primeras en Y)
    van_etiquetas = []
    van_fasores = []
    for k, c in enumerate(res.cargas, start=1):
        if c["conexion"] == "Y":
            van, vbn, vcn = _fasores_abc(c["v_fase"])
            van_etiquetas += [f"C{k} Van", f"C{k} Vbn", f"C{k} Vcn"]
            van_fasores += [van, vbn, vcn]
            _bloque_inciso(
                consola, "e", f"Fasorial de tensiones Estrella — carga C{k}",
                "V_an = V_f ; V_bn = V_an/-120 ; V_cn = V_an/120",
                f"V_f = {_fmt_complejo(c['v_fase'])}",
                f"{_fmt_complejo(van)} | {_fmt_complejo(vbn)} | {_fmt_complejo(vcn)}",
                f"{_fmt_polar(van)} | {_fmt_polar(vbn)} | {_fmt_polar(vcn)}",
            )
    if van_fasores:
        _graficar_fasores(consola, van_etiquetas, van_fasores,
                          "Fasorial de tensiones (Estrella)")

    # (f) Corriente por fase de cada carga
    for k, c in enumerate(res.cargas, start=1):
        if c["conexion"] == "Y":
            formula = "I_f_Y = I_L"
            sustit = f"I_L = {_fmt_complejo(res.i_linea)}"
            etiq = "Y"
        else:
            formula = "I_f_Delta = I_L * exp(j30)/sqrt(3)"
            sustit = (f"I_L = {_fmt_complejo(res.i_linea)} ; "
                      f"sqrt(3) = {_sqrt3():.4g}")
            etiq = "Delta"
        _bloque_inciso(
            consola, "f", f"Corriente por fase — carga C{k} ({etiq})",
            formula, sustit,
            _fmt_complejo(c["i_fase"]), _fmt_polar(c["i_fase"]),
        )

    # (g) Corrientes de malla en Delta
    for k, c in enumerate(res.cargas, start=1):
        if c["conexion"] == "Delta":
            iab, ibc, ica = _fasores_abc(c["i_fase"])
            _bloque_inciso(
                consola, "g", f"Corrientes de malla Delta — carga C{k}",
                "I_ab ; I_bc = I_ab/-120 ; I_ca = I_ab/120",
                f"I_f = {_fmt_complejo(c['i_fase'])}",
                f"{_fmt_complejo(iab)} | {_fmt_complejo(ibc)} | {_fmt_complejo(ica)}",
                f"{_fmt_polar(iab)} | {_fmt_polar(ibc)} | {_fmt_polar(ica)}",
            )

    # (h) Coordenadas para diagrama fasorial de corrientes en Delta
    delta_etiquetas = []
    delta_fasores = []
    for k, c in enumerate(res.cargas, start=1):
        if c["conexion"] == "Delta":
            iab, ibc, ica = _fasores_abc(c["i_fase"])
            delta_etiquetas += [f"C{k} Iab", f"C{k} Ibc", f"C{k} Ica"]
            delta_fasores += [iab, ibc, ica]
            _bloque_inciso(
                consola, "h", f"Coordenadas fasoriales de corrientes Delta — carga C{k}",
                "I_ab ; I_bc ; I_ca",
                f"I_f = {_fmt_complejo(c['i_fase'])}",
                f"{_fmt_complejo(iab)} | {_fmt_complejo(ibc)} | {_fmt_complejo(ica)}",
                f"{_fmt_polar(iab)} | {_fmt_polar(ibc)} | {_fmt_polar(ica)}",
            )
    if delta_fasores:
        _graficar_fasores(consola, delta_etiquetas, delta_fasores,
                          "Fasorial de corrientes (Delta)")

    # (i) Desglose de P y Q por carga y línea
    cuerpo = Text()
    cuerpo.append("Cargas\n", style="bold underline")
    for k, c in enumerate(res.cargas, start=1):
        cuerpo.append(
            f"  C{k}: P = {c['P'] / 1000:.4g} kW ; "
            f"Q = {c['Q'] / 1000:.4g} kVAR\n")
    s_linea = res.s_linea
    cuerpo.append("\nLínea\n", style="bold underline")
    cuerpo.append(
        f"  P_perdidas = {s_linea.real / 1000:.4g} kW ; "
        f"Q_linea = {s_linea.imag / 1000:.4g} kVAR\n")
    cuerpo.append(
        f"\nTotal: P = {res.P / 1000:.4g} kW ; "
        f"Q = {res.Q / 1000:.4g} kVAR\n")
    if hasattr(res, "balance") and not res.balance.ok:
        cuerpo.append(
            f"\n[red]BALANCE: S_fuente = {_fmt_complejo(res.balance.S_fuente)} "
            f"vs S_consumida = {_fmt_complejo(res.balance.S_total)} "
            f"(err_rel = {res.balance.err_rel:.4g}).[/]")
    _bloque_texto(consola, "Inciso (i) — Desglose de potencia P y Q",
                  cuerpo)

    # (j) Corrección de factor de potencia
    _inciso_j_correccion_fp(consola, res, datos, es_tri=True)


def _inciso_j_correccion_fp(consola, res, datos, es_tri) -> None:
    """Inciso (j): kVAR requeridos y capacitancia por fase (µF)."""
    from analizador.modules.correccion_fp import (
        capacitor_reactance, capacitor_value, required_reactive_power)

    idx = datos.carga_fp - 1
    if idx < 0 or idx >= len(res.cargas):
        _bloque_texto(
            consola, "Inciso (j) — Corrección de factor de potencia",
            f"[red]Índice de carga {datos.carga_fp} fuera de rango "
            f"(1..{len(res.cargas)}).[/]")
        return
    c = res.cargas[idx]
    p_carga = c["P"]
    q_carga = c["Q"]
    fp_carga = c["fp"]
    fp_obj = datos.fp_objetivo

    comp = required_reactive_power(p_carga, fp_carga, fp_obj)
    if comp.Qc <= 1e-12:
        _bloque_texto(
            consola, "Inciso (j) — Corrección de factor de potencia",
            (f"Carga C{datos.carga_fp}: FP actual {fp_carga:.4g} ya es >= "
             f"objetivo {fp_obj:.4g}. No se requiere compensación "
             f"(Qc = {comp.Qc / 1000:.4g} kVAR)."))
        return

    # Tensión en bornes de la carga (fase). Mono usa "v", tri usa "v_fase".
    v_ln_carga = abs(c["v_fase"] if "v_fase" in c else c["v"])
    xc = capacitor_reactance(v_ln_carga, comp.Qc)
    cap = capacitor_value(60.0, xc.Xc)

    cuerpo = Text()
    cuerpo.append(f"Carga seleccionada: C{datos.carga_fp}\n", style="bold")
    cuerpo.append(f"  FP actual = {fp_carga:.4g} ; FP objetivo = {fp_obj:.4g}\n")
    cuerpo.append(
        f"  P = {p_carga / 1000:.4g} kW ; Q = {q_carga / 1000:.4g} kVAR\n")
    cuerpo.append(f"  phi1 = {comp.phi1_deg:.4g}° ; phi2 = {comp.phi2_deg:.4g}°\n")
    cuerpo.append(
        f"  Q1 = {comp.Q1 / 1000:.4g} kVAR ; Q2 = {comp.Q2 / 1000:.4g} kVAR\n")
    cuerpo.append(
        f"  [bold]Qc requerida = {comp.Qc / 1000:.4g} kVAR[/] (capacitiva)\n")
    cuerpo.append(
        f"  Tensión por fase (banco Y) V_LN = {v_ln_carga:.4g} V\n")
    cuerpo.append(f"  Xc = |V^2/Qc| = {xc.Xc:.4g} ohm\n")
    cuerpo.append(
        f"  [bold]C = 1/(2*pi*f*Xc) = {cap.C_uF:.4g} uF por fase[/] "
        f"({cap.C_F * 1e6:.4g} uF)")
    _bloque_texto(consola, "Inciso (j) — Corrección de factor de potencia",
                  cuerpo)


def _incisos_monofasico(consola, circuito, res, datos) -> None:
    """Incisos relevantes para el circuito monofásico."""
    import numpy as np

    i = res.i_linea
    _bloque_inciso(
        consola, "a", "Corriente de la fuente",
        "I = V / Z_total",
        f"V = {_fmt_complejo(res.v_fuente)} ; Z_total = {_fmt_complejo(res.z_total)}",
        _fmt_complejo(i), _fmt_polar(i),
    )
    s = res.s
    _bloque_inciso(
        consola, "b", "Potencia compleja total",
        "S = V * conj(I)",
        f"{_fmt_complejo(res.v_fuente)} * conj({_fmt_complejo(i)})",
        _fmt_complejo(s), _fmt_polar(s),
    )
    v_carga = abs(res.v_carga)
    _bloque_inciso(
        consola, "d", "Tensión en bornes de la carga",
        "V_carga = |V_carga|",
        f"|{_fmt_complejo(res.v_carga)}|",
        f"{v_carga:.4g} V", f"{v_carga:.4g} V rms",
    )

    cuerpo = Text()
    cuerpo.append("Cargas\n", style="bold underline")
    for k, c in enumerate(res.cargas, start=1):
        cuerpo.append(
            f"  C{k}: P = {c['P'] / 1000:.4g} kW ; "
            f"Q = {c['Q'] / 1000:.4g} kVAR\n")
    cuerpo.append("\nTotal:\n", style="bold underline")
    cuerpo.append(
        f"  P = {res.P / 1000:.4g} kW ; Q = {res.Q / 1000:.4g} kVAR")
    _bloque_texto(consola, "Inciso (i) — Desglose de potencia P y Q", cuerpo)

    _inciso_j_correccion_fp(consola, res, datos, es_tri=False)


def _analisis_extendido(consola, circuito, res, es_tri: bool) -> None:
    """Módulo de análisis extendido: Y_eq, pérdidas, eficiencia, RV, LKC."""
    import numpy as np

    cuerpo = Text()

    # 1) Admitancia equivalente
    try:
        y_eq, g, b = _admitancia_equivalente(res.z_eq)
        signo_b = "capacitiva" if b < 0 else "inductiva"
        cuerpo.append("Admitancia equivalente\n", style="bold underline")
        cuerpo.append(
            f"  Y_eq = 1/Z_eq = {_fmt_complejo(y_eq)} S\n")
        cuerpo.append(
            f"  G = {g:.4g} S ; B = {b:.4g} S "
            f"(B {'< 0' if b < 0 else '> 0'} -> parte "
            f"[yellow]{signo_b}[/])\n")
    except Exception as err:
        cuerpo.append(f"  Y_eq: {err}\n")

    # 2) Pérdidas en la línea
    s_linea = res.s_linea
    cuerpo.append("\nPérdidas en la línea\n", style="bold underline")
    cuerpo.append(
        f"  P_perdidas = {s_linea.real / 1000:.4g} kW ; "
        f"Q_linea = {s_linea.imag / 1000:.4g} kVAR\n")

    # 3) Eficiencia de transmisión
    p_cargas = sum(c["P"] for c in res.cargas)
    eta = _eficiencia(p_cargas, res.P)
    cuerpo.append("\nEficiencia de transmisión\n", style="bold underline")
    cuerpo.append(
        f"  eta = P_cargas / P_fuente * 100 = {eta:.4g} %\n")

    # 4) Regulación de voltaje en bornes
    if es_tri:
        v_carga = res.v_carga_linea
        v_fuente = res.v_linea
    else:
        v_carga = abs(res.v_carga)
        v_fuente = abs(res.v_fuente)
    rv = _regulacion_voltaje(v_carga, v_fuente)
    cuerpo.append("\nRegulación de voltaje\n", style="bold underline")
    cuerpo.append(
        f"  RV% = (V_sin_carga - V_plena)/V_plena * 100 = {rv:.4g} %\n")

    # 5) Verificación LKC en el nodo
    cuerpo.append("\nVerificación LKC en el nodo\n", style="bold underline")
    if es_tri:
        suma = sum(c["i_linea"] for c in res.cargas)
        cuerpo.append(
            f"  Sum(I_f_Y + I_L_Delta) = {_fmt_complejo(suma)}\n")
        cuerpo.append(f"  I_linea = {_fmt_complejo(res.i_linea)}\n")
        diff = abs(suma - res.i_linea)
        cuerpo.append(
            f"  Diferencia = {diff:.4g} A "
            f"({'[green]OK' if diff < 1e-6 else '[red]NO coincide'}[/])\n")
    else:
        suma = sum(c["i"] for c in res.cargas)
        cuerpo.append(f"  Sum(I_ramas) = {_fmt_complejo(suma)}\n")
        cuerpo.append(f"  I_total = {_fmt_complejo(res.i_linea)}\n")
        diff = abs(suma - res.i_linea)
        cuerpo.append(
            f"  Diferencia = {diff:.4g} A "
            f"({'[green]OK' if diff < 1e-6 else '[red]NO coincide'}[/])\n")

    # 6) Balance de potencia (sanity check de conservación)
    cuerpo.append("\nBalance de potencia\n", style="bold underline")
    bal = res.balance
    cuerpo.append(
        f"  S_fuente    = {_fmt_complejo(bal.S_fuente)}\n")
    cuerpo.append(
        f"  S_consumida = {_fmt_complejo(bal.S_total)}\n")
    cuerpo.append(
        f"  err_P = {bal.err_P:.4g} W ;  err_Q = {bal.err_Q:.4g} var ;  "
        f"err_rel = {bal.err_rel:.4g}\n")
    cuerpo.append(
        f"  Estado: "
        f"{'[green]OK (conservacion cumplida)' if bal.ok else '[red]DESBALANCE'}[/]\n")

    consola.print(
        Panel(cuerpo, title="Análisis extendido", border_style="green",
              expand=True))


def _fmt_polar(z) -> str:
    """Formato polar ``M[ángulo]`` para un fasor."""
    return f"{abs(z):.4g}[{_angulo_grados(z):.4g}]"


# ---------------------------------------------------------------------------
# Presentación de resultados (panel estructurado e interpretativo)
# ---------------------------------------------------------------------------
def _campos_planos(result) -> list[tuple[str, object]]:
    """Devuelve los campos escalares (no estructuras) de un contrato."""
    from analizador.utils import _ETIQUETAS

    campos = []
    for nombre in getattr(result, "__dict__", {}):
        if nombre == "meta":
            continue
        valor = getattr(result, nombre)
        if isinstance(valor, (str, bool)):
            continue
        if hasattr(valor, "__dict__") or isinstance(valor, (list, tuple, dict)):
            continue
        campos.append((nombre, valor))
    return campos


def _etiqueta_campo(nombre: str) -> str:
    from analizador.utils import _ETIQUETAS

    return _ETIQUETAS.get(nombre, nombre)


def _mostrar_resultado(consola: Console, result, datos_entrada=None) -> None:
    """Presenta un contrato de servicios en un panel estructurado."""
    from analizador.utils import format_complex

    if isinstance(result, dict) and "codigo" in result:
        consola.print(
            Panel(
                f"[bold red]{result['mensaje']}[/]",
                title="Error",
                border_style="red",
            )
        )
        return

    meta = getattr(result, "meta", None)
    tema = getattr(meta, "tema", None) or type(result).__name__
    unidades = getattr(meta, "unidades", None)
    formulas = getattr(meta, "formulas", None)
    advertencias = getattr(meta, "advertencias", None)

    contenido = Text()

    # 1) Tema
    contenido.append("Tema: ", style="bold")
    contenido.append(tema, style="bold cyan")
    contenido.append("\n\n")

    # 2) Datos de entrada
    if datos_entrada:
        contenido.append("Datos de entrada\n", style="bold underline")
        for nombre, valor in datos_entrada:
            contenido.append(f"  • {nombre} = ")
            contenido.append(str(valor), style="yellow")
            contenido.append("\n")
        contenido.append("\n")

    # 3) Resultados con unidades
    contenido.append("Resultados\n", style="bold underline")
    campos = _campos_planos(result)
    if not campos:
        contenido.append("  (sin campos escalares)\n")
    for nombre, valor in campos:
        etiqueta = _etiqueta_campo(nombre)
        unidad = ""
        if unidades is not None and hasattr(unidades, nombre):
            unidad = getattr(unidades, nombre)
        contenido.append(f"  • {etiqueta}")
        if unidad:
            contenido.append(f"  [{unidad}]", style="dim")
        contenido.append(" = ")
        if isinstance(valor, complex):
            rect, polar = format_complex(valor)
            contenido.append(rect, style="green")
            contenido.append(f"  ({polar})", style="dim")
        else:
            contenido.append(f"{valor:g}", style="green")
        contenido.append("\n")

    # 4) Procedimiento / fórmulas
    if formulas:
        contenido.append("\nProcedimiento\n", style="bold underline")
        for k, f in enumerate(formulas, start=1):
            contenido.append(f"  {k}. ")
            contenido.append(str(f), style="dim")
            contenido.append("\n")

    # 5) Nota técnica interpretativa
    nota = _NOTAS.get(tema, None) or _NOTAS.get(_clave_tema(tema), None)
    if nota:
        contenido.append("\nNota\n", style="bold underline")
        contenido.append(nota, style="italic magenta")
        contenido.append("\n")

    if advertencias:
        contenido.append("\nAdvertencias\n", style="bold underline")
        for adv in advertencias:
            contenido.append(f"  • {adv}", style="yellow")
            contenido.append("\n")

    consola.print(Panel(contenido, title="Resultado", border_style="green"))


def _clave_tema(tema: str) -> str | None:
    """Mapea un tema textual a una clave de ``_NOTAS`` (aproximada)."""
    tema_l = tema.lower()
    if "potencia" in tema_l and "trifas" not in tema_l:
        return "potenciaCompleja"
    if "factor de potencia" in tema_l:
        return "correccionFP"
    if "flujo" in tema_l:
        return "flujoPotencia"
    if "por unidad" in tema_l:
        return "perUnit"
    if "trifas" in tema_l:
        return "sistemasTrifasicos"
    return None


# ---------------------------------------------------------------------------
# Comandos de cálculo (asistidos y didacticos)
# ---------------------------------------------------------------------------
def _cmd_potencia(consola: Console) -> None:
    """Potencia compleja: elige flujo y pide parámetros guiados."""
    flujo = _pedir_seleccion(
        consola,
        "Flujo de calculo de potencia",
        {
            "VI": ("VI (V e I)", "desde tension y corriente"),
            "VZ": ("VZ (V y Z)", "desde tension e impedancia"),
            "PF": ("PF (P, FP y tipo)", "desde potencia activa y factor de potencia"),
        },
        default="PF",
        sinonimos={
            "voltaje": "VI", "tension": "VI", "corriente": "VI",
            "impedancia": "VZ",
            "potencia": "PF", "fp": "PF", "factor": "PF",
        },
    )
    if flujo is None:
        return

    if flujo == "VI":
        v = _pedir_complejo(
            consola, "Tension V", "Tension aplicada a la carga.", "V", "200"
        )
        i = _pedir_complejo(
            consola, "Corriente I", "Corriente que circula por la carga.", "A", "4-8j"
        )
        if v is None or i is None:
            return
        res = _service("service_analizar_carga", "VI", v, i)
        datos = [("V", v), ("I", i)]
    elif flujo == "VZ":
        v = _pedir_complejo(
            consola, "Tension V", "Tension aplicada a la carga.", "V", "200"
        )
        r = _pedir_numero(
            consola, "R", "Resistencia de la impedancia.", "ohm", "10"
        )
        x = _pedir_numero(
            consola, "X", "Reactancia de la impedancia.", "ohm", "20"
        )
        if v is None or r is None or x is None:
            return
        z_entrada = r + 1j * x
        res = _service("service_analizar_carga", "VZ", v, z_entrada)
        datos = [("V", v), ("Z", f"{z_entrada} ohm")]
    else:
        p = _pedir_numero(
            consola, "P", "Potencia activa consumida por la carga.", "W",
            "250000",
        )
        fp = _pedir_numero(
            consola, "FP", "Factor de potencia de la carga.", "0 a 1", "0.9",
            rango=(0.0, 1.0),
        )
        tipo = _pedir_seleccion(
            consola,
            "Tipo de carga",
            {
                "inductiva": ("Inductiva", "FP en atraso (Q > 0)"),
                "capacitiva": ("Capacitiva", "FP en adelanto (Q < 0)"),
                "resistiva": ("Resistiva", "FP unitario (Q = 0)"),
            },
            default="inductiva",
            sinonimos={
                "inductivo": "inductiva", "atraso": "inductiva",
                "capacitivo": "capacitiva", "adelanto": "capacitiva",
                "resistivo": "resistiva",
            },
        )
        if p is None or fp is None or tipo is None:
            return
        res = _service("service_analizar_carga", "PF", p, fp, tipo)
        datos = [("P", f"{p} W"), ("FP", fp), ("tipo", tipo)]

    _mostrar_resultado(consola, res, datos)


def _cmd_correccion(consola: Console) -> None:
    """Corrección de factor de potencia (asistido)."""
    p = _pedir_numero(
        consola, "P", "Potencia activa de la instalacion.", "W", "1200"
    )
    fp1 = _pedir_numero(
        consola, "FP inicial", "Factor de potencia actual (entre 0 y 1).",
        "0 a 1", "0.6", rango=(0.0, 1.0),
    )
    fp2 = _pedir_numero(
        consola, "FP objetivo", "Factor de potencia deseado (entre 0 y 1).",
        "0 a 1", "0.9", rango=(0.0, 1.0),
    )
    v = _pedir_numero(
        consola, "V", "Tension de operacion.", "V", "200"
    )
    f = _pedir_numero(
        consola, "f", "Frecuencia de la red.", "Hz", "60"
    )
    if None in (p, fp1, fp2, v, f):
        return
    r = _service("service_corregir_fp", p, fp1, fp2, v, f)
    _mostrar_resultado(
        consola, r,
        [("P", f"{p} W"), ("FP inicial", fp1), ("FP objetivo", fp2),
         ("V", f"{v} V"), ("f", f"{f} Hz")],
    )


def _cmd_per_unit(consola: Console) -> None:
    """Sistema por unidad (asistido)."""
    sbase = _pedir_numero(
        consola, "Sbase", "Potencia base del sistema.", "VA", "100e6"
    )
    vbase = _pedir_numero(
        consola, "Vbase", "Tension base del sistema.", "V", "13.8e3"
    )
    fases = _pedir_seleccion(
        consola,
        "Tipo de sistema",
        {"trifasico": ("Trifasico", "3 fases"), "monofasico": ("Monofasico", "1 fase")},
        default="trifasico",
        sinonimos={"3f": "trifasico", "tri": "trifasico",
                   "1f": "monofasico", "mono": "monofasico"},
    )
    valor = _pedir_numero(
        consola, "Valor real", "Magnitud que se quiere convertir a p.u.", "varia", "13.8e3"
    )
    tipo = _pedir_seleccion(
        consola,
        "Tipo de magnitud",
        {"V": ("V", "tension"), "I": ("I", "corriente"),
         "S": ("S", "potencia"), "Z": ("Z", "impedancia")},
        default="V",
        sinonimos={"tension": "V", "voltaje": "V", "corriente": "I",
                   "potencia": "S", "impedancia": "Z"},
    )
    if None in (sbase, vbase, fases, valor, tipo):
        return
    r = _service("service_per_unit", sbase, vbase, fases, valor, tipo)
    _mostrar_resultado(
        consola, r,
        [("Sbase", f"{sbase} VA"), ("Vbase", f"{vbase} V"), ("fases", fases),
         ("valor", valor), ("tipo", tipo)],
    )


def _cmd_trifasico(consola: Console, args: list[str] | None = None) -> None:
    """Carga trifásica balanceada: modo CLI (con argumentos) o asistido."""
    if args:
        _cmd_trifasico_cli(consola, args)
        return
    vl = _pedir_numero(
        consola, "VL", "Tension de linea de la fuente.", "V", "208"
    )
    conexion = _pedir_seleccion(
        consola,
        "Conexion de la carga",
        {"Y": ("Estrella (Y)", "V_f = VL/sqrt(3)"), "Delta": ("Delta", "V_f = VL")},
        default="Y",
        sinonimos={"estrella": "Y", "wye": "Y"},
    )
    r = _pedir_numero(
        consola, "R", "Resistencia por fase.", "ohm", "24"
    )
    x = _pedir_numero(
        consola, "X", "Reactancia por fase.", "ohm", "0"
    )
    if None in (vl, conexion, r, x):
        return
    res = _service("service_trifasico_carga", vl, conexion, r + 1j * x)
    _mostrar_resultado(
        consola, res,
        [("VL", f"{vl} V"), ("Conexion", conexion), ("Z_fase", f"{r + 1j * x} ohm")],
    )


def _cmd_trifasico_cli(consola: Console, args: list[str]) -> None:
    """Resuelve una red trifásica balanceada con varias cargas y líneas."""
    from analizador.core.circuito import CircuitoTrifasico

    try:
        datos = _parse_red_args(args)
    except ValueError as err:
        _mostrar_error_args(consola, err)
        return

    if datos.fuente is None:
        _mostrar_error_args(consola, ValueError(
            "falta --fuente <V> (tension de linea de la fuente)"))
        return
    if not datos.cargas:
        _mostrar_error_args(consola, ValueError(
            "falta --cargas. Ej.: --cargas Y:4+j2 D:5-j4"))
        return

    circuito = CircuitoTrifasico()
    info_fuente = _aplicar_fuente(circuito, datos.fuente, datos.fuente_tipo)
    if datos.lineas:
        circuito.set_linea(sum(datos.lineas))
    for tipo, z in datos.cargas:
        circuito.agregar_carga(tipo, z)
    res = circuito.resolver()
    _guardar_ultimo_resultado(circuito, res, True, datos)
    _renderizar_red(consola, circuito, res, "trifasico",
                    fuente_tipo=info_fuente["tipo"])
    if datos.taller:
        _resolver_academico(consola, circuito, res, es_tri=True, datos=datos)


def _cmd_monofasico(consola: Console, args: list[str] | None = None) -> None:
    """Circuito monofásico: modo CLI (con argumentos) o asistido."""
    if args:
        _cmd_monofasico_cli(consola, args)
        return
    v = _pedir_numero(
        consola, "V", "Tension de la fuente.", "V", "120"
    )
    r = _pedir_numero(
        consola, "R", "Resistencia por fase.", "ohm", "24"
    )
    x = _pedir_numero(
        consola, "X", "Reactancia por fase.", "ohm", "0"
    )
    if None in (v, r, x):
        return
    res = _service("service_analizar_carga", "VZ", v, r + 1j * x)
    _mostrar_resultado(
        consola, res,
        [("V", f"{v} V"), ("Z", f"{r + 1j * x} ohm")],
    )


def _cmd_monofasico_cli(consola: Console, args: list[str]) -> None:
    """Resuelve un circuito monofásico con varias cargas y líneas."""
    from analizador.core.circuito import CircuitoMonofasico

    try:
        datos = _parse_red_args(args)
    except ValueError as err:
        _mostrar_error_args(consola, err)
        return

    if datos.fuente is None:
        _mostrar_error_args(consola, ValueError(
            "falta --fuente <V> (tension de la fuente)"))
        return
    if not datos.cargas:
        _mostrar_error_args(consola, ValueError(
            "falta --cargas. Ej.: --cargas 4+j2 5-j4"))
        return

    circuito = CircuitoMonofasico()
    circuito.set_fuente(abs(datos.fuente), 0.0)
    if datos.lineas:
        circuito.set_linea(sum(datos.lineas))
    for _, z in datos.cargas:
        circuito.agregar_carga(z)
    res = circuito.resolver()
    _guardar_ultimo_resultado(circuito, res, False, datos)
    _renderizar_red(consola, circuito, res, "monofasico")
    if datos.taller:
        _resolver_academico(consola, circuito, res, es_tri=False, datos=datos)


def _cmd_graficar(consola: Console, args: list[str]) -> None:
    """Visualiza los fasores (y opcionalmente el triángulo de potencias) del
    último circuito resuelto con 'trifasico' o 'monofasico'.

    Banderas:
      --tensiones      Solo el panel de fasores de tensión.
      --corrientes     Solo el panel de fasores de corriente.
      --potencia       Triángulo de potencias (P, Q, S).
      --guardar <ruta> Exporta la figura (PNG/PDF/SVG) sin abrir ventana.
    Sin banderas: dos subplots paralelos (tensiones y corrientes).
    """
    estado = _ultimo_resultado(consola)
    if estado is None:
        return

    import matplotlib.pyplot as plt
    from analizador.gui.viz import (
        phasor_plot, plot_current_phasors, plot_voltage_phasors,
        power_triangle)

    solo_tensiones = "--tensiones" in args
    solo_corrientes = "--corrientes" in args
    con_potencia = "--potencia" in args
    ruta = None
    if "--guardar" in args:
        i = args.index("--guardar")
        if i + 1 >= len(args):
            consola.print("[red]--guardar requiere una ruta de archivo.[/]")
            return
        ruta = args[i + 1]

    res = estado["res"]
    es_tri = estado["es_tri"]

    if con_potencia:
        fig, ax = plt.subplots()
        power_triangle(res.P, res.Q, titulo="Triangulo de potencias")
        plt.sca(ax)
    elif es_tri:
        if solo_tensiones:
            fig, ax = plot_voltage_phasors(res)
        elif solo_corrientes:
            fig, ax = plot_current_phasors(res)
        else:
            fig, (ax_v, ax_i) = plt.subplots(1, 2, subplot_kw={
                "projection": "polar"})
            fig.suptitle("Fasores del sistema trifásico")
            plot_voltage_phasors(res, ax=ax_v)
            plot_current_phasors(res, ax=ax_i)
    else:
        # Monofásico: V_fuente, I_linea, V_carga.
        fasores = [res.v_fuente, res.i_linea, res.v_carga]
        etiquetas = ["V_fuente", "I_linea", "V_carga"]
        fig, ax = phasor_plot(fasores, etiquetas=etiquetas,
                              titulo="Fasores - circuito monofásico")

    if ruta:
        try:
            fig.savefig(ruta, dpi=150, bbox_inches="tight")
            consola.print(
                f"[green]Figura exportada a:[/] {ruta}")
        except Exception as err:
            consola.print(f"[red]No se pudo guardar la figura: {err}[/]")
        finally:
            plt.close(fig)
        return

    try:
        plt.show()
        consola.print("[green]Diagrama generado correctamente.[/]")
    except Exception as err:
        consola.print(f"[red]No se pudo mostrar la figura: {err}[/]")


def _mostrar_error_args(consola: Console, err: Exception) -> None:
    """Muestra un panel de error para la sintaxis de los argumentos CLI."""
    consola.print(
        Panel(
            f"[bold red]{err}[/]\n\n"
            "Sintaxis:\n"
            "  trifasico  --fuente [L|F]:<V> --cargas <Y|D>:<Z>... "
            "[--linea <Z> | --lineas <Z>...]\n"
            "  monofasico --fuente <V> --cargas <Z>... "
            "[--linea <Z> | --lineas <Z>...]\n"
            "  L = tension de linea (V_LL), F = tension de fase (V_LN). "
            "Sin prefijo se asume L.\n"
            "  Z acepta rectangular 'a+jb' o polar 'M[angulo]'.\n"
            "  Ej: trifasico --fuente L:208[30] --cargas Y:4+j2 D:5-j4 --linea 8+j4",
            title="Argumentos invalidos",
            border_style="red",
        )
    )


def _cmd_flujo(consola: Console) -> None:
    """Flujo de potencia entre dos fuentes (asistido)."""
    v1 = _pedir_numero(
        consola, "V1", "Magnitud de la tension de la fuente 1.", "V", "480"
    )
    d1 = _pedir_numero(
        consola, "delta1", "Angulo de fase de la fuente 1.", "deg", "0"
    )
    v2 = _pedir_numero(
        consola, "V2", "Magnitud de la tension de la fuente 2.", "V", "480"
    )
    d2 = _pedir_numero(
        consola, "delta2", "Angulo de fase de la fuente 2.", "deg", "10"
    )
    r = _pedir_numero(
        consola, "R", "Resistencia de la linea.", "ohm", "1"
    )
    x = _pedir_numero(
        consola, "X", "Reactancia de la linea.", "ohm", "2"
    )
    if None in (v1, d1, v2, d2, r, x):
        return
    res = _service("service_flujo_dos_fuentes", v1, d1, v2, d2, r + 1j * x)
    _mostrar_resultado(
        consola, res,
        [("V1", f"{v1} V"), ("delta1", f"{d1} deg"), ("V2", f"{v2} V"),
         ("delta2", f"{d2} deg"), ("Zline", f"{r + 1j * x} ohm")],
    )


# ---------------------------------------------------------------------------
# Comandos de navegación e integración
# ---------------------------------------------------------------------------
def _cmd_legacy(consola: Console) -> None:
    from analizador.cli.legacy_menu import lanzar_legacy

    lanzar_legacy()


def _cmd_gui(consola: Console) -> None:
    consola.print("[dim]Lanzando la interfaz grafica...[/]")
    try:
        from analizador.gui.app import main as _gui_main

        _gui_main()
    except Exception as err:
        consola.print(f"[bold red]No se pudo abrir la GUI:[/] {err}")


def _cmd_circuito(consola: Console) -> None:
    consola.print(
        "\n[bold cyan]Consola de circuitos.[/] "
        "[dim]Escriba 'salir' para volver a la consola SPT.[/]"
    )
    try:
        from analizador.services.asistente import consola as _consola_circuito

        _consola_circuito()
    except Exception as err:
        consola.print(f"[bold red]Error en la consola de circuitos:[/] {err}")


def _cmd_taller(consola: Console) -> None:
    try:
        from analizador.core.exercises import menu_ejercicios

        menu_ejercicios()
    except Exception as err:
        consola.print(f"[bold red]Error en los ejercicios:[/] {err}")


def _cmd_modulos(consola: Console) -> None:
    tabla = Table(title="Módulos temáticos", border_style="blue")
    tabla.add_column("Comando", style="cyan")
    tabla.add_column("Tema")
    for comando, tema in (
        ("potencia", "Potencia compleja"),
        ("correccion", "Corrección de factor de potencia"),
        ("flujo", "Flujo de potencia entre dos fuentes"),
        ("trifasico", "Sistemas trifásicos balanceados"),
        ("per-unit", "Sistema por unidad"),
        ("circuito", "Consola de circuitos (mono/tri)"),
        ("taller", "Ejercicios del Taller 2026"),
    ):
        tabla.add_row(comando, tema)
    consola.print(tabla)


def _cmd_version(consola: Console) -> None:
    consola.print(f"[bold cyan]SPT[/] versión [yellow]{__version__}[/]")


def _cmd_banner(consola: Console) -> None:
    mostrar_banner(consola)


def _cmd_clc(consola: Console) -> None:
    """Limpia por completo el contenido de la terminal."""
    consola.clear()


def _cmd_gramatica(consola: Console, tokens: list[str]) -> None:
    """Procesa una instrucción por la gramática de tres niveles.

    Entra en el contexto del sistema (pila de navegación) y confirma de
    forma educativa la instrucción interpretada.
    """
    from analizador.cli.gramatica import analizar_instruccion

    try:
        inst = analizar_instruccion(tokens)
    except Exception as err:
        from analizador.cli.gramatica import ErrorSintactico

        if isinstance(err, ErrorSintactico):
            _mostrar_error_sintactico(consola, err)
        else:
            _mostrar_error_sintactico(
                consola,
                ErrorSintactico(str(err), sugerencia="Revise la instruccion."),
            )
        return

    # entrar en el contexto del sistema para habilitar el escape
    _nav_entrar(inst.sistema)

    resumen = Table(
        title=f"Instruccion '{inst.sistema} {inst.componente}' interpretada",
        border_style="cyan", box=None)
    resumen.add_column("Nivel", style="bold")
    resumen.add_column("Valor", style="green")
    resumen.add_row("1. Sistema", inst.sistema)
    resumen.add_row("2. Componente", inst.componente)
    for flag, valor in inst.parametros.items():
        resumen.add_row(f"3. {flag}", str(valor))
    consola.print(resumen)
    consola.print(
        "\n[dim]Contexto activo: "
        f"[bold cyan]{_prompt_actual()}[/]. "
        "Escriba 'volver', 'salir' o 'exit' para regresar al prompt "
        "principal.[/]"
    )


# ---------------------------------------------------------------------------
# Ayuda y despachador
# ---------------------------------------------------------------------------
def _cmd_help(consola: Console) -> None:
    tabla = Table(title="Comandos disponibles", border_style="blue")
    tabla.add_column("Comando", style="bold cyan")
    tabla.add_column("Descripción")
    for comando, desc, _ in _COMANDOS:
        tabla.add_row(comando, desc)
    consola.print(tabla)
    consola.print(
        "\n[dim]Los comandos de calculo son asistidos: le pediran cada "
        "parametro paso a paso.[/]"
    )
    consola.print(
        "\n[dim]'trifasico' y 'monofasico' aceptan tambien argumentos CLI:[/]\n"
        "  [cyan]trifasico --fuente L:208[30] --cargas Y:4+j2 D:5-j4 --linea 8+j4[/]\n"
        "  [cyan]monofasico --fuente 120 --cargas 4+j2 5-j4 --lineas 8+j4 2+j1[/]\n"
        "  [dim]L = tension de linea (defecto), F = tension de fase. "
        "Banderas autocompletadas: --fuente --cargas --linea --lineas "
        "--paralelo[/]\n"
    )
    consola.print(
        "\n[bold]Gramatica por niveles[/] (sistema -> componente -> banderas):\n"
        "  [cyan]trifasico fuente --conexion estrella --v-rms 208[/]\n"
        "  [cyan]trifasico carga --potencia-activa 1200 --factor-potencia 0.9 "
        "--tipo inductivo[/]\n"
        "  [cyan]monofasico linea --z 8+j4[/]\n"
    )
    consola.print(
        "\n[bold]Navegacion:[/] escriba [cyan]volver[/], [cyan]salir[/] o "
        "[cyan]exit[/] para cancelar el contexto actual y volver al prompt "
        "principal."
    )


def _mostrar_error_comando(consola: Console, texto: str, sugerencia: str | None) -> None:
    """Muestra un panel de error amigable para un comando desconocido."""
    if sugerencia:
        consola.print(
            Panel(
                f"No reconozco '[bold]{texto}[/]'. "
                f"\n\n[bold yellow]¿Quisiste decir '{sugerencia}'?[/]\n"
                "\nEscriba '[bold cyan]help[/]' para ver la lista completa.",
                title="Comando no reconocido",
                border_style="yellow",
            )
        )
    else:
        consola.print(
            Panel(
                f"No reconozco '[bold]{texto}[/]'. No hay ningun comando "
                "parecido.\n\nEscriba '[bold cyan]help[/]' para ver la lista "
                "de comandos disponibles.",
                title="Comando no reconocido",
                border_style="yellow",
            )
        )


def _mostrar_error_sintactico(consola: Console, err) -> None:
    """Muestra un error sintáctico educativo en un panel rich.

    ``err`` es una :class:`analizador.cli.gramatica.ErrorSintactico`.
    """
    lineas = [f"[bold red]{err.mensaje}[/]"]
    if err.sugerencia:
        lineas.append(f"\n[bold]Sugerencia:[/] {err.sugerencia}")
    if err.opciones_validas:
        lineas.append(
            f"\n[bold]Opciones validas:[/] "
            f"[cyan]{' | '.join(err.opciones_validas)}[/]"
        )
    if err.ejemplos:
        lineas.append(
            f"\n[bold]Ejemplos:[/] "
            + "\n".join(f"  [yellow]{e}[/]" for e in err.ejemplos)
        )
    consola.print(
        Panel(
            "\n".join(lineas),
            title="[ERROR SINTACTICO]",
            border_style="red",
        )
    )


def _aliases_comandos() -> list[str]:
    """Devuelve todos los alias de comandos validos."""
    aliases = []
    for comando, _, _ in _COMANDOS:
        aliases.extend(a.strip() for a in comando.replace(",", " ").split())
    return aliases


_COMANDOS: list[tuple[str, str, functools.partial]] = [
    ("banner, intro", "Vuelve a mostrar el banner de bienvenida.",
     functools.partial(_cmd_banner)),
    ("help, ?", "Muestra esta ayuda con la lista de comandos.",
     functools.partial(_cmd_help)),
    ("menu, legacy", "Abre el menu clasico navegable.", functools.partial(_cmd_legacy)),
    ("gui", "Abre la interfaz grafica (Tkinter/CustomTkinter).",
     functools.partial(_cmd_gui)),
    ("circuito, consola", "Entra a la consola de circuitos (mono/tri).",
     functools.partial(_cmd_circuito)),
    ("taller, ejercicios", "Ejecuta los ejercicios del Taller 2026.",
     functools.partial(_cmd_taller)),
    ("potencia", "Calcula potencia compleja (asistido).",
     functools.partial(_cmd_potencia)),
    ("correccion", "Corrige el factor de potencia (asistido).",
     functools.partial(_cmd_correccion)),
    ("flujo", "Flujo de potencia entre dos fuentes (asistido).",
     functools.partial(_cmd_flujo)),
    ("trifasico, tri, 3f", "Red trifasica balanceada: --fuente --cargas --linea, o asistido.",
     functools.partial(_cmd_trifasico)),
    ("monofasico, mono, 1f", "Red monofasica: --fuente --cargas --linea, o asistido.",
     functools.partial(_cmd_monofasico)),
    ("per-unit", "Convierte al sistema por unidad (asistido).",
     functools.partial(_cmd_per_unit)),
    ("graficar, fasores, plot", "Visualiza fasores del ultimo circuito resuelto.",
     functools.partial(_cmd_graficar)),
    ("modulos", "Lista los modulos tematicos disponibles.",
     functools.partial(_cmd_modulos)),
    ("version", "Muestra la version del proyecto.", functools.partial(_cmd_version)),
    ("clc, cls", "Limpia la pantalla de la terminal.",
     functools.partial(_cmd_clc)),
    ("salir, exit, quit, 0", "Sale de la consola.", None),
]


def _service(nombre: str, *args):
    """Invoca una fachada de servicios de forma dinámica."""
    import analizador.services as _services

    fn = getattr(_services, nombre)
    return fn(*args)


# ---------------------------------------------------------------------------
# Autocompletado (prompt_toolkit)
# ---------------------------------------------------------------------------
class _ComandoCompleter(Completer):
    """Autocompleta los comandos conocidos de la consola."""

    def __init__(self, palabras: list[str]):
        self._palabras = palabras

    def get_completions(self, document, complete_event):
        palabra = document.get_word_before_cursor()
        for cmd in self._palabras:
            if cmd.startswith(palabra):
                yield Completion(cmd, start_position=-len(palabra))


# Banderas con doble guion sugeridas en el autocompletado para los comandos
# de red (trifasico / monofasico) y de visualización (graficar / fasores).
_BANDERAS = ("--fuente", "--cargas", "--linea", "--lineas", "--paralelo",
             "--taller", "--carga-fp", "--fp",
             "--tensiones", "--corrientes", "--potencia", "--guardar")


def _palabras_comandos() -> list[str]:
    """Devuelve las palabras individuales de todos los comandos y banderas."""
    palabras: set[str] = set()
    for comando, _, _ in _COMANDOS:
        for parte in comando.replace(",", " ").split():
            palabras.add(parte.strip())
    for bandera in _BANDERAS:
        palabras.add(bandera)
    return sorted(palabras)


# ---------------------------------------------------------------------------
# Bucle REPL
# ---------------------------------------------------------------------------
# Pila de navegación de contextos. Cada elemento es el nombre de un contexto
# (p.ej. 'trifasico', 'monofasico', 'ayuda'). Vacia = prompt principal.
_NAV: list[str] = []

# Palabras de escape que cancelan el contexto actual y vuelven al prompt
# principal (o salen de la aplicación si la pila está vacía).
_ESCAPE = ("exit", "salir", "volver", "q", "0")


def _nav_reset() -> None:
    """Limpia por completo la pila de navegación (vuelve a la raíz)."""
    _NAV.clear()


def _nav_entrar(contexto: str) -> None:
    """Entra en un contexto (lo apila)."""
    _NAV.append(contexto)


def _nav_salir() -> bool:
    """Saca un contexto de la pila. Regresa ``True`` si quedaba contexto."""
    if _NAV:
        _NAV.pop()
        return True
    return False


def _prompt_actual() -> str:
    """Devuelve el prompt según el contexto actual de la pila."""
    if _NAV:
        return "SEP/" + "/".join(_NAV) + "> "
    return "SEP> "
def _ejecutar(consola: Console, linea: str) -> bool:
    """Procesa una línea de comando. Regresa ``False`` si hay que salir.

    Reglas de navegación:
      - ``exit``/``salir``/``volver``/``q``/``0`` en un contexto (pila no
        vacía) saca el contexto actual y vuelve al prompt principal.
      - El mismo comando en la raíz sale de la aplicación.
    """
    texto_original = linea.strip()
    texto = texto_original.lower()
    if not texto:
        return True

    partes = texto.split()
    cmd = partes[0]
    args = partes[1:]

    # Palabras de escape: contexto vs raiz.
    if cmd in _ESCAPE:
        if _nav_salir():
            consola.print(
                f"[dim]Saliendo del contexto. Volviendo a [bold]{_prompt_actual()}[/][/]"
            )
            return True
        return False

    # Comandos de sistema (Nivel 1): gramática o sintaxis CLI legada.
    from analizador.cli.gramatica import SISTEMAS, es_instruccion_cli

    if cmd in SISTEMAS:
        if es_instruccion_cli(partes):
            # Sintaxis CLI legada (trifasico --fuente ... --cargas ...).
            if cmd in ("trifasico",):
                _cmd_trifasico(consola, args)
            else:
                _cmd_monofasico(consola, args)
        else:
            # Nueva gramática de tres niveles.
            _cmd_gramatica(consola, partes)
        return True

    # Despacho de comandos normales (navegación / integración / ayuda).
    aliases_validos = _aliases_comandos()
    # Comandos que aceptan argumentos CLI (el resto los ignora).
    comandos_con_args = {"trifasico", "tri", "3f", "monofasico", "mono", "1f",
                         "graficar", "fasores", "plot"}
    for comando, _, handler in _COMANDOS:
        aliases = [a.strip() for a in comando.replace(",", " ").split()]
        if cmd in aliases:
            if handler is not None:
                if cmd in comandos_con_args:
                    handler(consola, args)
                else:
                    handler(consola)
            else:
                return False
            return True

    sugerencia = None
    coincidencias = difflib.get_close_matches(texto, aliases_validos, n=1, cutoff=0.5)
    if coincidencias:
        sugerencia = coincidencias[0]
    _mostrar_error_comando(consola, texto_original, sugerencia)
    return True


def main() -> None:
    """Punto de entrada de la consola interactiva SPT."""
    consola = Console()
    mostrar_banner(consola)

    completer = _ComandoCompleter(_palabras_comandos())
    historial = InMemoryHistory()
    _nav_reset()

    consola.print("[dim]Consola interactiva. Escriba 'help' para ver comandos.[/]\n")

    while True:
        try:
            linea = prompt(
                _prompt_actual(),
                completer=completer,
                history=historial,
                bottom_toolbar="Ctrl-C para salir · Escriba 'help' para ayuda · "
                               "'salir'/'volver' para salir del contexto",
            )
        except (KeyboardInterrupt, EOFError):
            consola.print("\n[bold]Hasta pronto![/]")
            break

        if not _ejecutar(consola, linea):
            consola.print("\n[bold]Hasta pronto![/]")
            break


if __name__ == "__main__":
    main()
