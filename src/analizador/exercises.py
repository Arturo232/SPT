"""Ejercicios del taller 2026 y ejemplos reproducibles.

Equivalente a ``exercises/workshop2026/*.m`` y ``exercises/examples/*.m``.
Cada ejercicio solo consume funciones generales (core/módulos) y no tiene
respuestas hardcodeadas.
"""

from .core import (admittance_from_impedance, current_from_power,
                   impedance_from_admittance, impedance_from_power,
                   power_factor, power_from_vi, rad2deg)
from .modules.correccion_fp import (capacitor_kvar, capacitor_reactance,
                                    capacitor_value, corrected_power_factor,
                                    required_reactive_power)
from .modules.potencia_compleja import (load_power_from_z, solve_carga,
                                        source_current, sum_power)
from .modules.circuitos import solve_series_rx
from .utils import print_results


def exercise01():
    """Taller 2026 - Ejercicio 1: carga serie R-X (V=480, P=250kW, FP=0.9)."""
    V = 480
    P = 250e3
    fp = 0.9

    carga = solve_carga("PF", P, fp, "inductiva")
    z = impedance_from_power(V, carga.S)
    serie = solve_series_rx(round(float(__import__("numpy").real(z)), 10),
                            round(float(__import__("numpy").imag(z)), 10))

    result = {
        "V": V, "P": P, "fp": fp, "Q": carga.Q, "S": carga.S,
        "Z": z, "R": float(__import__("numpy").real(z)),
        "X": float(__import__("numpy").imag(z)),
        "Zmag": serie.Zmag, "angleDeg": serie.angleDeg,
    }
    print("\n=== EJERCICIO 1: CARGA SERIE R-X ===")
    print("V = %g Vrms, P = %g kW, FP = %g atrasado" % (V, P / 1e3, fp))
    print("Q = %g var" % carga.Q)
    print_results(result)
    return result


def exercise02():
    """Taller 2026 - Ejercicio 2: carga paralelo R-X (via admitancias)."""
    V = 480
    P = 250e3
    fp = 0.9

    carga = solve_carga("PF", P, fp, "inductiva")
    y_equivalente = __import__("numpy").conjugate(carga.S) / (V ** 2)
    z_equivalente = impedance_from_admittance(y_equivalente)

    import numpy as np
    result = {
        "V": V, "P": P, "fp": fp, "Q": carga.Q, "S": carga.S,
        "Yeq": y_equivalente, "Zeq": z_equivalente,
        "R": float(np.real(z_equivalente)), "X": float(np.imag(z_equivalente)),
        "Zmag": abs(z_equivalente), "angleDeg": rad2deg(np.angle(z_equivalente)),
    }
    print("\n=== EJERCICIO 2: CARGA PARALELO R-X ===")
    print("V = %g Vrms, P = %g kW, FP = %g atrasado" % (V, P / 1e3, fp))
    print("Yeq = %g + j%g S" % (np.real(y_equivalente), np.imag(y_equivalente)))
    print_results(result)
    return result


def exercise03():
    """Taller 2026 - Ejercicio 3: dos cargas (total 35kW/FP 0.85, S2)."""
    V = 127
    ptotal = 35e3
    fptotal = 0.85
    P1 = 25e3
    fp1 = 0.95

    stotal = solve_carga("PF", ptotal, fptotal, "inductiva")
    s1 = solve_carga("PF", P1, fp1, "capacitiva")
    s2 = sum_power(stotal.S, -s1.S)

    import numpy as np
    result = {
        "V": V, "Ptotal": ptotal, "fptotal": fptotal, "Qt": stotal.Q,
        "Stotal": stotal.S, "P1": P1, "fp1": fp1, "Q1": s1.Q, "S1": s1.S,
        "S2": s2.S, "P2": s2.P, "Q2": s2.Q,
    }
    print("\n=== EJERCICIO 3: DOS CARGAS ===")
    print("V = %g Vrms, Ptot = %g kW, FPtot = %g atrasado"
          % (V, ptotal / 1e3, fptotal))
    print("Qt = %g var" % stotal.Q)
    print("Carga 1: P1 = %g kW, FP1 = %g ADELANTADO -> Q1 = %g var"
          % (P1 / 1e3, fp1, s1.Q))
    print("Por ser ADELANTADA, la carga 1 tiene Q < 0 (comportamiento capacitivo).")
    print_results(result)
    return result


def exercise04():
    """Taller 2026 - Ejercicio 4: R paralelo capacitor + linea.

    Se adopta ``Zline = 8.4 + j11.2 ohm`` (interpretación documentada).
    """
    import numpy as np
    vload = 1200
    s_abs = 800e3
    fp = 0.8
    z_linea = 8.4 + 1j * 11.2

    carga = solve_carga("PF", s_abs * fp, fp, "capacitiva")
    i_load = current_from_power(carga.S, vload)

    y = np.conjugate(carga.S) / (vload ** 2)
    r = 1 / np.real(y)
    xc = -1 / np.imag(y)

    v_fuente = vload + i_load * z_linea

    result = {
        "Vload": vload, "Pload": carga.P, "Qload": carga.Q, "Sload": carga.S,
        "Iload": i_load, "Zline": z_linea, "R": float(r), "Xc": float(xc),
        "Vfuente": v_fuente,
    }
    print("\n=== EJERCICIO 4: R PARALELO CAPACITOR + LINEA ===")
    print("Vload = %g Vrms, |S| = %g kVA, FP = %g ADELANTADO"
          % (vload, s_abs / 1e3, fp))
    print_results(result)
    return result


