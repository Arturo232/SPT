"""Menús interactivos de cada módulo (equivalente a ``modules/*/menu*.m``).

Consumen exclusivamente la capa de servicios y las funciones de presentación.
"""

from .core import polar_to_complex
from .modules.correccion_fp import capacitor_kvar
from .modules.flujo_potencia import (bus_structure, caso2_barras,
                                     ejemplo3_barras, line_structure)
from .modules.per_unit import change_of_base, from_per_unit, per_unit_base
from .modules.sistemas_trifasicos import (delta_to_wye, wye_to_delta,
                                          three_phase_power_from_line)
from .modules.transformadores import (ideal_transformer, three_phase_transformer,
                                      transformer_equivalent,
                                      transformer_loss_efficiency, voltage_regulation)
from .services import (service_analizar_carga, service_circuitos,
                       service_componentes_simetricas, service_corregir_fp,
                       service_cortocircuito, service_estabilidad,
                       service_flujo_carga, service_flujo_dos_fuentes,
                       service_maquina_sincrona, service_per_unit,
                       service_transformador, service_trifasico_carga)
from .utils import input_helpers, print_complex, print_results


def _print_complejo(z):
    print_complex(z)


def _es_error(result):
    return isinstance(result, dict) and "codigo" in result


def menu_circuitos():
    print("\n===== CIRCUITOS MONOFASICOS =====")
    opcion = input_helpers("choice", "Que desea calcular?", [
        "Impedancia serie R-X",
        "Impedancia paralelo R-X",
        "Resolver circuito serie (V, Z)",
        "Resolver circuito paralelo (V, varias Z)",
    ])
    if opcion == 1:
        r = input_helpers("positive", "R (ohm): ")
        x = input_helpers("number", "X (ohm): ")
        result = service_circuitos("serierx", r, x)
    elif opcion == 2:
        r = input_helpers("positive", "R (ohm): ")
        x = input_helpers("number", "X (ohm, distinto de 0): ")
        result = service_circuitos("paralelorx", r, x)
    elif opcion == 3:
        v = input_helpers("complex", "Tension V:")
        r = input_helpers("positive", "R (ohm): ")
        x = input_helpers("number", "X (ohm): ")
        result = service_circuitos("serie", v, r + 1j * x)
    else:
        v = input_helpers("complex", "Tension V:")
        n = int(round(input_helpers("positive", "Numero de ramas en paralelo: ")))
        zs = []
        for k in range(1, n + 1):
            r = input_helpers("positive", "R%d (ohm): " % k)
            x = input_helpers("number", "X%d (ohm): " % k)
            zs.append(r + 1j * x)
        result = service_circuitos("paralelo", v, *zs)
    print_results(result)


def menu_potencia_compleja():
    print("\n===== POTENCIA COMPLEJA =====")
    opcion = input_helpers("choice", "Flujo de calculo:", [
        "Desde V e I",
        "Desde V y Z",
        "Desde P, FP y tipo de carga",
        "Sumar cargas",
        "Corriente de la fuente",
    ])
    if opcion == 1:
        v = input_helpers("complex", "Tension V:")
        i = input_helpers("complex", "Corriente I:")
        result = service_analizar_carga("VI", v, i)
    elif opcion == 2:
        v = input_helpers("complex", "Tension V:")
        r = input_helpers("number", "R (ohm): ")
        x = input_helpers("number", "X (ohm): ")
        result = service_analizar_carga("VZ", v, r + 1j * x)
    elif opcion == 3:
        p = input_helpers("number", "P (W): ")
        fp = input_helpers("fp", "FP (0-1): ")
        tipo = input_helpers("choice", "Tipo de carga:", [
            "Inductiva (atraso)", "Capacitiva (adelanto)", "Resistiva"])
        tipos = ["inductiva", "capacitiva", "resistiva"]
        result = service_analizar_carga("PF", p, fp, tipos[tipo - 1])
    elif opcion == 4:
        n = int(round(input_helpers("positive", "Numero de cargas: ")))
        ss = []
        for k in range(1, n + 1):
            p = input_helpers("number", "P%d (W): " % k)
            q = input_helpers("number", "Q%d (var): " % k)
            ss.append(p + 1j * q)
        result = service_analizar_carga("SUM", *ss)
    else:
        p = input_helpers("number", "P total (W): ")
        q = input_helpers("number", "Q total (var): ")
        v = input_helpers("complex", "Tension V:")
        result = service_analizar_carga("SOURCE", p, q, v)

    print_results(result)

    if input_helpers("choice", "Exportar resultados?", ["No", "Si"]) == 2:
        from .utils import export_results
        formato = input_helpers("choice", "Formato:", ["TXT", "JSON", "CSV", "Excel"])
        formatos = ["txt", "json", "csv", "xlsx"]
        nombre = input("  Archivo (sin extension): ").strip()
        archivo = export_results(result, nombre, formatos[formato - 1])
        print("  Exportado: %s" % archivo)


