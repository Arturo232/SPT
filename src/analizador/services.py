"""Capa de servicios (equivalente a ``services/*.m``).

Fachadas que orquestan operaciones completas y devuelven solo datos
estructurados (contrato) más el bloque ``.meta``. Nunca lanzan errores al
usuario: capturan excepciones y devuelven una estructura de error
``{codigo, mensaje, causa}``.
"""

from types import SimpleNamespace

from .errors import construir_error
from .modules import (componentes_simetricas as cs, correccion_fp as cfp,
                      cortocircuitos as cc, circuitos as circ,
                      estabilidad as est, flujo_potencia as fp,
                      maquinas as maq, per_unit as pu,
                      potencia_compleja as pc, sistemas_trifasicos as st,
                      transformadores as tr)


def _construir_meta(modulo, tema, formulas, unidades):
    """Bloque de metadatos (procedimiento) de un resultado."""
    return SimpleNamespace(
        modulo=modulo,
        tema=tema,
        formulas=list(formulas),
        unidades=unidades,
        advertencias=[],
    )


def _es_error(result):
    return isinstance(result, dict) and "codigo" in result


# ---------------------------------------------------------------------------
def service_circuitos(mode, *args):
    """Fachada de circuitos monofásicos."""
    try:
        m = mode.lower()
        if m == "serierx":
            result = circ.solve_series_rx(*args)
            formulas = ["Z = R + jX", "|Z| = sqrt(R^2 + X^2)", "phi = atan2(X, R)"]
            tema = "Impedancia serie R-X"
        elif m == "paralelorx":
            result = circ.solve_parallel_rx(*args)
            formulas = ["Y = 1/R + 1/(jX)", "Zeq = 1/Y"]
            tema = "Impedancia paralelo R-X"
        elif m == "serie":
            result = circ.solve_series_circuit(*args)
            formulas = ["I = V/Z", "S = V*conj(I)"]
            tema = "Circuito serie (V, Z)"
        elif m == "paralelo":
            result = circ.solve_parallel_circuit(*args)
            formulas = ["Ytotal = sum(1/Zk)", "Zeq = 1/Ytotal", "I = V/Zeq"]
            tema = "Circuito paralelo (V, varias Z)"
        else:
            from .errors import error_analizador
            error_analizador("servicios", "modoDesconocido",
                             "Error: modo no valido para service_circuitos: {0}", mode)
        result.meta = _construir_meta("circuitosMonofasicos", tema, formulas,
                                      SimpleNamespace(V="V", I="A", Z="ohm", S="VA"))
    except Exception as err:
        result = construir_error(err)
    return result


def service_analizar_carga(mode, *args):
    """Fachada del módulo de potencia compleja."""
    try:
        m = mode.upper()
        if m == "VI":
            result = pc.solve_carga("VI", *args)
            formulas = ["S = V*conj(I)"]
            tema = "Potencia compleja desde V e I"
        elif m == "VZ":
            result = pc.solve_carga("VZ", *args)
            formulas = ["I = V/Z", "S = V*conj(I)"]
            tema = "Potencia compleja desde V y Z"
        elif m == "PF":
            result = pc.solve_carga("PF", *args)
            formulas = ["phi = acos(FP)", "Q = P*tan(phi) (signo segun tipo)"]
            tema = "Potencia compleja desde P, FP y tipo"
        elif m == "SUM":
            result = pc.sum_power(*args)
            formulas = ["Stotal = S1 + S2 + ... + Sn"]
            tema = "Suma de cargas"
        elif m == "SOURCE":
            p, q, v = args[0], args[1], args[2]
            i = pc.source_current(p + 1j * q, v)
            from .core import power_from_vi
            result = power_from_vi(v, i)
            formulas = ["I = conj(S/V)"]
            tema = "Corriente de la fuente"
        else:
            from .errors import error_analizador
            error_analizador("servicios", "modoDesconocido",
                             "Error: modo no valido para service_analizar_carga: {0}", mode)
        result.meta = _construir_meta(
            "potenciaCompleja", tema, formulas,
            SimpleNamespace(V="V", I="A", S="VA", P="W", Q="var"))
    except Exception as err:
        result = construir_error(err)
    return result