def exercise05():
    """Taller 2026 - Ejercicio 5: dos cargas + motor + correccion FP=1."""
    import numpy as np
    V = 200
    f = 60
    z1 = 0.8 + 1j * 5.6
    z2 = 8 - 1j * 16
    s3mag = 5e3
    fp3 = 0.8

    s1 = load_power_from_z(V, z1)
    s2 = load_power_from_z(V, z2)
    s3 = solve_carga("PF", s3mag * fp3, fp3, "inductiva")
    stotal = sum_power(s1, s2, s3)

    i_fuente = source_current(stotal.S, V)
    fp_global = stotal.fp

    comp = required_reactive_power(stotal.P, fp_global, 1)
    x_cap = capacitor_reactance(V, comp.Qc)
    cap = capacitor_value(f, x_cap.Xc)

    i_nueva = source_current(stotal.P + 0j, V)
    s_corregido = stotal.P + 0j

    result = {
        "V": V, "f": f, "S1": s1.S, "S2": s2.S, "S3": s3.S,
        "Stotal": stotal.S, "I": i_fuente, "fp": fp_global,
        "Qc": -comp.Qc, "Qc_kvar": capacitor_kvar(comp.Qc),
        "Xc": x_cap.Xc, "C_F": cap.C_F, "C_uF": cap.C_uF,
        "Inew": i_nueva, "fp_corregido": power_factor(s_corregido).fp,
    }
    print("\n=== EJERCICIO 5: DOS CARGAS + MOTOR + CORRECCION ===")
    print("V = %g Vrms, f = %g Hz" % (V, f))
    print("Z1 = %g + j%g ohm, Z2 = %g %+gj ohm, Motor S = %g kVA FP = %g"
          % (np.real(z1), np.imag(z1), np.real(z2), np.imag(z2),
             s3mag / 1e3, fp3))
    print_results(result)
    print("FP corregido = %g" % result["fp_corregido"])
    return result


EXERCICIOS = {
    1: exercise01,
    2: exercise02,
    3: exercise03,
    4: exercise04,
    5: exercise05,
}


def menu_ejercicios():
    """Menú interactivo de los ejercicios del taller 2026."""
    from .utils import input_helpers
    print("\n===== EJERCICIOS DEL TALLER 2026 =====")
    opcion = input_helpers("choice", "Seleccione ejercicio:", [
        "Ejercicio 1: carga serie R-X",
        "Ejercicio 2: carga paralelo R-X",
        "Ejercicio 3: dos cargas",
        "Ejercicio 4: R paralelo capacitor + linea",
        "Ejercicio 5: cargas + motor + correccion",
    ])
    EXERCICIOS[opcion]()


def example_base():
    """Ejemplo reproducible: dos cargas en paralelo (V = 200 V)."""
    V = 200
    z1 = 100
    z2 = 10 + 20j

    s1 = load_power_from_z(V, z1)
    s2 = load_power_from_z(V, z2)
    stotal = sum_power(s1, s2)
    i_total = source_current(stotal.S, V)

    print("\n=== EJEMPLO: DOS CARGAS EN PARALELO ===")
    print("V = %g angulo 0 V" % V)
    print("Z1 = 100 + j0 ohm")
    print("Z2 = 10 + j20 ohm\n")
    print("Carga 1:")
    print_results(s1)
    print("Carga 2:")
    print_results(s2)
    print("Total:")
    print_results(stotal)
    print("Corriente total:")
    print_results(power_from_vi(V, i_total))


def example_fp_correction():
    """Ejemplo reproducible: corrección de FP (0.6 -> 0.8)."""
    import numpy as np
    P = 1200
    fp1 = 0.6
    fp2 = 0.8
    V = 200
    f = 60

    comp = required_reactive_power(P, fp1, fp2)
    xc = capacitor_reactance(V, comp.Qc)
    cap = capacitor_value(f, xc.Xc)
    corregido = corrected_power_factor(P, comp.Q1, -comp.Qc)

    print("\n=== EJEMPLO: CORRECCION DE FP ===")
    print("P = %g W, FP inicial = %g, FP objetivo = %g\n" % (P, fp1, fp2))
    print("  Q1 = %g var" % comp.Q1)
    print("  Q2 = %g var" % comp.Q2)
    print("  Qc = %g var (%g kvar)" % (comp.Qc, capacitor_kvar(comp.Qc)))
    print("  |Xc| = %g ohm" % xc.Xc)
    print("  C    = %g uF" % cap.C_uF)
    print("  FP despues = %g (%s)" % (corregido.fp, corregido.type))


def menu_ejemplos():
    """Menú interactivo de ejemplos reproducibles."""
    from .utils import input_helpers
    print("\n===== EJEMPLOS =====")
    opcion = input_helpers("choice", "Seleccione ejemplo:", [
        "Dos cargas en paralelo (V = 200 V)",
        "Correccion de FP (0.6 -> 0.8)",
    ])
    if opcion == 1:
        example_base()
    else:
        example_fp_correction()
