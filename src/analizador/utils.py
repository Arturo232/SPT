"""Utilidades de presentación, entrada y exportación.

Equivalente a ``utils/*.m``. Las funciones de formateo son puras (devuelven
cadenas); las de presentación imprimen por consola.
"""

import csv
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from .config import default_config
from .core import power_factor, rad2deg, validate_input
from .errors import error_analizador


# ---------------------------------------------------------------------------
# Formateo puro (reutilizable por consola, exportación y GUI)
# ---------------------------------------------------------------------------
def format_complex(z):
    """Representación de un complejo en forma rectangular y polar.

    Regresa ``(rect, polar)`` con cadenas como '4 - j8' y
    '8.94427 angulo -63.4349 deg'.
    """
    validate_input("numeric", z, "z")
    rect = _rect_string(z)
    polar = "%g angulo %g deg" % (abs(z), rad2deg(np.angle(z)))
    return rect, polar


def _rect_string(z):
    if abs(np.imag(z)) < 1e-12 * max(1, abs(z)):
        return "%g" % np.real(z)
    if abs(np.real(z)) < 1e-12 * max(1, abs(z)):
        return "%gj" % np.imag(z)
    if np.imag(z) >= 0:
        return "%g + j%g" % (np.real(z), np.imag(z))
    return "%g - j%g" % (np.real(z), -np.imag(z))


def _state_string(tipo):
    if tipo == "inductiva":
        return "ATRASO (inductivo)"
    if tipo == "capacitiva":
        return "ADELANTO (capacitivo)"
    return "RESISTIVO"


def format_power(S):
    """Presentación de una potencia compleja como cadena multilínea."""
    validate_input("numeric", S, "S")
    fp_info = power_factor(S)
    return ("P = %g W\nQ = %g var\n|S| = %g VA\n"
            "angulo = %g deg\nFP = %g\nestado = %s" % (
                np.real(S), np.imag(S), fp_info.Sabs,
                rad2deg(np.angle(S)), fp_info.fp, _state_string(fp_info.type)))


def _es_estructura(val):
    return isinstance(val, SimpleNamespace)


def _campos(result):
    if isinstance(result, SimpleNamespace):
        return [n for n in result.__dict__.keys()]
    if isinstance(result, dict):
        return list(result.keys())
    return []


def _get(result, campo):
    if isinstance(result, SimpleNamespace):
        return getattr(result, campo)
    if isinstance(result, dict):
        return result[campo]
    raise KeyError(campo)


def format_results(result):
    """Texto de una estructura de resultados (tema, procedimiento, campos).

    Devuelve una cadena multilínea usada por consola, exportación TXT y GUI.
    """
    campos = _campos(result)
    lineas = []
    meta = _get(result, "meta") if "meta" in campos else None
    if meta is not None and _es_estructura(meta):
        if getattr(meta, "tema", None):
            lineas.append("Tema: " + meta.tema)
        formulas = getattr(meta, "formulas", None)
        if formulas:
            lineas.append("Procedimiento:")
            for k, f in enumerate(formulas, start=1):
                lineas.append("  %d. %s" % (k, f))
    for fn in campos:
        if fn == "meta":
            continue
        val = _get(result, fn)
        if _es_estructura(val) or isinstance(val, (list, tuple, dict)):
            continue
        if isinstance(val, (str, bool)):
            continue
        if isinstance(val, np.ndarray):
            continue
        if np.isscalar(val):
            if np.iscomplexobj(val):
                rect, polar = format_complex(val)
                lineas.append("%s: %s ; %s" % (fn, rect, polar))
            else:
                lineas.append("%s = %g" % (fn, val))
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Presentación por consola
# ---------------------------------------------------------------------------
def print_complex(z):
    """Imprime un complejo en forma rectangular y polar."""
    validate_input("numeric", z, "z")
    rect, polar = format_complex(z)
    print("  Rectangular: %s" % rect)
    print("  Polar:       %s" % polar)


def print_power(S):
    """Imprime la potencia compleja con todas sus magnitudes."""
    validate_input("numeric", S, "S")
    print(format_power(S))