def service_corregir_fp(P, fp1, fp2, V, f):
    """Fachada de corrección de factor de potencia."""
    try:
        comp = cfp.required_reactive_power(P, fp1, fp2)
        corregido = cfp.corrected_power_factor(P, comp.Q1, -comp.Qc)

        result = SimpleNamespace()
        result.P = P
        result.fp1 = fp1
        result.fp2 = fp2
        result.Q1 = comp.Q1
        result.Q2 = comp.Q2
        result.Qc = comp.Qc
        result.requiereCompensacion = comp.requiereCompensacion
        result.Q_corregida = corregido.Q_new
        result.fp_corregido = corregido.fp
        result.type = corregido.type

        if abs(comp.Qc) > 1e-12:
            xc = cfp.capacitor_reactance(V, comp.Qc)
            cap = cfp.capacitor_value(f, xc.Xc)
            result.Xc = xc.Xc
            result.C_F = cap.C_F
            result.C_uF = cap.C_uF
        else:
            result.Xc = float("nan")
            result.C_F = float("nan")
            result.C_uF = float("nan")

        result.meta = _construir_meta(
            "correccionFP", "Correccion de factor de potencia",
            ["phi1 = acos(FP1)", "Q1 = P*tan(phi1)",
             "phi2 = acos(FP2)", "Q2 = P*tan(phi2)",
             "Qc = Q1 - Q2", "|Xc| = V^2/|Qc|", "C = 1/(2*pi*f*|Xc|)"],
            SimpleNamespace(P="W", Q="var", Qc="var", Xc="ohm", C="F"))
        if comp.Qc <= 1e-12:
            result.meta.advertencias.append(
                "Qc <= 0: no se requiere compensacion capacitiva.")
    except Exception as err:
        result = construir_error(err)
    return result


def service_flujo_dos_fuentes(v1mag, delta1_deg, v2mag, delta2_deg, zline):
    """Fachada del flujo de potencia entre dos fuentes."""
    try:
        result = fp.power_flow_two_bus(v1mag, delta1_deg, v2mag, delta2_deg, zline)
        result.meta = _construir_meta(
            "flujoPotencia", "Flujo de potencia entre dos fuentes",
            ["I12 = (V1 - V2)/Zline", "S12 = V1*conj(I12)",
             "P12 = real(S12)", "Q12 = imag(S12)"],
            SimpleNamespace(V="V", I="A", S="VA", Z="ohm"))
    except Exception as err:
        result = construir_error(err)
    return result


def service_trifasico_carga(VL, conexion, zfase):
    """Fachada de la carga trifásica balanceada."""
    try:
        result = st.solve_three_phase_load(VL, conexion, zfase)
        result.meta = _construir_meta(
            "sistemasTrifasicos", "Carga trifasica balanceada",
            ["Vf = VL/sqrt(3) (Y) o Vf = VL (Delta)",
             "If = Vf / Zfase",
             "S3f = 3 * Vf * conj(If)"],
            SimpleNamespace(V="V", I="A", Z="ohm", S="VA"))
    except Exception as err:
        result = construir_error(err)
    return result


def service_per_unit(sbase, vbase, fases, valor=None, tipo=None):
    """Fachada del sistema por unidad."""
    try:
        base = pu.per_unit_base(sbase, vbase, fases)
        result = SimpleNamespace()
        result.base = base
        if valor is not None and tipo is not None:
            result.tipo = tipo.upper()
            result.valor_real = valor
            result.valor_pu = pu.to_per_unit(valor, base, tipo.upper())
        result.meta = _construir_meta(
            "perUnit", "Sistema por unidad",
            ["Zbase = Vbase^2 / Sbase",
             "Ibase = Sbase / (sqrt(3)*Vbase)  (trifasico)",
             "Xpu = X / Xbase"],
            SimpleNamespace(S="VA", V="V", I="A", Z="ohm"))
    except Exception as err:
        result = construir_error(err)
    return result


