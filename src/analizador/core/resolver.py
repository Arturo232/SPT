"""Lógica pura de la GUI: resuelve un cálculo por su identificador.

Equivalente a ``app/resolverCalculo.m``. Devuelve ``(texto, result)`` donde
``texto`` es la cadena legible (resultados o error controlado) y ``result``
la estructura de resultados (contrato) con ``.meta``.
"""

from .base import polar_to_complex
from ..utils import format_results


def resolver_calculo(id_, v):
    """Resuelve un cálculo por su identificador.

    ids admitidos:
      'potenciaPF'  : v.P, v.fp, v.tipo
      'correccionFP': v.P, v.fp1, v.fp2, v.V, v.f
      'cargaVZ'     : v.Vmag, v.Vang, v.R, v.X
      'trifasico'   : v.VL, v.conexion, v.R, v.X
      'perUnit'     : v.Sbase, v.Vbase, v.fases, v.valor, v.tipoMag
    """
    from ..services import (service_analizar_carga, service_corregir_fp,
                            service_per_unit, service_trifasico_carga)

    try:
        if id_ == "potenciaPF":
            result = service_analizar_carga("PF", v.P, v.fp, v.tipo)
        elif id_ == "correccionFP":
            result = service_corregir_fp(v.P, v.fp1, v.fp2, v.V, v.f)
        elif id_ == "cargaVZ":
            voltaje = polar_to_complex(v.Vmag, v.Vang)
            result = service_analizar_carga("VZ", voltaje, v.R + 1j * v.X)
        elif id_ == "trifasico":
            result = service_trifasico_carga(v.VL, v.conexion, v.R + 1j * v.X)
        elif id_ == "perUnit":
            result = service_per_unit(v.Sbase, v.Vbase, v.fases, v.valor,
                                      v.tipoMag)
        else:
            from ..errors import error_analizador
            error_analizador("servicios", "modoDesconocido",
                             "Error: calculo no reconocido: {0}", id_)

        if isinstance(result, dict) and "codigo" in result:
            texto = "ERROR\n" + result["mensaje"]
        else:
            texto = format_results(result)
        return texto, result
    except Exception as err:
        texto = "ERROR\n" + str(err)
        from ..errors import construir_error
        result = construir_error(err)
        return texto, result
