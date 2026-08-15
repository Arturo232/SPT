"""Visualización (equivalente a ``viz/*.m``).

Diagrama de fasores y triángulo de potencias con ``matplotlib``.
"""

import numpy as np

from .core import validate_input


def phasor_plot(phasores, etiquetas=None, titulo="Diagrama de fasores"):
    """Grafica fasores en un diagrama polar.

    Regresa el objeto del eje polar (compatible con ``matplotlib``).
    """
    import matplotlib.pyplot as plt

    validate_input("numeric", phasores, "phasores")
    if etiquetas is None:
        etiquetas = []
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="polar")
    angulos = np.angle(np.asarray(phasores).flatten())
    magnitudes = np.abs(np.asarray(phasores).flatten())
    ax.plot(angulos, magnitudes, "o-", linewidth=1.5)
    ax.set_title(titulo)
    if etiquetas:
        for k, (a, m) in enumerate(zip(angulos, magnitudes)):
            if k < len(etiquetas):
                ax.text(a, m, etiquetas[k], ha="center")
    return ax


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