def menu_correccion_fp():
    print("\n===== CORRECCION DE FACTOR DE POTENCIA =====")
    p = input_helpers("positive", "P (W): ")
    fp1 = input_helpers("fp", "FP inicial (0-1): ")
    fp2 = input_helpers("fp", "FP objetivo (0-1): ")
    v = input_helpers("positive", "V (Vrms): ")
    f = input_helpers("frequency", "f (Hz): ")

    result = service_corregir_fp(p, fp1, fp2, v, f)

    if _es_error(result):
        print("\nERROR\n  %s" % result["mensaje"])
        return

    print("\n  Q1 = %g var" % result.Q1)
    print("  Q2 = %g var" % result.Q2)
    print("  Qc = %g var  (%g kvar)" % (result.Qc, capacitor_kvar(result.Qc)))
    print("  Compensacion requerida: %s" % result.requiereCompensacion.upper())

    if result.Qc > 1e-12:
        print("  |Xc| = %g ohm" % result.Xc)
        print("  C    = %g F = %g uF" % (result.C_F, result.C_uF))
    print("  FP corregido = %g (%s)" % (result.fp_corregido, result.type))
    print("  Q nueva      = %g var" % result.Q_corregida)

    print_results(result)


def menu_flujo_potencia():
    print("\n===== FLUJO DE POTENCIA (DOS FUENTES) =====")
    v1m = input_helpers("positive", "V1 (magnitud): ")
    d1 = input_helpers("number", "delta1 (grados): ")
    v2m = input_helpers("positive", "V2 (magnitud): ")
    d2 = input_helpers("number", "delta2 (grados): ")
    rl = input_helpers("number", "R de la linea (ohm): ")
    xl = input_helpers("number", "X de la linea (ohm): ")

    result = service_flujo_dos_fuentes(v1m, d1, v2m, d2, rl + 1j * xl)
    print_results(result)


def menu_trifasico():
    print("\n===== SISTEMAS TRIFASICOS =====")
    opcion = input_helpers("choice", "Que desea calcular?", [
        "Carga trifasica balanceada (Y o Delta)",
        "Transformar impedancia Delta <-> Y",
        "Potencia trifasica desde valores de linea",
    ])
    if opcion == 1:
        v_l = input_helpers("positive", "Tension de linea VL (V): ")
        conexion = input_helpers("choice", "Conexion:", ["Estrella (Y)", "Delta"])
        conexiones = ["Y", "Delta"]
        r = input_helpers("number", "R de la impedancia por fase (ohm): ")
        x = input_helpers("number", "X de la impedancia por fase (ohm): ")
        result = service_trifasico_carga(v_l, conexiones[conexion - 1], r + 1j * x)
    elif opcion == 2:
        modo = input_helpers("choice", "Transformacion:", ["Delta -> Y", "Y -> Delta"])
        r = input_helpers("number", "R (ohm): ")
        x = input_helpers("number", "X (ohm): ")
        z = r + 1j * x
        result = {}
        if modo == 1:
            result["Zdelta"] = z
            result["ZY"] = delta_to_wye(z)
        else:
            result["ZY"] = z
            result["Zdelta"] = wye_to_delta(z)
    else:
        v_l = input_helpers("positive", "VL (V): ")
        i_l = input_helpers("positive", "IL (A): ")
        phi = input_helpers("number", "Angulo del FP (grados): ")
        result = three_phase_power_from_line(v_l, i_l, phi)

    print_results(result)


