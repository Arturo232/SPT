"""Visualización (equivalente a ``viz/*.m``).

Diagramas de fasores vectoriales y triángulo de potencias con ``matplotlib``.

Todas las funciones **no** abren ventanas emergentes: retornan la figura y el
eje para que el llamador decida cuándo llamar a ``plt.show()`` o guardar.
"""

import numpy as np

from ..core.base import validate_input


# Colores estándar por fase (A: Rojo, B: Naranja/Amarillo, C: Azul).
_COLORES_FASE = ["#D62728", "#FF7F0E", "#1F77B4"]


def _color_por_indice(idx):
    """Devuelve el color correspondiente al índice (ciclado por fase)."""
    return _COLORES_FASE[idx % len(_COLORES_FASE)]


def _fmt_polar_label(nombre, z, unidad):
    """Formatea una etiqueta polar descriptiva para la punta de una flecha.

    Ej: ``"Van: 120.08 V ∠ -30.0°"``.
    """
    mag = abs(z)
    ang = np.degrees(np.angle(z))
    return "%s: %.2f %s ∠ %.1f°" % (nombre, mag, unidad, ang)


def phasor_plot(fasores, etiquetas=None, titulo="Diagrama de fasores",
                unidad="V", colores=None, ax=None):
    """Dibuja fasores como vectores (flechas) en un eje polar.

    Parámetros:
        fasores: iterable de números complejos (origen en (0,0)).
        etiquetas: lista de nombres de variable para cada fasor.
        titulo: título del diagrama.
        unidad: unidad para el texto de etiqueta ("V", "A", ...).
        colores: lista de colores; por defecto cicla Rojo/Naranja/Azul.
        ax: eje polar opcional (para crear subplots).

    Retorna ``(fig, ax)``. No llama a ``plt.show()``.
    """
    import matplotlib.pyplot as plt

    fasores = np.asarray(fasores, dtype=complex).flatten()
    validate_input("numeric", fasores, "fasores")
    n = fasores.size
    if n == 0:
        raise ValueError("phasor_plot: no hay fasores que graficar")
    if etiquetas is None:
        etiquetas = [""] * n
    etiquetas = list(etiquetas) + [""] * (n - len(etiquetas))
    if colores is None:
        colores = [_color_por_indice(i) for i in range(n)]

    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="polar")
    else:
        fig = ax.figure

    angulos = np.angle(fasores)
    magnitudes = np.abs(fasores)
    rmax = magnitudes.max() * 1.10 if magnitudes.max() > 0 else 1.0

    # Offsets de etiqueta por fasor. Si dos fasores tienen ángulos muy
    # cercanos (ej. corriente de línea e interna en Delta) se varía el
    # desplazamiento para que los textos no se traslapen.
    offsets = _calcular_offsets_etiquetas(angulos, n)

    for k in range(n):
        color = colores[k]
        # Flecha desde el origen hasta la punta del fasor.
        ax.annotate(
            "", xy=(angulos[k], magnitudes[k]), xytext=(0, 0),
            arrowprops=dict(arrowstyle="->", color=color,
                            lw=2, mutation_scale=18),
        )
        if etiquetas[k]:
            dx, dy = offsets[k]
            ax.annotate(
                _fmt_polar_label(etiquetas[k], fasores[k], unidad),
                xy=(angulos[k], magnitudes[k]),
                xytext=(dx, dy),
                textcoords="offset points",
                fontsize=8, color=color, ha="left", va="bottom",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none",
                          alpha=0.7),
            )

    ax.set_ylim(0, rmax)
    ax.set_rmax(rmax)
    # Desplaza las etiquetas radiales hacia afuera para no interrumpir la
    # lectura de los fasores.
    ax.set_rticks(np.linspace(0, rmax, 5))
    ax.tick_params(pad=10)
    ax.grid(True)
    ax.set_title(titulo)
    return fig, ax


