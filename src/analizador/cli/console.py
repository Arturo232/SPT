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


def _parse_red_args(args: list[str]):
    """Interpreta los argumentos de línea de comando de una red.

    Opciones aceptadas:
      --fuente <V>             Tensión de la fuente [V].
      --cargas <Tipo:Valor>... Lista dinámica de 'N' cargas (1, 2 o N).
      --linea <Z>              Un tramo de impedancia de línea.
      --lineas <Z>...          Varios tramos de impedancia de línea (se suman).
      --paralelo               Bandera documentada: las cargas ya se reducen
                               en paralelo (no altera el cálculo).

    Cada valor complejo acepta rectangular ``a+jb`` o polar ``M[ángulo]``.
    Regresa ``SimpleNamespace(fuente, cargas, lineas, paralelo)``.
    """
    fuente = None
    cargas: list[tuple[str, complex]] = []
    lineas: list[complex] = []
    paralelo = False

    i = 0
    n = len(args)
    while i < n:
        tok = args[i]
        if tok.startswith("--"):
            nombre = tok.lower()
            if nombre in ("--fuente", "-f"):
                if i + 1 >= n:
                    raise ValueError("falta el valor de --fuente")
                fuente = _parse_complejo_valor(args[i + 1])
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
            else:
                raise ValueError(f"opcion desconocida: '{tok}'")
        else:
            raise ValueError(f"argumento inesperado: '{tok}'. "
                             "Use --fuente, --cargas, --linea/--lineas.")
    return SimpleNamespace(fuente=fuente, cargas=cargas, lineas=lineas,
                           paralelo=paralelo)


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


def _renderizar_red(consola: Console, circuito, res, modo: str) -> None:
    """Renderiza las 4 componentes visuales de un circuito resuelto."""
    es_tri = modo == "trifasico"

    # --- Panel 1: Datos de entrada ------------------------------------
    datos = Text()
    if es_tri:
        datos.append("Fuente: V_L = ", style="bold")
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
                        border_style="cyan"))

    # --- Tabla 2: Proceso de reduccion ---------------------------------
    reduccion = Table(
        title="2. Proceso de reduccion (equivalente por fase)",
        border_style="blue", box=None)
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
                        border_style="magenta"))

    # --- Tabla 4: Balance de potencia ----------------------------------
    balance = Table(
        title="4. Balance de potencia", border_style="green", box=None)
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
        border_style="yellow", box=None)
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
    circuito.set_fuente(abs(datos.fuente), 0.0, "linea")
    if datos.lineas:
        circuito.set_linea(sum(datos.lineas))
    for tipo, z in datos.cargas:
        circuito.agregar_carga(tipo, z)
    res = circuito.resolver()
    _renderizar_red(consola, circuito, res, "trifasico")


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
    _renderizar_red(consola, circuito, res, "monofasico")


def _mostrar_error_args(consola: Console, err: Exception) -> None:
    """Muestra un panel de error para la sintaxis de los argumentos CLI."""
    consola.print(
        Panel(
            f"[bold red]{err}[/]\n\n"
            "Sintaxis:\n"
            "  trifasico  --fuente <V> --cargas <Y|D>:<Z>... "
            "[--linea <Z> | --lineas <Z>...]\n"
            "  monofasico --fuente <V> --cargas <Z>... "
            "[--linea <Z> | --lineas <Z>...]\n"
            "  Z acepta rectangular 'a+jb' o polar 'M[angulo]'.\n"
            "  Ej: trifasico --fuente 208 --cargas Y:4+j2 D:5-j4 --linea 8+j4",
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
        "  [cyan]trifasico --fuente 208 --cargas Y:4+j2 D:5-j4 --linea 8+j4[/]\n"
        "  [cyan]monofasico --fuente 120 --cargas 4+j2 5-j4 --lineas 8+j4 2+j1[/]\n"
        "  [dim]Banderas autocompletadas: --fuente --cargas --linea --lineas "
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
# de red (trifasico / monofasico).
_BANDERAS = ("--fuente", "--cargas", "--linea", "--lineas", "--paralelo")


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
    comandos_con_args = {"trifasico", "tri", "3f", "monofasico", "mono", "1f"}
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