def service_transformador(V1, N1, N2, zsecundario):
    """Fachada del transformador ideal + impedancia referida."""
    try:
        ideal = tr.ideal_transformer(V1, N1, N2)
        result = ideal
        result.Zsecundario = zsecundario
        result.Zprimario_ref = tr.transformer_equivalent(ideal.a, zsecundario, "primario")
        result.meta = _construir_meta(
            "transformadores", "Transformador ideal + impedancia referida",
            ["a = N1/N2", "V2 = V1/a", "Z' = a^2 * Zsecundario"],
            SimpleNamespace(V="V", Z="ohm"))
    except Exception as err:
        result = construir_error(err)
    return result


def service_flujo_carga(buses, lines, metodo="nr", tol=None):
    """Fachada del flujo de carga N-barras."""
    try:
        m = metodo.lower()
        if m in ("nr", "newton", "newtonraphson"):
            if tol is not None:
                res = fp.newton_raphson_power_flow(buses, lines, tol)
            else:
                res = fp.newton_raphson_power_flow(buses, lines)
            nombre = "Newton-Raphson"
        elif m in ("gs", "gauss", "gaussseidel"):
            if tol is not None:
                res = fp.gauss_seidel_power_flow(buses, lines, tol)
            else:
                res = fp.gauss_seidel_power_flow(buses, lines)
            nombre = "Gauss-Seidel"
        else:
            from .errors import error_analizador
            error_analizador("servicios", "modoDesconocido",
                             "Error: metodo no valido para service_flujo_carga: {0}", metodo)
        result = res
        result.metodo = nombre
        result.meta = _construir_meta(
            "flujoPotencia", "Flujo de carga N-barras",
            ["Ybus: Y_ii = sum(y) + jB/2, Y_ij = -y",
             "P_i = V_i*sum V_j(G cos + B sin)",
             "Q_i = V_i*sum V_j(G sin - B cos)"],
            SimpleNamespace(V="pu", S="pu", Z="pu"))
    except Exception as err:
        result = construir_error(err)
    return result


def service_componentes_simetricas(mode, x):
    """Fachada de la transformación de componentes simétricas."""
    try:
        import numpy as np
        m = mode.lower()
        if m in ("abc012", "abc->012", "abca012"):
            result = SimpleNamespace()
            result.xabc = np.asarray(x).flatten()
            result.seq = cs.abc_to_sequence(x)
            formulas = ["X0 = (Xa+Xb+Xc)/3",
                        "X1 = (Xa + a*Xb + a^2*Xc)/3",
                        "X2 = (Xa + a^2*Xb + a*Xc)/3"]
            tema = "Componentes de secuencia (abc -> 012)"
        elif m in ("012abc", "012->abc"):
            result = SimpleNamespace()
            result.seq = np.asarray(x).flatten()
            result.xabc = cs.sequence_to_abc(x)
            formulas = ["Xa = X0+X1+X2", "Xb = X0 + a^2*X1 + a*X2",
                        "Xc = X0 + a*X1 + a^2*X2"]
            tema = "Componentes de fase (012 -> abc)"
        else:
            from .errors import error_analizador
            error_analizador("servicios", "modoDesconocido",
                             "Error: modo no valido para service_componentes_simetricas: {0}", mode)
        result.meta = _construir_meta("componentesSimetricas", tema, formulas, SimpleNamespace())
    except Exception as err:
        result = construir_error(err)
    return result


