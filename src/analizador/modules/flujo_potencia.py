"""Flujo de potencia (equivalente a ``modules/flujoPotencia/*.m``).

Incluye el flujo entre dos fuentes y el flujo de carga N-barras
(Newton-Raphson y Gauss-Seidel). Solo cálculos: nunca imprimen.
"""

import math
from types import SimpleNamespace

import numpy as np

from ..core import (complex_power, current_from_voltage_impedance,
                    polar_to_complex, power_factor, rad2deg,
                    validate_input)
from ..errors import error_analizador


# ---------------------------------------------------------------------------
# Dos fuentes (caso simplificado puramente reactivo + general)
# ---------------------------------------------------------------------------
def active_power_flow(v1mag, delta1_deg, v2mag, delta2_deg, X):
    """``P12 = (V1*V2/X) * sin(delta1 - delta2)`` (línea puramente reactiva)."""
    validate_input("numeric", v1mag, "V1mag")
    validate_input("numeric", delta1_deg, "delta1Deg")
    validate_input("numeric", v2mag, "V2mag")
    validate_input("numeric", delta2_deg, "delta2Deg")
    validate_input("positive", X, "X")
    return (v1mag * v2mag / X) * math.sin(math.radians(delta1_deg - delta2_deg))


def reactive_power_flow(v1mag, delta1_deg, v2mag, delta2_deg, X):
    """``Q12 = (V1^2 - V1*V2*cos(delta1 - delta2)) / X`` (línea reactiva)."""
    validate_input("numeric", v1mag, "V1mag")
    validate_input("numeric", delta1_deg, "delta1Deg")
    validate_input("numeric", v2mag, "V2mag")
    validate_input("numeric", delta2_deg, "delta2Deg")
    validate_input("positive", X, "X")
    delta = delta1_deg - delta2_deg
    return (v1mag ** 2 - v1mag * v2mag * math.cos(math.radians(delta))) / X


def maximum_transfer_power(v1mag, v2mag, X):
    """``Pmax = V1*V2 / X``."""
    validate_input("numeric", v1mag, "V1mag")
    validate_input("numeric", v2mag, "V2mag")
    validate_input("positive", X, "X")
    return v1mag * v2mag / X


def power_flow_two_bus(v1mag, delta1_deg, v2mag, delta2_deg, zline):
    """Flujo de potencia entre dos fuentes por una impedancia de línea.

    Regresa ``{V1, V2, Zline, I12, S12, P12, Q12, S12abs, fp, type}`` y,
    si ``R ~ 0``, además ``P12_reactivo``, ``Q12_reactivo`` y ``Pmax``.
    """
    validate_input("numeric", v1mag, "V1mag")
    validate_input("numeric", delta1_deg, "delta1Deg")
    validate_input("numeric", v2mag, "V2mag")
    validate_input("numeric", delta2_deg, "delta2Deg")
    validate_input("numeric", zline, "Zline")
    validate_input("nonzero", zline, "Zline")

    v1 = polar_to_complex(v1mag, delta1_deg)
    v2 = polar_to_complex(v2mag, delta2_deg)

    result = SimpleNamespace()
    result.V1 = v1
    result.V2 = v2
    result.Zline = zline
    result.I12 = (v1 - v2) / zline
    result.S12 = complex_power(v1, result.I12)
    result.P12 = np.real(result.S12)
    result.Q12 = np.imag(result.S12)
    fp_info = power_factor(result.S12)
    result.S12abs = fp_info.Sabs
    result.fp = fp_info.fp
    result.type = fp_info.type

    x_linea = np.imag(zline)
    r_linea = abs(np.real(zline))
    if r_linea < 1e-12 * max(1, abs(zline)) and x_linea != 0:
        result.P12_reactivo = active_power_flow(v1mag, delta1_deg, v2mag, delta2_deg, x_linea)
        result.Q12_reactivo = reactive_power_flow(v1mag, delta1_deg, v2mag, delta2_deg, x_linea)
        result.Pmax = maximum_transfer_power(v1mag, v2mag, x_linea)
    return result


# ---------------------------------------------------------------------------
# Flujo de carga N-barras
# ---------------------------------------------------------------------------
def bus_structure(id_, tipo, V=1.0, angulo=0.0, P=0.0, Q=0.0):
    """Estructura de una barra (bus) para el flujo de carga.

    Campos: ``id, type ('slack'|'PV'|'PQ'), V, angle, P, Q``.
    Convención: ``P > 0`` es generación; en 'slack' V y angle son fijos.
    """
    if not isinstance(tipo, str):
        error_analizador("flujoCarga", "tipoBarraInvalido",
                         "Error: el tipo de barra debe ser 'slack', 'PV' o 'PQ'.")
    t = tipo.lower()
    if t not in ("slack", "pv", "pq"):
        error_analizador("flujoCarga", "tipoBarraInvalido",
                         "Error: tipo de barra no reconocido: {0}.", tipo)
    bus = SimpleNamespace()
    bus.id = id_
    bus.type = t
    bus.V = V if V is not None else 1.0
    bus.angle = angulo if angulo is not None else 0.0
    bus.P = P if P is not None else 0.0
    bus.Q = Q if Q is not None else 0.0
    return bus