_ETIQUETAS = {
    "V": "V (tension)", "Vfuente": "V (fuente)",
    "VL": "VL (tension de linea)", "Vf": "Vf (tension de fase)",
    "I": "I (corriente)", "IL": "IL (corriente de linea)",
    "If": "If (corriente de fase)", "Z": "Z (impedancia)",
    "Zeq": "Zeq (impedancia equivalente)", "Yeq": "Yeq (admitancia equivalente)",
    "Zline": "Zline (impedancia de linea)", "Zfase": "Zfase (impedancia por fase)",
    "ZY": "ZY (impedancia estrella)", "Zdelta": "Zdelta (impedancia delta)",
    "R": "R (resistencia)", "X": "X (reactancia)",
    "Xc": "Xc (reactancia capacitiva)", "I12": "I12", "S12": "S12",
    "Sf": "Sf (potencia por fase)", "P": "P (potencia activa)",
    "Q": "Q (potencia reactiva)", "Qc": "Qc (compensacion reactiva)",
    "Sabs": "|S| (potencia aparente)", "S12abs": "|S12|", "fp": "FP",
    "Zmag": "|Z|", "P12": "P12", "Q12": "Q12", "Pmax": "Pmax",
    "C_uF": "C (uF)", "C_F": "C (F)",
    "Sbase": "Sbase (potencia base)", "Vbase": "Vbase (tension base)",
    "Ibase": "Ibase (corriente base)", "Zbase": "Zbase (impedancia base)",
    "Ybase": "Ybase (admitancia base)",
    "valor_real": "valor (real)", "valor_pu": "valor (p.u.)",
    "zpu_viejo": "Z (p.u., base vieja)", "zpu_nuevo": "Z (p.u., base nueva)",
    "V1": "V1 (tension primario)", "V2": "V2 (tension secundario)",
    "N1": "N1 (espiras primario)", "N2": "N2 (espiras secundario)",
    "I1": "I1 (corriente primario)", "I2": "I2 (corriente secundario)",
    "a": "a (relacion de transformacion)", "Zref": "Z (referida)",
    "Zprimario_ref": "Z (secundario referida al primario)",
    "Zsecundario": "Z (secundario)", "reg": "regulacion (%)",
    "eficiencia": "eficiencia (%)", "perdidas_porcentaje": "perdidas (%)",
    "r": "razon VL2/VL1", "desfase_deg": "desfase (grados)",
    "Zpu_trafo": "Z (p.u., base transformador)", "Zpu_sistema": "Z (p.u., base sistema)",
    "I0": "I0 (secuencia cero)", "I1s": "I1 (secuencia positiva)",
    "I2s": "I2 (secuencia negativa)",
    "Ia": "Ia (fase a)", "Ib": "Ib (fase b)", "Ic": "Ic (fase c)",
    "Z0": "Z0 (secuencia cero)", "Z1": "Z1 (secuencia positiva)",
    "Z2": "Z2 (secuencia negativa)", "Zf": "Zf (impedancia de falla)",
    "Zth": "Zth (Thevenin)", "If": "If (corriente de falla)",
    "If_mag": "|If| (magnitud de falla)", "I_mag": "|I|",
    "E": "E (fem interna)", "E_mag": "|E| (fem interna)",
    "Xs": "Xs (reactancia sincrona)",
    "delta_deg": "delta (angulo de carga, grados)",
    "delta0_deg": "delta0 (angulo inicial, grados)",
    "deltaCr_deg": "deltaCr (angulo critico, grados)",
    "deltaMax_deg": "deltaMax (angulo maximo, grados)",
    "A1": "A1 (area de aceleracion)", "A2": "A2 (area de desaceleracion)",
    "tcr": "tcr (tiempo critico de despeje, s)",
    "Pa": "Pa (potencia de aceleracion)", "M": "M (constante de inercia)",
    "Pm": "Pm (potencia mecanica)", "Pmax_falla": "Pmax (durante la falla)",
}