def service_cortocircuito(tipo, Vf, Z1, Z2, Z0=None, Zf=0):
    """Fachada del módulo de cortocircuitos."""
    try:
        t = tipo.lower()
        if t in ("3f", "trifasica", "trifasico"):
            result = cc.three_phase_fault_current(Vf, Z1)
            result.meta = _construir_meta(
                "cortocircuitos", "Falla trifasica balanceada",
                ["If = Vf / Zth"], SimpleNamespace(I="A", V="V", Z="ohm"))
            return result
        if t in ("slg", "monofasica", "linea-tierra"):
            result = cc.single_line_to_ground_fault(Vf, Z1, Z2, Z0, Zf)
            formulas = ["I1 = Vf/(Z1+Z2+Z0+3*Zf)", "I0=I2=I1", "If = 3*I1"]
        elif t in ("ll", "linea-linea"):
            result = cc.line_to_line_fault(Vf, Z1, Z2, Zf)
            formulas = ["I1 = Vf/(Z1+Z2+Zf)", "I2 = -I1", "Ib = (a^2-a)*I1"]
        elif t in ("llg", "doble-linea-tierra"):
            result = cc.double_line_to_ground_fault(Vf, Z1, Z2, Z0, Zf)
            formulas = ["Zp = Z2*(Z0+3Zf)/(Z2+Z0+3Zf)", "I1 = Vf/(Z1+Zp)"]
        else:
            from .errors import error_analizador
            error_analizador("servicios", "modoDesconocido",
                             "Error: tipo de falla no reconocido: {0}", tipo)
        result.meta = _construir_meta("cortocircuitos", "Falla " + result.tipo,
                                      formulas, SimpleNamespace(I="A", V="V", Z="ohm"))
    except Exception as err:
        result = construir_error(err)
    return result


def service_maquina_sincrona(mode, *args):
    """Fachada del módulo de máquinas eléctricas (generador síncrono)."""
    try:
        m = mode.lower()
        if m in ("fem", "emf"):
            result = maq.sync_generator_emf(*args)
            formulas = ["E = V + I*(Ra + jXs)"]
            tema = "FEM interna del generador sincrono"
        elif m in ("potencia", "pdelta", "curva"):
            result = maq.power_angle_curve(*args)
            formulas = ["P = E*V/Xs * sin(delta)", "Pmax = E*V/Xs"]
            tema = "Curva potencia-angulo"
        else:
            from .errors import error_analizador
            error_analizador("servicios", "modoDesconocido",
                             "Error: modo no valido para service_maquina_sincrona: {0}", mode)
        result.meta = _construir_meta("maquinasElectricas", tema, formulas,
                                      SimpleNamespace(V="V", I="A", Z="ohm", P="W"))
    except Exception as err:
        result = construir_error(err)
    return result


def service_estabilidad(Pm, Pmax, PmaxFalla, H, f):
    """Fachada del módulo de estabilidad (criterio de áreas iguales)."""
    try:
        ea = est.equal_area_criterion(Pm, Pmax, PmaxFalla)
        tc = est.critical_clearing_time(Pm, ea.delta0_deg, ea.deltaCr_deg, H, f)

        result = SimpleNamespace()
        result.Pm = Pm
        result.Pmax = Pmax
        result.Pmax_falla = PmaxFalla
        result.delta0_deg = ea.delta0_deg
        result.deltaCr_deg = ea.deltaCr_deg
        result.deltaMax_deg = ea.deltaMax_deg
        result.A1 = ea.A1
        result.A2 = ea.A2
        result.tcr = tc.tcr
        result.meta = _construir_meta(
            "estabilidad", "Estabilidad transitoria (areas iguales)",
            ["delta0 = asin(Pm/Pmax)",
             "A1 = integral(Pm - PmaxFalla*sin)",
             "A2 = integral(Pmax*sin - Pm)",
             "tcr = sqrt(2*(deltaCr-delta0)*2H/(Pm*omega_s))"],
            SimpleNamespace(P="pu", t="s", angulo="grados"))
    except Exception as err:
        result = construir_error(err)
    return result
