"""Configuración por defecto y catálogo canónico de mensajes.

Equivalente a ``config/defaultConfig.m`` y ``config/mensajes.m``.
La configuración externalizada se lee de ``config/config.json``.
"""

import json
import os
from pathlib import Path


def mensajes() -> dict:
    """Catálogo central de mensajes de error del proyecto.

    Clave: ``analizador:<modulo>:<codigo>``; valor: mensaje canónico
    (sin valores interpolados).
    """
    catalogo = {
        # --- núcleo (core) ---
        "analizador:core:noNumerico": "Error: el valor debe ser numerico.",
        "analizador:core:fpInvalido": "Error: el factor de potencia debe estar entre 0 y 1.",
        "analizador:core:noPositivo": "Error: el valor debe ser positivo.",
        "analizador:core:frecuenciaInvalida": "Error: la frecuencia debe ser positiva.",
        "analizador:core:cero": "Error: el valor no puede ser cero.",
        "analizador:core:noEscalar": "Error: el valor debe ser un escalar.",
        "analizador:core:tipoDesconocido": "Error: tipo de validacion desconocido.",
        "analizador:core:magNegativa": "Error: la magnitud debe ser no negativa.",
        "analizador:core:dimensiones": "Error: las entradas deben tener las mismas dimensiones.",
        # --- circuitos monofásicos ---
        "analizador:circuitosMonofasicos:Xcero": "Error: la reactancia no puede ser cero.",
        "analizador:circuitosMonofasicos:sinImpedancias": "Error: indique al menos una impedancia.",
        # --- potencia compleja ---
        "analizador:potenciaCompleja:argumentos": "Error: argumentos incorrectos.",
        "analizador:potenciaCompleja:modoDesconocido": "Error: modo de calculo no valido.",
        "analizador:potenciaCompleja:tipoInvalido": "Error: tipo de carga no reconocido.",
        "analizador:potenciaCompleja:sinEntradas": "Error: indique al menos una potencia.",
        "analizador:potenciaCompleja:estructuraInvalida": "Error: la estructura no contiene S ni P/Q.",
        # --- corrección de factor de potencia ---
        "analizador:correccionFP:QcCero": "Error: la compensacion Qc no puede ser cero.",
        "analizador:correccionFP:XcCero": "Error: Xc no puede ser cero.",
        # --- sistemas trifásicos ---
        "analizador:sistemasTrifasicos:conexionInvalida": "Error: conexion no reconocida. Use Y o Delta.",
        "analizador:sistemasTrifasicos:noTrifasico": "Error: se esperan exactamente 3 fasores.",
        # --- sistema por unidad ---
        "analizador:perUnit:fasesInvalida": "Error: numero de fases no reconocido.",
        "analizador:perUnit:tipoInvalido": "Error: tipo de magnitud no valido. Use V, I, S o Z.",
        "analizador:perUnit:baseIncompleta": "Error: la base no contiene el campo requerido.",
        # --- transformadores ---
        "analizador:transformadores:ladoInvalido": "Error: lado no reconocido. Use primario o secundario.",
        "analizador:transformadores:conexionInvalida": "Error: conexion no reconocida. Use Y o Delta.",
        # --- flujo de carga N-barras ---
        "analizador:flujoCarga:tipoBarraInvalido": "Error: tipo de barra no reconocido. Use slack, PV o PQ.",
        "analizador:flujoCarga:sinSlack": "Error: se requiere una barra slack.",
        "analizador:flujoCarga:multiplesSlack": "Error: solo se permite una barra slack.",
        "analizador:flujoCarga:lineaImpedanciaCero": "Error: la linea tiene impedancia cero.",
        "analizador:flujoCarga:ybusSingular": "Error: Ybus es singular; no se puede invertir.",
        # --- unidades ---
        "analizador:unidades:unidadesIncompatibles": "Error: las unidades no son compatibles.",
        "analizador:unidades:unidadInvalida": "Error: unidad no valida.",
        # --- presentación ---
        "analizador:presentacion:noEstructura": "Error: se espera una estructura de resultados.",
        "analizador:presentacion:modoDesconocido": "Error: modo de entrada desconocido.",
        "analizador:presentacion:formatoInvalido": "Error: formato de exportacion no soportado.",
        "analizador:presentacion:noSePudoEscribir": "Error: no se pudo escribir el archivo.",
        # --- servicios ---
        "analizador:servicios:modoDesconocido": "Error: modo de servicio no valido.",
        "analizador:servicios:excepcion": "Error interno del servicio.",
        # --- componentes simétricas ---
        "analizador:componentesSimetricas:noTrifasico": "Error: se esperan exactamente 3 fasores.",
        # --- estabilidad ---
        "analizador:estabilidad:PmExcede": "Error: Pm debe ser menor que Pmax.",
        "analizador:estabilidad:deltaCrInvalido": "Error: deltaCr debe ser mayor que delta0.",
        # --- circuito trifásico (entorno de resolución) ---
        "analizador:circuito:sinFuente": "Error: defina la tension de la fuente (VL) antes de resolver.",
        "analizador:circuito:sinCargas": "Error: agregue al menos una carga antes de resolver.",
        "analizador:circuito:sinResolver": "Error: resuelva el circuito antes de generar el reporte.",
        "analizador:circuito:comandoDesconocido": "Error: comando no reconocido. Escriba 'ayuda' para ver los comandos.",
        "analizador:circuito:complejoInvalido": "Error: no pude interpretar el numero complejo. Use el formato R+jX (ej. 10+5j).",
        "analizador:circuito:argumentos": "Error: argumentos insuficientes para el comando.",
        "analizador:circuito:datoFuenteInvalido": "Error: el tipo de dato de la fuente debe ser 'linea' o 'fase'.",
    }
    return catalogo


def default_config() -> dict:
    """Configuración por defecto de la aplicación.

    Lee ``config/config.json`` (ruta relativa al paquete) con valores por
    defecto si el archivo no existe o no puede leerse.
    """
    cfg = {
        "frequency": 60,      # frecuencia nominal [Hz]
        "decimals": 4,        # decimales en la presentación
        "tolerance": 1e-6,    # tolerancia numérica de los tests
        "language": "es",     # idioma de la interfaz
    }
    ruta = Path(os.environ.get("SEP_CONFIG", Path(__file__).parent / "config.json"))
    try:
        if ruta.is_file():
            with open(ruta, "r", encoding="utf-8") as fh:
                datos = json.load(fh)
            for clave in cfg:
                if clave in datos:
                    cfg[clave] = datos[clave]
    except Exception:
        # mantener valores por defecto si el JSON es inválido
        pass
    return cfg