def menu_per_unit():
    print("\n===== SISTEMA POR UNIDAD (P.U.) =====")
    sbase = input_helpers("positive", "Sbase (VA): ")
    vbase = input_helpers("positive", "Vbase (V): ")
    fases = input_helpers("choice", "Numero de fases:", ["Monofasico", "Trifasico"])
    fases_txt = ["monofasico", "trifasico"]
    base = per_unit_base(sbase, vbase, fases_txt[fases - 1])

    print("\n  Ibase = %g A" % base.Ibase)
    print("  Zbase = %g ohm" % base.Zbase)
    print("  Ybase = %g S" % base.Ybase)

    opcion = input_helpers("choice", "Que desea hacer?", [
        "Convertir un valor real a p.u.",
        "Convertir de p.u. a valor real",
        "Cambio de base de impedancia",
    ])
    tipos = ["V", "I", "S", "Z"]
    if opcion == 1:
        tipo = input_helpers("choice", "Tipo de magnitud:", [
            "Tension (V)", "Corriente (I)", "Potencia (S)", "Impedancia (Z)"])
        valor = input_helpers("number", "Valor real: ")
        result = service_per_unit(sbase, vbase, fases_txt[fases - 1], valor, tipos[tipo - 1])
    elif opcion == 2:
        tipo = input_helpers("choice", "Tipo de magnitud:", [
            "Tension (V)", "Corriente (I)", "Potencia (S)", "Impedancia (Z)"])
        pu_val = input_helpers("number", "Valor en p.u.: ")
        result = {"tipo": tipos[tipo - 1], "valor_pu": pu_val,
                  "valor_real": from_per_unit(pu_val, base, tipos[tipo - 1])}
    else:
        sb_vieja = input_helpers("positive", "Sbase vieja (VA): ")
        vb_vieja = input_helpers("positive", "Vbase vieja (V): ")
        sb_nueva = input_helpers("positive", "Sbase nueva (VA): ")
        vb_nueva = input_helpers("positive", "Vbase nueva (V): ")
        zpu = input_helpers("number", "Z en p.u. (base vieja): ")
        result = {"zpu_viejo": zpu,
                  "zpu_nuevo": change_of_base(zpu, sb_vieja, vb_vieja, sb_nueva, vb_nueva)}

    print_results(result)


def menu_transformador():
    print("\n===== TRANSFORMADORES =====")
    opcion = input_helpers("choice", "Que desea calcular?", [
        "Transformador ideal (V1, N1, N2)",
        "Referir impedancia a un lado",
        "Regulacion de tension",
        "Eficiencia",
        "Impedancia en p.u. (cambio de base)",
        "Transformador trifasico (conexiones)",
    ])
    if opcion == 1:
        v1 = input_helpers("positive", "V1 (V): ")
        n1 = input_helpers("positive", "N1 (espiras): ")
        n2 = input_helpers("positive", "N2 (espiras): ")
        op = input_helpers("choice", "Incluir corriente I1?", ["No", "Si"])
        if op == 1:
            result = ideal_transformer(v1, n1, n2)
        else:
            i1 = input_helpers("number", "I1 (A): ")
            result = ideal_transformer(v1, n1, n2, i1)
    elif opcion == 2:
        a = input_helpers("number", "Relacion a = N1/N2: ")
        r = input_helpers("number", "R de la impedancia (ohm): ")
        x = input_helpers("number", "X de la impedancia (ohm): ")
        lado = input_helpers("choice", "Lado al que referir:", ["Primario", "Secundario"])
        lados = ["primario", "secundario"]
        result = {"Z": r + 1j * x, "lado": lados[lado - 1],
                  "Zref": transformer_equivalent(a, r + 1j * x, lados[lado - 1])}
    elif opcion == 3:
        vsc = input_helpers("number", "V2 sin carga (V): ")
        vpc = input_helpers("number", "V2 a plena carga (V): ")
        result = {"reg": voltage_regulation(vsc, vpc)}
    elif opcion == 4:
        pout = input_helpers("positive", "Pout (W): ")
        ploss = input_helpers("positive", "Perdidas (W): ")
        result = transformer_loss_efficiency(pout, ploss)
    elif opcion == 5:
        zpu = input_helpers("number", "Z en p.u. (base del transformador): ")
        sbt = input_helpers("positive", "Sbase transformador (VA): ")
        vbt = input_helpers("positive", "Vbase transformador (V): ")
        sbs = input_helpers("positive", "Sbase sistema (VA): ")
        vbs = input_helpers("positive", "Vbase sistema (V): ")
        from .modules.transformadores import per_unit_transformer
        result = per_unit_transformer(zpu, sbt, vbt, sbs, vbs)
    else:
        a = input_helpers("number", "Relacion a = N1/N2: ")
        c1 = input_helpers("choice", "Conexion primario:", ["Estrella (Y)", "Delta"])
        c2 = input_helpers("choice", "Conexion secundario:", ["Estrella (Y)", "Delta"])
        conexiones = ["Y", "Delta"]
        result = three_phase_transformer(a, conexiones[c1 - 1], conexiones[c2 - 1])

    print_results(result)