def print_results(result):
    """Presenta una estructura de resultados de forma genérica."""
    if not (_es_estructura(result) or isinstance(result, dict)):
        error_analizador("presentacion", "noEstructura",
                         "Error: se espera una estructura de resultados.")
    campos = _campos(result)
    print("\nRESULTADOS")
    print("--------------------------------------------")
    meta = _get(result, "meta") if "meta" in campos else None
    if meta is not None and _es_estructura(meta):
        if getattr(meta, "tema", None):
            print("Tema: %s" % meta.tema)
        formulas = getattr(meta, "formulas", None)
        if formulas:
            print("Procedimiento:")
            for k, f in enumerate(formulas, start=1):
                print("  %d. %s" % (k, f))
        print("--------------------------------------------")
    for campo, etiqueta in _ETIQUETAS.items():
        if campo in campos:
            val = _get(result, campo)
            if np.isscalar(val) and not isinstance(val, (str, bool)):
                if np.iscomplexobj(val):
                    print("%-26s" % (etiqueta + ":"))
                    print_complex(val)
                else:
                    print("%-26s = %g" % (etiqueta + ":", val))
    if "type" in campos and isinstance(_get(result, "type"), str):
        print("%-26s = %s" % ("Tipo de carga:", _get(result, "type").upper()))
    if "S" in campos:
        s_val = _get(result, "S")
        if np.isscalar(s_val):
            print_power(s_val)
    print("--------------------------------------------")
    if meta is not None and _es_estructura(meta):
        advertencias = getattr(meta, "advertencias", [])
        if advertencias:
            print("ADVERTENCIAS")
            for adv in advertencias:
                print("  - %s" % adv)
            print("--------------------------------------------")


# ---------------------------------------------------------------------------
# Entrada de datos por consola
# ---------------------------------------------------------------------------
def _leer_numero(prompt):
    while True:
        respuesta = input(prompt + " ").strip()
        try:
            return float(respuesta)
        except ValueError:
            print("Error: ingrese un numero valido.")


def _leer_positivo(prompt):
    while True:
        val = _leer_numero(prompt)
        if val > 0:
            return val
        print("Error: el valor debe ser positivo.")


def _leer_fp(prompt):
    while True:
        val = _leer_numero(prompt)
        if 0 <= val <= 1:
            return val
        print("Error: el factor de potencia debe estar entre 0 y 1.")


def _leer_frecuencia(prompt):
    while True:
        val = _leer_numero(prompt)
        if val > 0:
            return val
        print("Error: la frecuencia debe ser positiva.")


def _leer_choice(prompt, opciones):
    print(prompt)
    for k, opcion in enumerate(opciones, start=1):
        print("  %d. %s" % (k, opcion))
    while True:
        val = _leer_numero("Opcion:")
        if 1 <= val <= len(opciones) and val == round(val):
            return int(round(val))
        print("Error: opcion fuera de rango.")


def _leer_complejo(prompt):
    from .core import polar_to_complex
    print(prompt)
    mag = _leer_positivo("  Magnitud:")
    ang = _leer_numero("  Angulo (grados):")
    return polar_to_complex(mag, ang)


def input_helpers(mode, prompt, opciones=None):
    """Funciones de ayuda para la entrada de datos por consola."""
    m = mode.lower()
    if m == "number":
        return _leer_numero(prompt)
    if m == "positive":
        return _leer_positivo(prompt)
    if m == "fp":
        return _leer_fp(prompt)
    if m == "frequency":
        return _leer_frecuencia(prompt)
    if m == "choice":
        return _leer_choice(prompt, opciones)
    if m == "complex":
        return _leer_complejo(prompt)
    error_analizador("presentacion", "modoDesconocido",
                     "Error: modo de entrada desconocido: %s", mode)


# ---------------------------------------------------------------------------
# Conversión de unidades
# ---------------------------------------------------------------------------
_PREFIX_FACTOR = {"": 1, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3,
                  "k": 1e3, "M": 1e6, "G": 1e9}
_PREFIXES = ["p", "n", "u", "m", "k", "M", "G"]


def _parse_unit(unit):
    if not isinstance(unit, str) or unit == "":
        error_analizador("unidades", "unidadInvalida", "Error: unidad no valida.")
    if len(unit) >= 2 and unit[0] in _PREFIXES:
        return unit[0], unit[1:]
    return "", unit