def line_structure(from_, to_, R=0.0, X=0.0, B=0.0):
    """Estructura de una línea (modelo pi) para el flujo de carga.

    Campos: ``from, to, R, X, B`` (B se reparte B/2 en cada extremo).
    """
    line = SimpleNamespace()
    line.from_ = from_
    line.to = to_
    line.R = R if R is not None else 0.0
    line.X = X if X is not None else 0.0
    line.B = B if B is not None else 0.0
    return line


def ybus_matrix(n, lines):
    """Matriz de admitancias nodales ``Ybus``.

    ``y_ij = 1/(R+jX)``; ``Y_ii = sum(y) + jB/2``; ``Y_ij = -y``.
    """
    validate_input("numeric", n, "n")
    validate_input("positive", n, "n")
    ybus = np.zeros((n, n), dtype=complex)
    for line in lines:
        z = line.R + 1j * line.X
        if z == 0:
            error_analizador("flujoCarga", "lineaImpedanciaCero",
                             "Error: la linea {0}-{1} tiene impedancia cero.",
                             line.from_, line.to)
        y = 1 / z
        i = line.from_
        j = line.to
        ybus[i - 1, i - 1] = ybus[i - 1, i - 1] + y
        ybus[j - 1, j - 1] = ybus[j - 1, j - 1] + y
        ybus[i - 1, j - 1] = ybus[i - 1, j - 1] - y
        ybus[j - 1, i - 1] = ybus[j - 1, i - 1] - y
        if line.B != 0:
            ybus[i - 1, i - 1] = ybus[i - 1, i - 1] + 1j * line.B / 2
            ybus[j - 1, j - 1] = ybus[j - 1, j - 1] + 1j * line.B / 2
    return ybus


def zbus_matrix(ybus):
    """``Zbus = inv(Ybus)``."""
    validate_input("numeric", ybus, "Ybus")
    if np.linalg.det(ybus) == 0:
        error_analizador("flujoCarga", "ybusSingular",
                         "Error: Ybus es singular; no se puede invertir.")
    return np.linalg.inv(ybus)


def _bus_types(buses):
    return [b.type.lower() for b in buses]


def _armar_resultado(buses, V, delta, ybus, conv, iter_, slack, p_targ):
    """Construye la estructura de resultado compartida por ambos solvers."""
    n = len(V)
    result = SimpleNamespace()
    result.V = np.array(V, dtype=float).reshape(-1)
    result.delta = np.array(delta, dtype=float).reshape(-1)
    result.delta_deg = rad2deg(result.delta)
    result.Ybus = ybus
    result.converged = bool(conv)
    result.iterations = iter_
    result.slack = slack

    G = np.real(ybus)
    B = np.imag(ybus)
    p_slack = 0.0
    q_slack = 0.0
    i_s = slack - 1
    for j in range(n):
        d = delta[i_s] - delta[j]
        p_slack = p_slack + V[i_s] * V[j] * (G[i_s, j] * math.cos(d) + B[i_s, j] * math.sin(d))
        q_slack = q_slack + V[i_s] * V[j] * (G[i_s, j] * math.sin(d) - B[i_s, j] * math.cos(d))
    result.Pslack = p_slack
    result.Qslack = q_slack
    tipos = _bus_types(buses)
    no_slack = [i for i, t in enumerate(tipos) if t != "slack"]
    result.perdidas = p_slack + sum(p_targ[i] for i in no_slack)
    return result