def menu_flujo_carga():
    print("\n===== FLUJO DE CARGA N-BARRAS =====")
    metodo = input_helpers("choice", "Metodo:", ["Newton-Raphson", "Gauss-Seidel"])
    metodos = ["nr", "gs"]
    sistema = input_helpers("choice", "Sistema:", [
        "3 barras (benchmark de regresion)", "2 barras (solucion analitica)"])

    if sistema == 1:
        buses, lines = ejemplo3_barras()
        nombre = "Sistema de 3 barras"
    else:
        buses, lines = caso2_barras()
        nombre = "Sistema de 2 barras"

    result = service_flujo_carga(buses, lines, metodos[metodo - 1])

    if _es_error(result):
        print("\nERROR\n  %s" % result["mensaje"])
        return

    print("\n")
    print("Sistema: %s  |  Metodo: %s" % (nombre, result.metodo))
    print("Convergio: %s  |  Iteraciones: %d"
          % ("SI" if result.converged else "NO", result.iterations))
    print("Perdidas totales: %g pu" % result.perdidas)

    print("\n%-6s %-6s %-12s %-12s %-12s %-12s" %
          ("Barra", "Tipo", "V (pu)", "delta (deg)", "P (pu)", "Q (pu)"))
    for k, bus in enumerate(buses, start=1):
        print("%-6d %-6s %-12.4f %-12.4f %-12.4f %-12.4f" % (
            k, bus.type, result.V[k - 1], result.delta_deg[k - 1],
            bus.P, bus.Q))
    print("\nPotencia de la barra slack: P = %g pu, Q = %g pu"
          % (result.Pslack, result.Qslack))


def menu_componentes():
    print("\n===== COMPONENTES SIMETRICAS =====")
    modo = input_helpers("choice", "Transformacion:", [
        "abc -> 012 (secuencia)", "012 -> abc (fase)"])

    nombres = ["Xa", "Xb", "Xc"] if modo == 1 else ["X0", "X1", "X2"]
    x = []
    for k in range(3):
        mag = input_helpers("positive", "%s (magnitud): " % nombres[k])
        ang = input_helpers("number", "%s (angulo, grados): " % nombres[k])
        x.append(polar_to_complex(mag, ang))

    if modo == 1:
        result = service_componentes_simetricas("abc012", x)
        print("\nSecuencia:")
        for i, label in enumerate(["X0", "X1", "X2"], start=1):
            print("  %s = " % label, end="")
            _print_complejo(result.seq[i - 1])
    else:
        result = service_componentes_simetricas("012abc", x)
        print("\nFases:")
        for i, label in enumerate(["Xa", "Xb", "Xc"], start=1):
            print("  %s = " % label, end="")
            _print_complejo(result.xabc[i - 1])