def unit_convert(value, from_unit, to_unit):
    """Convierte un valor entre unidades con prefijos SI.

    P. ej. ``unit_convert(5, 'kVA', 'VA')`` → 5000.
    Regresa ``{value, fromUnit, toUnit, base}``.
    """
    validate_input("numeric", value, "value")
    p1, base1 = _parse_unit(from_unit)
    p2, base2 = _parse_unit(to_unit)
    if base1 != base2:
        error_analizador("unidades", "unidadesIncompatibles",
                         "Error: {0} y {1} no son unidades compatibles.",
                         from_unit, to_unit)
    f1 = _PREFIX_FACTOR[p1]
    f2 = _PREFIX_FACTOR[p2]
    result = SimpleNamespace()
    result.value = value * f1 / f2
    result.fromUnit = from_unit
    result.toUnit = to_unit
    result.base = base1
    return result


# ---------------------------------------------------------------------------
# Exportación de resultados
# ---------------------------------------------------------------------------
def _serializar_para_json(val):
    """Serializa un resultado a tipos JSON (complejos como {re, im})."""
    if _es_estructura(val):
        out = {}
        for c in val.__dict__:
            out[c] = _serializar_para_json(getattr(val, c))
        return out
    if isinstance(val, dict):
        return {k: _serializar_para_json(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_serializar_para_json(v) for v in val]
    if isinstance(val, np.ndarray):
        if np.iscomplexobj(val):
            return {"re": np.real(val).tolist(), "im": np.imag(val).tolist()}
        return val.tolist()
    if isinstance(val, (complex, np.complexfloating)) or (np.iscomplexobj(val) and np.isscalar(val)):
        return {"re": float(np.real(val)), "im": float(np.imag(val))}
    if isinstance(val, np.number):
        return val.item()
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val
    return str(val)


def _escribir_texto(archivo, contenido):
    try:
        with open(archivo, "w", encoding="utf-8") as fh:
            fh.write(contenido)
    except OSError:
        error_analizador("presentacion", "noSePudoEscribir",
                         "Error: no se pudo escribir el archivo %s.", archivo)


def _escribir_tabla(result, archivo):
    campos = _campos(result)
    filas = []
    for fn in campos:
        if fn == "meta":
            continue
        val = _get(result, fn)
        if _es_estructura(val) or isinstance(val, (list, tuple, dict)):
            continue
        if isinstance(val, (str, bool)):
            continue
        if np.isscalar(val):
            if np.iscomplexobj(val):
                filas.append((fn, "%g + j%g" % (np.real(val), np.imag(val))))
            else:
                filas.append((fn, "%g" % val))
    with open(archivo, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["campo", "valor"])
        for nombre, valor in filas:
            writer.writerow([nombre, valor])


def resolve_export_path(archivo: str | Path) -> Path:
    """Resuelve la ruta final de un archivo de exportación.

    - Rutas absolutas se respetan tal cual.
    - Rutas relativas se combinan con ``export_dir()``.
    - Crea los directorios intermedios necesarios.
    """
    from .config import export_dir

    ruta = Path(archivo)
    if not ruta.is_absolute():
        ruta = export_dir() / ruta
    ruta.parent.mkdir(parents=True, exist_ok=True)
    return ruta


def export_results(result, archivo, formato=None):
    """Exporta una estructura de resultados a un archivo.

    Formatos: 'txt', 'csv', 'json', 'xlsx'. Si ``formato`` se omite, se
    deduce de la extensión; sin extensión se usa txt. Regresa la ruta real
    del archivo creado.
    """
    if not (_es_estructura(result) or isinstance(result, dict)):
        error_analizador("presentacion", "noEstructura",
                         "Error: se espera una estructura de resultados.")
    import os
    ruta = resolve_export_path(archivo)
    archivo_str = str(ruta)
    if formato is None:
        ext = os.path.splitext(archivo_str)[1].lower()
        formato = {".txt": "txt", ".csv": "csv", ".json": "json",
                   ".xlsx": "xlsx", ".xls": "xlsx"}.get(ext, "txt")
    ext = os.path.splitext(archivo_str)[1]
    if not ext:
        archivo_str = archivo_str + "." + formato.lower()

    fmt = formato.lower()
    if fmt == "txt":
        _escribir_texto(archivo_str, format_results(result))
    elif fmt == "json":
        _escribir_texto(archivo_str, json.dumps(
            _serializar_para_json(result), ensure_ascii=False, indent=2))
    elif fmt in ("csv", "xlsx"):
        _escribir_tabla(result, archivo_str)
    else:
        error_analizador("presentacion", "formatoInvalido",
                         "Error: formato no soportado: %s.", formato)
    return archivo_str