def newton_raphson_power_flow(buses, lines, tol=1e-9, max_iter=50):
    """Resuelve el flujo de carga por Newton-Raphson.

    Regresa ``{V, delta, delta_deg, Ybus, converged, iterations, slack,
    Pslack, Qslack, perdidas}``.
    """
    n = len(buses)
    tipos = _bus_types(buses)
    slack_indices = [i + 1 for i, t in enumerate(tipos) if t == "slack"]
    if len(slack_indices) == 0:
        error_analizador("flujoCarga", "sinSlack",
                         "Error: se requiere una barra slack.")
    if len(slack_indices) > 1:
        error_analizador("flujoCarga", "multiplesSlack",
                         "Error: solo se permite una barra slack.")
    slack = slack_indices[0]

    ybus = ybus_matrix(n, lines)
    G = np.real(ybus)
    B = np.imag(ybus)

    V = np.ones(n)
    delta = np.zeros(n)
    V[slack - 1] = buses[slack - 1].V
    delta[slack - 1] = math.radians(buses[slack - 1].angle)
    pv = [i + 1 for i, t in enumerate(tipos) if t == "pv"]
    pq = [i + 1 for i, t in enumerate(tipos) if t == "pq"]
    for i in pv:
        V[i - 1] = buses[i - 1].V

    np_buses = pv + pq   # P especificada
    nq_buses = pq        # Q especificada
    n_p = len(np_buses)
    n_q = len(nq_buses)

    p_targ = [b.P for b in buses]
    q_targ = [b.Q for b in buses]

    conv = False
    iter_ = 0
    while iter_ < max_iter:
        iter_ += 1
        p_cal = np.zeros(n)
        q_cal = np.zeros(n)
        for i in range(n):
            for j in range(n):
                d = delta[i] - delta[j]
                p_cal[i] += V[i] * V[j] * (G[i, j] * math.cos(d) + B[i, j] * math.sin(d))
                q_cal[i] += V[i] * V[j] * (G[i, j] * math.sin(d) - B[i, j] * math.cos(d))

        dP = np.array([p_targ[i - 1] - p_cal[i - 1] for i in np_buses])
        dQ = np.array([q_targ[i - 1] - q_cal[i - 1] for i in nq_buses])
        if len(dP) == 0:
            dP = np.array([])
        if len(dQ) == 0:
            dQ = np.array([])
        if np.size(np.concatenate([np.abs(dP), np.abs(dQ)])) == 0 or \
                np.max(np.concatenate([np.abs(dP), np.abs(dQ)])) < tol:
            conv = True
            break
        if n_p == 0:
            conv = True
            break

        Hp = np.zeros((n_p, n_p))  # dP/ddelta
        Np = np.zeros((n_p, n_q))  # dP/dV
        Jq = np.zeros((n_q, n_p))  # dQ/ddelta
        Lq = np.zeros((n_q, n_q))  # dQ/dV

        for a, i in enumerate(np_buses):
            for b, j in enumerate(np_buses):
                d = delta[i - 1] - delta[j - 1]
                if i == j:
                    Hp[a, b] = -q_cal[i - 1] - B[i - 1, i - 1] * V[i - 1] ** 2
                else:
                    Hp[a, b] = V[i - 1] * V[j - 1] * (G[i - 1, j - 1] * math.sin(d)
                                                      - B[i - 1, j - 1] * math.cos(d))
            for b, j in enumerate(nq_buses):
                d = delta[i - 1] - delta[j - 1]
                if i == j:
                    Np[a, b] = p_cal[i - 1] / V[i - 1] + G[i - 1, i - 1] * V[i - 1]
                else:
                    Np[a, b] = V[i - 1] * (G[i - 1, j - 1] * math.cos(d)
                                           + B[i - 1, j - 1] * math.sin(d))

        for a, i in enumerate(nq_buses):
            for b, j in enumerate(np_buses):
                d = delta[i - 1] - delta[j - 1]
                if i == j:
                    Jq[a, b] = p_cal[i - 1] - G[i - 1, i - 1] * V[i - 1] ** 2
                else:
                    Jq[a, b] = -V[i - 1] * V[j - 1] * (G[i - 1, j - 1] * math.cos(d)
                                                       + B[i - 1, j - 1] * math.sin(d))
            for b, j in enumerate(nq_buses):
                d = delta[i - 1] - delta[j - 1]
                if i == j:
                    Lq[a, b] = q_cal[i - 1] / V[i - 1] - B[i - 1, i - 1] * V[i - 1]
                else:
                    Lq[a, b] = V[i - 1] * (G[i - 1, j - 1] * math.sin(d)
                                           - B[i - 1, j - 1] * math.cos(d))

        J = np.block([[Hp, Np], [Jq, Lq]])
        dx = np.linalg.solve(J, np.concatenate([dP, dQ]))
        for a, i in enumerate(np_buses):
            delta[i - 1] += dx[a]
        for a, i in enumerate(nq_buses):
            V[i - 1] += dx[n_p + a]

    return _armar_resultado(buses, V, delta, ybus, conv, iter_, slack, p_targ)