def menu_cortocircuito():
    print("\n===== CORTOCIRCUITOS =====")
    tipo = input_helpers("choice", "Tipo de falla:", [
        "Trifasica balanceada", "Linea a tierra (SLG)",
        "Linea-linea (LL)", "Dos lineas a tierra (LLG)"])

    vf_mag = input_helpers("positive", "Vf (magnitud de prefalla): ")
    vf_ang = input_helpers("number", "Vf (angulo, grados): ")
    vf = polar_to_complex(vf_mag, vf_ang)

    z1 = _input_complejo("Z1 (secuencia positiva, R + jX): ")
    z2 = _input_complejo("Z2 (secuencia negativa, R + jX): ")

    if tipo == 1:
        result = service_cortocircuito("3f", vf, z1, z2)
    elif tipo == 2:
        z0 = _input_complejo("Z0 (secuencia cero, R + jX): ")
        zf = _input_complejo("Zf (impedancia de falla, R + jX): ")
        result = service_cortocircuito("slg", vf, z1, z2, z0, zf)
    elif tipo == 3:
        zf = _input_complejo("Zf (impedancia de falla, R + jX): ")
        result = service_cortocircuito("ll", vf, z1, z2, zf)
    else:
        z0 = _input_complejo("Z0 (secuencia cero, R + jX): ")
        zf = _input_complejo("Zf (impedancia de falla, R + jX): ")
        result = service_cortocircuito("llg", vf, z1, z2, z0, zf)

    if _es_error(result):
        print("\nERROR\n  %s" % result["mensaje"])
        return

    print("\nFalla: %s" % result.tipo)
    if hasattr(result, "I0"):
        print("  I0 = ", end="")
        _print_complejo(result.I0)
        print("  I1 = ", end="")
        _print_complejo(result.I1)
        print("  I2 = ", end="")
        _print_complejo(result.I2)
    if hasattr(result, "Ia"):
        print("  Ia = ", end="")
        _print_complejo(result.Ia)
        print("  Ib = ", end="")
        _print_complejo(result.Ib)
        print("  Ic = ", end="")
        _print_complejo(result.Ic)
    print("  |If| = %g" % result.If_mag)


def _input_complejo(prompt):
    print(prompt)
    r = input_helpers("number", "  R (ohm): ")
    x = input_helpers("number", "  X (ohm): ")
    return r + 1j * x


def menu_maquinas():
    print("\n===== MAQUINAS ELECTRICAS (GENERADOR SINCRONO) =====")
    opcion = input_helpers("choice", "Que desea calcular?", [
        "FEM interna (E = V + I*(Ra + jXs))",
        "Curva potencia-angulo (P = E*V/Xs*sin(delta))",
    ])
    if opcion == 1:
        v = input_helpers("complex", "Tension terminal V:")
        i = input_helpers("complex", "Corriente I:")
        xs = input_helpers("positive", "Xs (ohm): ")
        ra = input_helpers("number", "Ra (ohm, 0 si se omite): ")
        result = service_maquina_sincrona("fem", v, i, xs, ra)
    else:
        e = input_helpers("positive", "E (magnitud): ")
        v = input_helpers("positive", "V (magnitud): ")
        xs = input_helpers("positive", "Xs (ohm): ")
        delta = input_helpers("number", "delta (grados): ")
        result = service_maquina_sincrona("potencia", e, v, xs, delta)

    print_results(result)


def menu_estabilidad():
    print("\n===== ESTABILIDAD (AREAS IGUALES) =====")
    pm = input_helpers("positive", "Pm (potencia mecanica, pu): ")
    p_max = input_helpers("positive", "Pmax post-falla (pu): ")
    p_falla = input_helpers("number", "Pmax durante la falla (pu, 0 en bornes): ")
    h = input_helpers("positive", "H (constante de inercia, s): ")
    f = input_helpers("frequency", "f (Hz): ")

    result = service_estabilidad(pm, p_max, p_falla, h, f)

    if _es_error(result):
        print("\nERROR\n  %s" % result["mensaje"])
        return

    print("\n  delta0  = %.4f deg" % result.delta0_deg)
    print("  deltaCr = %.4f deg" % result.deltaCr_deg)
    print("  deltaMax= %.4f deg" % result.deltaMax_deg)
    print("  A1 = A2 = %.4f pu-rad" % result.A1)
    print("  tcr = %.4f s" % result.tcr)


def menu_circuito_trifasico():
    """Menú del entorno de resolución de circuitos trifásicos balanceados."""
    from .asistente import asistente, consola
    print("\n===== ENTORNO DE CIRCUITO TRIFASICO =====")
    print("Resuelve el circuito completo (fuente + linea + varias cargas en")
    print("paralelo, en Y o Delta) sin anotar valores intermedios.\n")
    opcion = input_helpers("choice", "Elija el modo:", [
        "Asistente guiado (paso a paso)",
        "Consola de comandos (avanzado)",
    ])
    if opcion == 1:
        asistente()
    else:
        consola()
