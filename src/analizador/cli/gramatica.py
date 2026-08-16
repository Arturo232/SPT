"""Gramática por niveles para los comandos de red de la consola SPT.

Define un analizador sintáctico de tres niveles que fuerza un flujo lógico
y educativo de comandos para Sistemas Eléctricos de Potencia:

  Nivel 1 - Sistema eléctrico (comando raíz): ``monofasico`` / ``trifasico``.
            Regla de exclusión: el token de sistema no puede repetirse dentro
            de la misma instrucción.
  Nivel 2 - Componente de red (obligatorio): ``fuente`` / ``carga`` / ``linea``.
  Nivel 3 - Parámetros y banderas según el componente seleccionado.

Este módulo es **puro** (no imprime ni lee): solo interpreta la instrucción y
regresa un resultado estructurado o lanza un ``ErrorSintactico`` con
información pedagógica (qué falló, qué se esperaba y ejemplos válidos).

La consola CLI legada (``trifasico --fuente ... --cargas ...``) no se
interpreta aquí; convive por compatibilidad y se gestiona en ``console.py``.
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Tipos de datos del resultado sintáctico
# ---------------------------------------------------------------------------
@dataclass
class ErrorSintactico(Exception):
    """Describe de forma educativa qué parte de la instrucción falló."""

    mensaje: str
    sugerencia: str = ""
    opciones_validas: list = field(default_factory=list)
    ejemplos: list = field(default_factory=list)

    def __str__(self) -> str:
        return self.mensaje


@dataclass
class Instruccion:
    """Instrucción ya interpretada y validada por la gramática."""

    sistema: str                 # 'monofasico' | 'trifasico'
    componente: str              # 'fuente' | 'carga' | 'linea'
    parametros: dict             # flags normalizados {nombre: valor}
    tokens_originales: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Vocabulario canónico
# ---------------------------------------------------------------------------
SISTEMAS = ("monofasico", "trifasico")
COMPONENTES = ("fuente", "carga", "linea")

# Nivel 3: banderas permitidas por componente.
# Formato: {componente: {flag: (tipo, opciones_validas)}}
#   tipo: 'opcion' (elige una de opciones_validas) | 'valor' (número/valor libre)
BANDERAS = {
    "fuente": {
        "--conexion": ("opcion", ("estrella", "delta")),
        "--v-rms": ("valor", ()),
        "--secuencia": ("opcion", ("positiva", "negativa")),
    },
    "carga": {
        "--potencia-activa": ("valor", ()),
        "--factor-potencia": ("valor", ()),
        "--tipo": ("opcion", ("inductivo", "capacitivo")),
    },
    "linea": {
        "--z": ("valor", ()),
        "--r": ("valor", ()),
        "--x": ("valor", ()),
    },
}


# ---------------------------------------------------------------------------
# Parseo de valores
# ---------------------------------------------------------------------------
def _parsear_valor(tipo: str, flag: str, valor: str, opciones: tuple):
    """Valida el valor de una bandera según su tipo.

    ``tipo`` 'opcion' verifica que ``valor`` esté dentro de ``opciones``;
    ``tipo`` 'valor' acepta un número en notación decimal o compleja.
    """
    if tipo == "opcion":
        if valor not in opciones:
            raise ErrorSintactico(
                f"Valor no valido para '{flag}': '{valor}'.",
                sugerencia=f"'{flag}' solo acepta: {' | '.join(opciones)}.",
                opciones_validas=list(opciones),
            )
        return valor
    # 'valor' -> numero (entero, flotante, o complejo simple R o R+jX)
    return valor


# ---------------------------------------------------------------------------
# Parser principal de la gramática
# ---------------------------------------------------------------------------
def analizar_instruccion(tokens: list[str]) -> Instruccion:
    """Interpreta y valida una instrucción de tres niveles.

    Parámetros:
        tokens: lista de tokens (ya en minúsculas, sin comandos de escape).

    Regresa una :class:`Instruccion` normalizada.

    Lanza :class:`ErrorSintactico` con información pedagógica cuando la
    instrucción no respeta la gramática.
    """
    if not tokens:
        raise ErrorSintactico(
            "Instruccion vacia.",
            sugerencia="Escriba 'trifasico' o 'monofasico' seguido de un "
                       "componente de red.",
            opciones_validas=list(SISTEMAS),
            ejemplos=["trifasico fuente", "monofasico carga"],
        )

    # --- Nivel 1: sistema -------------------------------------------------
    sistema = tokens[0]
    if sistema not in SISTEMAS:
        raise ErrorSintactico(
            f"No reconozco el comando '{sistema}'.",
            sugerencia="El primer comando debe ser el tipo de sistema "
                       "electrico.",
            opciones_validas=list(SISTEMAS),
            ejemplos=["trifasico fuente --v-rms 208",
                      "monofasico carga --potencia-activa 1200"],
        )

    # Regla de exclusión: el sistema no puede repetirse en la misma
    # instrucción.
    for token in tokens[1:]:
        if token == sistema:
            raise ErrorSintactico(
                f"No puedes repetir el comando '{sistema}'.",
                sugerencia=f"Despues de '{sistema}' debes especificar un "
                           "componente de red.",
                opciones_validas=list(COMPONENTES),
                ejemplos=[f"{sistema} fuente", f"{sistema} carga",
                          f"{sistema} linea"],
            )

    # --- Nivel 2: componente obligatorio ---------------------------------
    if len(tokens) < 2:
        raise ErrorSintactico(
            f"Falta el componente de red despues de '{sistema}'.",
            sugerencia=f"Despues de '{sistema}' debes especificar un "
                       "componente de red.",
            opciones_validas=list(COMPONENTES),
            ejemplos=[f"{sistema} fuente", f"{sistema} carga",
                      f"{sistema} linea"],
        )
    componente = tokens[1]
    if componente not in COMPONENTES:
        raise ErrorSintactico(
            f"Componente no valido: '{componente}'.",
            sugerencia=f"Despues de '{sistema}' debes indicar un componente "
                       "fisico de la red.",
            opciones_validas=list(COMPONENTES),
            ejemplos=[f"{sistema} fuente", f"{sistema} carga",
                      f"{sistema} linea"],
        )

    # --- Nivel 3: parámetros / banderas según componente -----------------
    parametros: dict = {}
    resto = tokens[2:]
    banderas_componente = BANDERAS.get(componente, {})

    i = 0
    while i < len(resto):
        token = resto[i]
        if not token.startswith("--"):
            raise ErrorSintactico(
                f"Token inesperado: '{token}'.",
                sugerencia=f"Despues de '{sistema} {componente}' solo se "
                           "admiten banderas.",
                opciones_validas=sorted(banderas_componente),
                ejemplos=[f"{sistema} {componente} "
                          f"{next(iter(banderas_componente), '--v-rms')} 208"],
            )
        flag = token
        if flag not in banderas_componente:
            raise ErrorSintactico(
                f"La bandera '{flag}' no es valida para el componente "
                f"'{componente}'.",
                sugerencia=f"Para '{componente}' las banderas validas son: "
                           f"{' | '.join(sorted(banderas_componente))}.",
                opciones_validas=sorted(banderas_componente),
                ejemplos=[f"{sistema} {componente} "
                          f"{next(iter(banderas_componente))} 208"],
            )
        tipo, opciones = banderas_componente[flag]
        if i + 1 >= len(resto):
            raise ErrorSintactico(
                f"La bandera '{flag}' requiere un valor.",
                sugerencia=f"Ejemplo: {sistema} {componente} {flag} <valor>.",
                ejemplos=[f"{sistema} {componente} {flag} 208"],
            )
        valor = resto[i + 1]
        parametros[flag] = _parsear_valor(tipo, flag, valor, opciones)
        i += 2

    return Instruccion(
        sistema=sistema,
        componente=componente,
        parametros=parametros,
        tokens_originales=tokens,
    )


def es_instruccion_cli(tokens: list[str]) -> bool:
    """Detecta si la instrucción usa la sintaxis CLI legada (``--fuente``,
    ``--cargas``, ``--linea``/``--lineas``), que convive con la gramática.

    La sintaxis legada comienza por un sistema y luego usa banderas del
    estilo ``--fuente ...`` (no un componente de red en Nivel 2).
    """
    if not tokens or tokens[0] not in SISTEMAS:
        return False
    if len(tokens) < 2:
        return False
    segundo = tokens[1]
    # La sintaxis legada usa banderas directas (--fuente/--cargas/...),
    # mientras la gramática usa un componente (fuente/carga/linea) sin '--'.
    return segundo in ("--fuente", "-f", "--cargas", "-c",
                       "--linea", "-l", "--lineas", "-L")