def gauss_seidel_power_flow(buses, lines, tol=1e-9, max_iter=100):
    """Resuelve el flujo de carga por Gauss-Seidel.

    Las barras PV fijan la magnitud de tensión tras cada iteración; no se
    aplican límites de reactiva. Regresa la misma estructura que
    ``newton_raphson_power_flow``.
    """
    n = len(buses)
    tipos = _bus_types(buses)
    slack_indices = [i + 1 for i, t in enumerate(tipos) if t == "slack"]
    if len(slack_indices) == 0:
        error_analizador("flujoCarga", "sinSlack",
                         "Error: se requiere una barra slack.")
    slack = slack_indices[0]

    ybus = ybus_matrix(n, lines)

    V = np.ones(n)
    delta = np.zeros(n)
    V[slack - 1] = buses[slack - 1].V
    delta[slack - 1] = math.radians(buses[slack - 1].angle)
    pv = [i + 1 for i, t in enumerate(tipos) if t == "pv"]
    for i in pv:
        V[i - 1] = buses[i - 1].V

    p_targ = [b.P for b in buses]

    conv = False
    iter_ = 0
    while iter_ < max_iter:
        iter_ += 1
        v_antes = V.copy()
        for i in range(1, n + 1):
            if i == slack:
                continue
            suma = 0
            for j in range(1, n + 1):
                if j != i:
                    suma = suma + ybus[i - 1, j - 1] * (V[j - 1] * np.exp(1j * delta[j - 1]))
            vi_previo = V[i - 1] * np.exp(1j * delta[i - 1])
            if tipos[i - 1] == "pq":
                si = buses[i - 1].P + 1j * buses[i - 1].Q
                v_nueva = (np.conjugate(si / vi_previo) - suma) / ybus[i - 1, i - 1]
            else:
                # PV: estimar Q y fijar magnitud
                qi = -np.imag(np.conjugate(vi_previo) * (ybus[i - 1, i - 1] * vi_previo + suma))
                si = buses[i - 1].P + 1j * qi
                v_nueva = (np.conjugate(si / vi_previo) - suma) / ybus[i - 1, i - 1]
                v_nueva = abs(V[i - 1]) * v_nueva / abs(v_nueva)
            V[i - 1] = abs(v_nueva)
            delta[i - 1] = np.angle(v_nueva)
        if np.max(np.abs(V - v_antes)) < tol:
            conv = True
            break

    return _armar_resultado(buses, V, delta, ybus, conv, iter_, slack, p_targ)


def power_mismatch(V, delta, ybus, buses):
    """Potencia calculada y desbalances para un estado dado.

    Regresa ``{dP, dQ, Pcal, Qcal, npBuses, nqBuses}``.
    """
    validate_input("numeric", V, "V")
    validate_input("numeric", delta, "delta")
    validate_input("numeric", ybus, "Ybus")
    n = len(np.atleast_1d(V))
    V = np.atleast_1d(V).astype(float)
    delta = np.atleast_1d(delta).astype(float)
    G = np.real(ybus)
    B = np.imag(ybus)

    p_cal = np.zeros(n)
    q_cal = np.zeros(n)
    for i in range(n):
        for j in range(n):
            d = delta[i] - delta[j]
            p_cal[i] += V[i] * V[j] * (G[i, j] * math.cos(d) + B[i, j] * math.sin(d))
            q_cal[i] += V[i] * V[j] * (G[i, j] * math.sin(d) - B[i, j] * math.cos(d))

    tipos = _bus_types(buses)
    np_buses = np.array([i + 1 for i, t in enumerate(tipos) if t != "slack"])
    nq_buses = np.array([i + 1 for i, t in enumerate(tipos) if t == "pq"])
    p_targ = np.array([b.P for b in buses])
    q_targ = np.array([b.Q for b in buses])

    m = SimpleNamespace()
    m.dP = p_targ[np_buses - 1] - p_cal[np_buses - 1]
    m.dQ = q_targ[nq_buses - 1] - q_cal[nq_buses - 1]
    m.Pcal = p_cal
    m.Qcal = q_cal
    m.npBuses = np_buses
    m.nqBuses = nq_buses
    return m


def caso2_barras():
    """Sistema de 2 barras con solución analítica conocida."""
    buses = [
        bus_structure(1, "slack", 1.0, 0, 0, 0),
        bus_structure(2, "pq", 1.0, 0, 0.5, 0),
    ]
    lines = [line_structure(1, 2, 0, 0.1, 0)]
    return buses, lines


def ejemplo3_barras():
    """Sistema de referencia de 3 barras (benchmark de regresión)."""
    buses = [
        bus_structure(1, "slack", 1.0, 0, 0, 0),
        bus_structure(2, "pq", 1.0, 0, -0.5, -0.2),
        bus_structure(3, "pv", 1.0, 0, 0.5, 0),
    ]
    lines = [
        line_structure(1, 2, 0.02, 0.1, 0.01),
        line_structure(1, 3, 0.02, 0.1, 0.01),
        line_structure(2, 3, 0.02, 0.1, 0.01),
    ]
    return buses, lines