def _calcular_offsets_etiquetas(angulos, n, umbral_grados=5.0):
    """Calcula offsets (en puntos) para las etiquetas de cada fasor.

    Si dos fasores comparten un ángulo casi idéntico (dentro de
    ``umbral_grados``), se alterna el desplazamiento vertical para que los
    textos no se encimen. El resto usa un offset por defecto (5, 5).
    """
    offsets = [(5, 5)] * n
    grados = np.degrees(angulos)
    for i in range(n):
        for j in range(i + 1, n):
            dif = abs(grados[i] - grados[j])
            dif = min(dif, 360.0 - dif)
            if dif < umbral_grados:
                # Textos en direcciones opuestas para separarlos.
                offsets[j] = (5, -12)
    return offsets


def plot_voltage_phasors(res, ax=None):
    """Grafica los fasores de tensión de un circuito trifásico balanceado.

    Para cada carga en Estrella se dibujan ``Van, Vbn, Vcn`` (fase-neutro);
    para cada carga en Delta se dibujan ``Vab, Vbc, Vca`` (tensión de línea).

    Retorna ``(fig, ax)``.
    """
    etiquetas = []
    fasores = []
    for k, c in enumerate(res.cargas, start=1):
        if c["conexion"] == "Y":
            van, vbn, vcn = _fasores_abc(c["v_fase"])
            fasores += [van, vbn, vcn]
            etiquetas += ["Van", "Vbn", "Vcn"]
        else:  # Delta
            vab, vbc, vca = _fasores_abc(c["v_linea_fasor"])
            fasores += [vab, vbc, vca]
            etiquetas += ["Vab", "Vbc", "Vca"]
    return phasor_plot(fasores, etiquetas=etiquetas,
                       titulo="Fasores de tensión", unidad="V", ax=ax)


def plot_current_phasors(res, ax=None):
    """Grafica los fasores de corriente de un circuito trifásico balanceado.

    Para cada carga en Estrella se dibujan ``Ia, Ib, Ic`` (corriente de línea);
    para cada carga en Delta se dibujan ``Iab, Ibc, Ica`` (corriente de malla).

    Retorna ``(fig, ax)``.
    """
    etiquetas = []
    fasores = []
    for k, c in enumerate(res.cargas, start=1):
        if c["conexion"] == "Y":
            ia, ib, ic = _fasores_abc(c["i_linea"])
            fasores += [ia, ib, ic]
            etiquetas += ["Ia", "Ib", "Ic"]
        else:  # Delta
            iab, ibc, ica = _fasores_abc(c["i_fase"])
            fasores += [iab, ibc, ica]
            etiquetas += ["Iab", "Ibc", "Ica"]
    return phasor_plot(fasores, etiquetas=etiquetas,
                       titulo="Fasores de corriente", unidad="A", ax=ax)


def _fasores_abc(z):
    """Devuelve los tres fasores balanceados (a, b, c) desde la fase 'a'."""
    import math

    return (z,
            z * complex(math.cos(math.radians(-120)),
                        math.sin(math.radians(-120))),
            z * complex(math.cos(math.radians(120)),
                        math.sin(math.radians(120))))


def power_triangle(P, Q, titulo="Triangulo de potencias"):
    """Grafica el triángulo de potencias (P, Q, S). Regresa el eje."""
    import matplotlib.pyplot as plt

    validate_input("numeric", P, "P")
    validate_input("numeric", Q, "Q")
    s = np.hypot(P, Q)
    fig, ax = plt.subplots()
    ax.plot([0, P], [0, 0], color="b", linewidth=2)   # P
    ax.plot([P, P], [0, Q], color="g", linewidth=2)   # Q
    ax.plot([0, P], [0, Q], color="r", linewidth=2)   # S
    offset = max(abs(P), abs(Q)) * 0.08
    ax.text(P / 2, -offset, "P = %g" % P, color="b", ha="center")
    ax.text(P + max(abs(P), abs(Q)) * 0.05, Q / 2, "Q = %g" % Q,
            color="g", ha="left")
    ax.text(P / 2, Q / 2, "S = %g" % s, color="r")
    ax.grid(True)
    ax.set_xlabel("P (W)")
    ax.set_ylabel("Q (var)")
    ax.set_title(titulo)
    ax.axis("equal")
    return ax
