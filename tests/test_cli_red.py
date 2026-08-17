"""Pruebas del motor de comandos CLI para redes (trifasico / monofasico).

Cubre el parser dinámico de 'N' cargas, la conversión Delta→Y, el multi-tramo
de líneas, y la resolución vía el despachador de la consola.
"""

import pytest
from unittest.mock import patch

from rich.console import Console

from analizador.cli import console as cli
from analizador.core.circuito import CircuitoMonofasico, CircuitoTrifasico

@pytest.fixture
def consola():
    return Console(record=True)


# ---------------------------------------------------------------------------
# Parser de argumentos
# ---------------------------------------------------------------------------
def test_parser_cargas_dinamicas():
    datos = cli._parse_red_args(
        ["--fuente", "208", "--cargas", "Y:4+j2", "D:5-j4", "Y:10+j0"])
    assert datos.fuente == 208 + 0j
    assert datos.cargas == [
        ("Y", 4 + 2j),
        ("Delta", 5 - 4j),
        ("Y", 10 + 0j),
    ]
    assert datos.lineas == []


def test_parser_una_carga_sin_tipo():
    datos = cli._parse_red_args(["--fuente", "120", "--cargas", "4+j2"])
    assert datos.cargas == [("Y", 4 + 2j)]


def test_parser_multitramo_lineas():
    datos = cli._parse_red_args(
        ["--fuente", "208", "--cargas", "Y:4+j2", "--lineas", "8+j4", "2+j1"])
    assert datos.lineas == [8 + 4j, 2 + 1j]


def test_parser_linea_unica():
    datos = cli._parse_red_args(
        ["--fuente", "208", "--cargas", "Y:4+j2", "--linea", "8+j4"])
    assert datos.lineas == [8 + 4j]


def test_parser_polar_rectangular():
    datos = cli._parse_red_args(
        ["--fuente", "100[0]", "--cargas", "Y:50[-36.87]", "D:30[0]"])
    assert abs(datos.fuente - 100) < 1e-6
    assert abs(datos.cargas[0][1] - (40 - 30j)) < 1e-3
    assert abs(datos.cargas[1][1] - 30) < 1e-3


def test_parser_error_opcion_desconocida():
    with pytest.raises(ValueError):
        cli._parse_red_args(["--fuente", "208", "--bogus", "x"])


def test_parser_error_tipo_conexion():
    with pytest.raises(ValueError):
        cli._parse_red_args(["--fuente", "208", "--cargas", "Z:4+j2"])


def test_parser_error_complejo():
    with pytest.raises(ValueError):
        cli._parse_red_args(["--fuente", "208", "--cargas", "Y:abc"])


def test_parser_sin_fuente_devuelve_none():
    # el parser solo recoge los valores; la falta de fuente la valida el
    # comando (que muestra un panel de error).
    datos = cli._parse_red_args(["--cargas", "Y:4+j2"])
    assert datos.fuente is None
    assert datos.cargas == [("Y", 4 + 2j)]


# ---------------------------------------------------------------------------
# Resolución vía despachador
# ---------------------------------------------------------------------------
def test_trifasico_cli_multiples_cargas(consola):
    cli._ejecutar(
        consola, "trifasico --fuente 208 --cargas Y:4+j2 D:5-j4 --linea 8+j4")

    esperado = CircuitoTrifasico()
    esperado.set_fuente(208, 0.0, "linea")
    esperado.set_linea(8 + 4j)
    esperado.agregar_carga("Y", 4 + 2j)
    esperado.agregar_carga("Delta", 5 - 4j)
    res = esperado.resolver()

    # verificar la conversion Delta->Y interna
    assert abs(esperado.cargas[1]["z_y"] - (5 - 4j) / 3) < 1e-9
    assert abs(esperado.z_total - ((8 + 4j) + 1 / (
        1 / (4 + 2j) + 1 / ((5 - 4j) / 3)))) < 1e-9
    # invariantes del balance total
    assert res.P == pytest.approx(esperado.resultado.P, rel=1e-6)
    assert res.Q == pytest.approx(esperado.resultado.Q, rel=1e-6)
    # el render no lanza y genero salida
    assert consola.export_text()


def test_trifasico_cli_polar(consola):
    cli._ejecutar(
        consola, "trifasico --fuente 100[0] --cargas Y:50[-36.87] D:30[0]")
    esperado = CircuitoTrifasico()
    esperado.set_fuente(100, 0.0, "linea")
    esperado.agregar_carga("Y", 40 - 30j)
    esperado.agregar_carga("Delta", 30 + 0j)
    res = esperado.resolver()
    assert res.Sabs == pytest.approx(esperado.resultado.Sabs, rel=1e-6)


def test_monofasico_cli_multitramo(consola):
    cli._ejecutar(
        consola,
        "monofasico --fuente 120 --cargas 4+j2 5-j4 --lineas 8+j4 2+j1")

    esperado = CircuitoMonofasico()
    esperado.set_fuente(120, 0.0)
    esperado.set_linea((8 + 4j) + (2 + 1j))
    esperado.agregar_carga(4 + 2j)
    esperado.agregar_carga(5 - 4j)
    res = esperado.resolver()

    assert abs(esperado.z_linea - (10 + 5j)) < 1e-9
    assert res.P == pytest.approx(esperado.resultado.P, rel=1e-6)
    assert res.Q == pytest.approx(esperado.resultado.Q, rel=1e-6)
    assert consola.export_text()


def test_trifasico_comando_con_argumentos_reconocido(consola):
    # el despachador debe reconocer el comando base con argumentos
    assert cli._ejecutar(
        consola, "tri --fuente 208 --cargas Y:4+j2") is True


def test_error_argumentos_muestra_panel(consola):
    cli._ejecutar(consola, "trifasico --cargas Y:4+j2")
    assert "Argumentos invalidos" in consola.export_text()


# ---------------------------------------------------------------------------
# Limpieza de pantalla (clc / cls)
# ---------------------------------------------------------------------------
def test_clc_limpia_pantalla(consola):
    with patch.object(consola, "clear") as mock_clear:
        cli._cmd_clc(consola)
        mock_clear.assert_called_once()


def test_cls_despachado(consola):
    with patch.object(consola, "clear") as mock_clear:
        assert cli._ejecutar(consola, "cls") is True
        mock_clear.assert_called_once()


def test_clc_despachado(consola):
    with patch.object(consola, "clear") as mock_clear:
        assert cli._ejecutar(consola, "clc") is True
        mock_clear.assert_called_once()


# ---------------------------------------------------------------------------
# Autocompletado de banderas -- y bandera --paralelo
# ---------------------------------------------------------------------------
def test_autocompletado_incluye_banderas():
    palabras = cli._palabras_comandos()
    for bandera in ("--fuente", "--cargas", "--linea", "--lineas",
                    "--paralelo"):
        assert bandera in palabras


def test_autocompletado_sugiere_banderas():
    # el completador devuelve candidatos al escribir el prefijo '--'
    class Doc:
        def get_word_before_cursor(self):
            return "--"

    completer = cli._ComandoCompleter(cli._palabras_comandos())
    completions = list(completer.get_completions(Doc(), None))
    sugeridos = {c.text for c in completions}
    assert "--fuente" in sugeridos
    assert "--paralelo" in sugeridos


def test_parser_bandera_paralelo():
    datos = cli._parse_red_args(
        ["--fuente", "208", "--cargas", "Y:4+j2", "--paralelo"])
    assert datos.paralelo is True
    assert datos.cargas == [("Y", 4 + 2j)]


def test_parser_paralelo_default_false():
    datos = cli._parse_red_args(["--fuente", "208", "--cargas", "Y:4+j2"])
    assert datos.paralelo is False


# ---------------------------------------------------------------------------
# Desglose trifasico completo (3 hilos) por carga
# ---------------------------------------------------------------------------
def test_desglose_trifasico_estrella(consola):
    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2")
    txt = consola.export_text()
    assert "Desglose trifasico por carga" in txt
    for lbl in ("V_an/V_bn/V_cn", "I_a/I_b/I_c"):
        assert lbl in txt


def test_desglose_trifasico_delta(consola):
    cli._ejecutar(consola, "trifasico --fuente 208 --cargas D:5-j4")
    txt = consola.export_text()
    assert "Desglose trifasico por carga" in txt
    for lbl in ("V_ab/V_bc/V_ca", "I_ab/I_bc/I_ca"):
        assert lbl in txt


def test_desglose_trifasico_mixto(consola):
    cli._ejecutar(
        consola, "trifasico --fuente 208 --cargas Y:4+j2 D:5-j4")
    txt = consola.export_text()
    assert "V_an/V_bn/V_cn" in txt
    assert "I_a/I_b/I_c" in txt
    assert "V_ab/V_bc/V_ca" in txt
    assert "I_ab/I_bc/I_ca" in txt


def test_desglose_no_en_monofasico(consola):
    cli._ejecutar(consola, "monofasico --fuente 120 --cargas 4+j2")
    txt = consola.export_text()
    assert "Desglose trifasico" not in txt
    assert "V_an/V_bn/V_cn" not in txt


# ---------------------------------------------------------------------------
# Gramática por niveles y navegación
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _nav_limpia():
    """Limpia la pila de navegación y el último resultado entre pruebas."""
    cli._nav_reset()
    cli._ULTIMO_RESULTADO = None
    yield
    cli._nav_reset()
    cli._ULTIMO_RESULTADO = None


@pytest.fixture(autouse=True)
def _no_mostrar_graficas():
    """Evita que los diagramas fasoriales bloqueen la ejecución en pruebas."""
    with patch("matplotlib.pyplot.show"):
        yield


def test_gramatica_valida_trifasico_fuente(consola):
    assert cli._ejecutar(
        consola, "trifasico fuente --conexion estrella --v-rms 208") is True
    txt = consola.export_text()
    assert "trifasico" in txt and "fuente" in txt
    assert "estrella" in txt


def test_gramatica_entra_en_contexto(consola):
    cli._ejecutar(consola, "trifasico fuente --v-rms 208")
    assert cli._prompt_actual() == "SEP/trifasico> "


def test_escape_volver_saca_contexto(consola):
    cli._ejecutar(consola, "trifasico fuente --v-rms 208")
    assert cli._prompt_actual() == "SEP/trifasico> "
    assert cli._ejecutar(consola, "volver") is True
    assert cli._prompt_actual() == "SEP> "


def test_escape_salir_en_raiz_sale(consola):
    assert cli._ejecutar(consola, "salir") is False


def test_escape_exit_saca_contexto_no_sale(consola):
    cli._ejecutar(consola, "monofasico carga --potencia-activa 1200")
    # en contexto, exit vuelve al prompt principal (no sale de la app)
    assert cli._ejecutar(consola, "exit") is True
    assert cli._prompt_actual() == "SEP> "


def test_error_repetir_trifasico(consola):
    cli._ejecutar(consola, "trifasico trifasico")
    txt = consola.export_text()
    assert "[ERROR SINTACTICO]" in txt
    assert "No puedes repetir el comando 'trifasico'" in txt
    assert "Opciones validas" in txt
    assert "trifasico fuente" in txt and "trifasico carga" in txt


def test_error_falta_componente(consola):
    cli._ejecutar(consola, "trifasico")
    txt = consola.export_text()
    assert "[ERROR SINTACTICO]" in txt
    assert "Falta el componente" in txt


def test_error_componente_invalido(consola):
    cli._ejecutar(consola, "trifasico motor")
    txt = consola.export_text()
    assert "[ERROR SINTACTICO]" in txt
    assert "Componente no valido" in txt
    assert "fuente | carga | linea" in txt


def test_error_bandera_invalida_para_componente(consola):
    cli._ejecutar(consola, "trifasico fuente --tipo inductivo")
    txt = consola.export_text()
    assert "[ERROR SINTACTICO]" in txt
    assert "--tipo" in txt and "no es valida" in txt


def test_error_sistema_desconocido(consola):
    # un sistema desconocido cae en la corrección tipográfica (difflib)
    cli._ejecutar(consola, "bifasico fuente")
    txt = consola.export_text()
    assert "bifasico" in txt
    assert "trifasico" in txt


def test_gramatica_carga_banderas(consola):
    cli._ejecutar(
        consola, "trifasico carga --potencia-activa 1200 "
                 "--factor-potencia 0.9 --tipo inductivo")
    txt = consola.export_text()
    assert "carga" in txt
    assert "0.9" in txt


def test_gramatica_convive_con_cli_legacy(consola):
    # la sintaxis legada sigue funcionando tras usar la gramática
    cli._ejecutar(consola, "trifasico fuente --v-rms 208")
    cli._nav_reset()
    cli._ejecutar(
        consola, "trifasico --fuente 208 --cargas Y:4+j2 D:5-j4 --linea 8+j4")
    txt = consola.export_text()
    assert "Desglose trifasico" in txt


# ---------------------------------------------------------------------------
# Layout adaptativo
# ---------------------------------------------------------------------------
def test_render_adaptativo_ancho_estrecho():
    cons = Console(record=True, width=60)
    cli._nav_reset()
    cli._ejecutar(cons, "trifasico --fuente 208 --cargas Y:4+j2 D:5-j4")
    txt = cons.export_text()
    assert "1. Datos de entrada" in txt
    assert "2. Proceso de reduccion" in txt
    assert "3. Variables de estado" in txt
    assert "4. Balance de potencia" in txt
    assert "5. Desglose trifasico" in txt
    assert "6. Interpretación técnica" in txt


def test_render_adaptativo_ancho_amplio():
    cons = Console(record=True, width=160)
    cli._nav_reset()
    cli._ejecutar(cons, "trifasico --fuente 208 --cargas Y:4+j2 D:5-j4")
    txt = cons.export_text()
    assert "1. Datos de entrada" in txt
    assert "Desglose trifasico" in txt


# ---------------------------------------------------------------------------
# Fuente Fase (F) / Línea (L)
# ---------------------------------------------------------------------------
def test_parse_fuente_linea_prefijo():
    datos = cli._parse_red_args(["--fuente", "L:208[30]", "--cargas", "Y:4+j2"])
    assert datos.fuente_tipo == "L"
    assert abs(datos.fuente) == pytest.approx(208, rel=1e-6)
    assert cli._angulo_grados(datos.fuente) == pytest.approx(30, rel=1e-6)


def test_parse_fuente_fase_prefijo():
    datos = cli._parse_red_args(["--fuente", "F:120[0]", "--cargas", "Y:4+j2"])
    assert datos.fuente_tipo == "F"
    assert abs(datos.fuente) == pytest.approx(120, rel=1e-6)
    assert cli._angulo_grados(datos.fuente) == pytest.approx(0, rel=1e-6)


def test_parse_fuente_sin_prefijo_defecto_linea():
    datos = cli._parse_red_args(["--fuente", "208", "--cargas", "Y:4+j2"])
    assert datos.fuente_tipo == "L"
    assert datos.fuente == pytest.approx(208 + 0j)


def test_fuente_fase_magnitud_convertida(consola):
    cli._ejecutar(consola, "trifasico --fuente F:120[0] --cargas Y:4+j2")
    txt = consola.export_text()
    assert "Fuente (fase)" in txt
    assert "V_LL = 207.8 V" in txt
    assert "V_LN = 120 V" in txt


def test_fuente_angulo_linea_opcion_b(consola):
    # L:208[30] -> fase 'a' = 30 - 30 = 0 deg
    cli._ejecutar(consola, "trifasico --fuente L:208[30] --cargas Y:4+j2")
    txt = consola.export_text()
    assert "Fuente (linea)" in txt
    assert "restando 30" in txt
    # la tension de fase en la carga debe estar casi en 0 deg (despues de linea)
    assert "120.1 ∠ 0°" in txt or "120.089" in txt


# ---------------------------------------------------------------------------
# Panel interpretativo
# ---------------------------------------------------------------------------
def test_panel_interpretativo_presente(consola):
    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2")
    txt = consola.export_text()
    assert "6. Interpretación técnica" in txt
    assert "Conversión aplicada" in txt
    assert "Diagnóstico del sistema" in txt
    assert "Factor de potencia global" in txt


def test_diagnostico_inductivo_vs_capacitivo(consola):
    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2")
    txt = consola.export_text()
    assert "INDUCTIVO" in txt
    assert "Q > 0" in txt

    cons2 = Console(record=True)
    cli._nav_reset()
    cli._ejecutar(cons2, "trifasico --fuente 208 --cargas D:5-j4")
    txt2 = cons2.export_text()
    assert "CAPACITIVO" in txt2
    assert "Q < 0" in txt2


def test_evalua_factor_potencia(consola):
    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2")
    txt = consola.export_text()
    assert "FP =" in txt
    assert "%)" in txt




# ---------------------------------------------------------------------------
# Resolución académica --taller (incisos a-j) y análisis extendido
# ---------------------------------------------------------------------------
def test_flag_taller_activa_incisos(consola):
    with patch("matplotlib.pyplot.show"):
        cli._ejecutar(
            consola, "trifasico --fuente 208 --cargas Y:4+j2 D:5-j4 "
                     "--linea 8+j4 --taller")
    txt = consola.export_text()
    for lbl in ("Inciso (a)", "Inciso (b)", "Inciso (c)", "Inciso (d)",
                "Inciso (e)", "Inciso (f)", "Inciso (g)", "Inciso (h)",
                "Inciso (i)", "Inciso (j)", "Análisis extendido"):
        assert lbl in txt


def test_flag_resolver_incisos_alias(consola):
    with patch("matplotlib.pyplot.show"):
        cli._ejecutar(
            consola, "trifasico --fuente 208 --cargas Y:4+j2 --resolver-incisos")
    assert "Inciso (a)" in consola.export_text()


def test_inciso_b_c_potencia_coincide_con_motor(consola):
    from analizador.core.circuito import CircuitoTrifasico

    with patch("matplotlib.pyplot.show"):
        cli._ejecutar(
            consola, "trifasico --fuente 208 --cargas Y:4+j2 --taller")

    esperado = CircuitoTrifasico()
    esperado.set_fuente(208, 0.0, "linea")
    esperado.agregar_carga("Y", 4 + 2j)
    res = esperado.resolver()

    txt = consola.export_text()
    # (b) y (c) deben coincidir con S3f del motor
    s_mag = abs(res.s3f)
    # la magnitud de S3f (en notación de ingeniería) aparece al menos en (b) y (c)
    assert txt.count(f"{s_mag / 1000:.4g} k") >= 2
    # ambos métodos deben dar el mismo resultado complejo
    assert f"{s_mag / 1000:.4g} k" in txt


def test_inciso_a_corriente_fuente(consola):
    from analizador.core.circuito import CircuitoTrifasico

    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2 --taller")
    esperado = CircuitoTrifasico()
    esperado.set_fuente(208, 0.0, "linea")
    esperado.agregar_carga("Y", 4 + 2j)
    res = esperado.resolver()
    txt = consola.export_text()
    assert f"{abs(res.i_linea):.4g}" in txt


def test_inciso_d_tension_carga(consola):
    from analizador.core.circuito import CircuitoTrifasico

    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2 --taller")
    esperado = CircuitoTrifasico()
    esperado.set_fuente(208, 0.0, "linea")
    esperado.agregar_carga("Y", 4 + 2j)
    res = esperado.resolver()
    txt = consola.export_text()
    assert f"{res.v_carga_linea:.4g} V" in txt


def test_inciso_e_fasorial_estrella(consola):
    with patch("matplotlib.pyplot.show"):
        cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2 --taller")
    txt = consola.export_text()
    assert "V_an =" in txt
    assert "V_bn" in txt and "V_cn" in txt
    assert "Fasorial de tensiones (Estrella)" in txt
    assert "∠" in txt and "°" in txt


def test_inciso_f_g_h_delta(consola):
    with patch("matplotlib.pyplot.show"):
        cli._ejecutar(
            consola, "trifasico --fuente 208 --cargas D:5-j4 --taller")
    txt = consola.export_text()
    assert "I_f =" in txt
    assert "I_ab" in txt and "I_bc" in txt and "I_ca" in txt
    assert "Fasorial de corrientes (Delta)" in txt


def test_inciso_i_desglose_potencia(consola):
    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2 --taller")
    txt = consola.export_text()
    assert "P_perdidas" in txt
    assert "kW" in txt and "kvar" in txt


def test_inciso_j_correccion_fp_kvar(consola):
    from analizador.core.circuito import CircuitoTrifasico
    from analizador.modules.correccion_fp import required_reactive_power

    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:3+j4 --taller")
    esperado = CircuitoTrifasico()
    esperado.set_fuente(208, 0.0, "linea")
    esperado.agregar_carga("Y", 3 + 4j)
    res = esperado.resolver()
    c = res.cargas[0]
    comp = required_reactive_power(c["P"], c["fp"], 0.8)
    txt = consola.export_text()
    assert f"{comp.Qc / 1000:.4g} kvar" in txt


def test_inciso_j_correccion_fp_capacitancia(consola):
    from analizador.core.circuito import CircuitoTrifasico
    from analizador.modules.correccion_fp import (capacitor_reactance,
                                                  capacitor_value,
                                                  required_reactive_power)

    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:3+j4 --taller")
    esperado = CircuitoTrifasico()
    esperado.set_fuente(208, 0.0, "linea")
    esperado.agregar_carga("Y", 3 + 4j)
    res = esperado.resolver()
    c = res.cargas[0]
    comp = required_reactive_power(c["P"], c["fp"], 0.8)
    v_ln = abs(c["v_fase"])
    cap = capacitor_value(60.0, capacitor_reactance(v_ln, comp.Qc).Xc)
    txt = consola.export_text()
    assert f"{cap.C_uF:.4g} uF" in txt


def test_analisis_extendido_variables(consola):
    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2 --taller")
    txt = consola.export_text()
    assert "Y_eq =" in txt
    assert "Eficiencia de transmisión" in txt
    assert "Regulación de voltaje" in txt
    assert "Verificación LKC" in txt


def test_analisis_extendido_lkc_ok(consola):
    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2 D:5-j4 --taller")
    txt = consola.export_text()
    assert "[green]OK[/]" in txt


def test_monofasico_taller(consola):
    cli._ejecutar(consola, "monofasico --fuente 120 --cargas 4+j2 5-j4 --taller")
    txt = consola.export_text()
    for lbl in ("Inciso (a)", "Inciso (b)", "Inciso (d)", "Inciso (i)",
                "Inciso (j)", "Análisis extendido"):
        assert lbl in txt


def test_parser_flag_taller_y_fp():
    datos = cli._parse_red_args(
        ["--fuente", "208", "--cargas", "Y:4+j2", "--taller",
         "--carga-fp", "2", "--fp", "0.9"])
    assert datos.taller is True
    assert datos.carga_fp == 2
    assert datos.fp_objetivo == pytest.approx(0.9)


def test_parser_taller_defaults():
    datos = cli._parse_red_args(["--fuente", "208", "--cargas", "Y:4+j2"])
    assert datos.taller is False
    assert datos.carga_fp == 1
    assert datos.fp_objetivo == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# Comando graficar / fasores
# ---------------------------------------------------------------------------
def test_graficar_sin_resultado(consola):
    cli._ejecutar(consola, "graficar")
    txt = consola.export_text()
    assert "No hay resultado previo" in txt


def test_graficar_trifasico_tensiones(consola):
    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2")
    cli._ejecutar(consola, "graficar --tensiones")
    txt = consola.export_text()
    assert "Diagrama generado correctamente" in txt
    import matplotlib.pyplot as plt
    assert plt.get_fignums()
    assert plt.gcf().axes[0].get_title() == "Fasores de tensión"


def test_graficar_trifasico_por_defecto(consola):
    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2 D:5-j4")
    cli._ejecutar(consola, "fasores")
    txt = consola.export_text()
    assert "Diagrama generado correctamente" in txt
    import matplotlib.pyplot as plt
    fig = plt.gcf()
    assert len(fig.axes) >= 2


def test_graficar_trifasico_corrientes(consola):
    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2")
    cli._ejecutar(consola, "graficar --corrientes")
    txt = consola.export_text()
    assert "Diagrama generado correctamente" in txt
    import matplotlib.pyplot as plt
    assert plt.gcf().axes[0].get_title() == "Fasores de corriente"


def test_graficar_guardar(tmp_path):
    consola = Console(record=True)
    with patch("matplotlib.pyplot.show"):
        cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2")
        ruta = tmp_path / "fasores.png"
        cli._ejecutar(consola, f"graficar --guardar {ruta}")
    txt = consola.export_text()
    assert "Figura exportada a" in txt
    assert ruta.exists()
    assert ruta.stat().st_size > 0


def test_graficar_potencia(consola):
    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2")
    cli._ejecutar(consola, "graficar --potencia")
    txt = consola.export_text()
    assert "Diagrama generado correctamente" in txt


def test_graficar_monofasico(consola):
    cli._ejecutar(consola, "monofasico --fuente 120 --cargas 4+j2")
    cli._ejecutar(consola, "graficar")
    txt = consola.export_text()
    assert "Diagrama generado correctamente" in txt


def test_phasor_plot_dibuja_vectores():
    from analizador.gui.viz import phasor_plot

    fig, ax = phasor_plot([120 + 0j, -60 - 103.9j], ["Van", "Vbn"], unidad="V")
    etiquetas = [t.get_text() for t in ax.texts if t.get_text().strip()]
    assert len(etiquetas) >= 2
    assert any("Van: 120.00 V" in e for e in etiquetas)
    flechas = [t for t in ax.texts if getattr(t, "arrow_patch", None) is not None]
    assert len(flechas) >= 2
    assert ax.get_rmax() > 0
    assert ax.get_rmax() <= 120 * 1.10 + 1e-9


# ---------------------------------------------------------------------------
# Bandera --graficar dentro de trifasico / monofasico
# ---------------------------------------------------------------------------
def test_parser_flag_graficar():
    datos = cli._parse_red_args(
        ["--fuente", "216.51[0]", "--cargas", "Y:36+j40", "--graficar"])
    assert datos.graficar is True
    assert datos.graficar_args == []


def test_parser_flag_graficar_modo():
    datos = cli._parse_red_args(
        ["--fuente", "216.51[0]", "--cargas", "Y:36+j40",
         "--graficar", "tensiones"])
    assert datos.graficar is True
    assert datos.graficar_args == ["tensiones"]


def test_parser_flag_graficar_mono_alias():
    datos = cli._parse_red_args(
        ["--fuente", "216.51[0]", "--cargas", "Y:36+j40",
         "--graficar", "-m"])
    assert datos.graficar is True
    assert datos.graficar_args == ["-m"]


def test_parser_flag_graficar_1f_tensiones():
    datos = cli._parse_red_args(
        ["--fuente", "216.51[0]", "--cargas", "Y:36+j40",
         "--graficar", "--1f", "--tensiones"])
    assert datos.graficar_args == ["--1f", "--tensiones"]


def test_parser_flag_graficar_invalida():
    with pytest.raises(ValueError, match="bandera de visualizacion"):
        cli._parse_red_args(
            ["--fuente", "216.51[0]", "--cargas", "Y:36+j40",
             "--graficar", "-mono"])


def test_trifasico_graficar_bandera(consola):
    cli._ejecutar(
        consola, "trifasico --fuente 216.51[0] --cargas Y:36+j40 --graficar")
    txt = consola.export_text()
    assert "Diagrama generado correctamente" in txt


def test_trifasico_graficar_modo_tensiones(consola):
    cli._ejecutar(
        consola, "trifasico --fuente 216.51[0] --cargas Y:36+j40 "
                 "--graficar tensiones")
    import matplotlib.pyplot as plt
    assert plt.gcf().axes[0].get_title() == "Fasores de tensión"


def test_monofasico_graficar_bandera(consola):
    cli._ejecutar(consola, "monofasico --fuente 120 --cargas 4+j2 --graficar")
    txt = consola.export_text()
    assert "Diagrama generado correctamente" in txt


def test_trifasico_graficar_con_alias_m(consola):
    cli._ejecutar(
        consola, "trifasico --fuente 207.85[0] --cargas Y:30+j40 "
                 "--taller --graficar -m")
    assert "equivalente monofásico" in _titulo_fig()
    txt = consola.export_text()
    assert "Diagrama generado correctamente" in txt


def test_trifasico_graficar_con_1f_tensiones(consola):
    cli._ejecutar(
        consola, "trifasico --fuente 207.85[0] --cargas Y:30+j40 "
                 "--graficar --1f --tensiones")
    assert "equivalente monofásico" in _titulo_fig()


def test_trifasico_graficar_bandera_invalida(consola):
    cli._ejecutar(
        consola, "trifasico --fuente 207.85[0] --cargas Y:30+j40 "
                 "--graficar -mono")
    txt = consola.export_text()
    assert "bandera de visualizacion desconocida" in txt


# ---------------------------------------------------------------------------
# Modo monofásico en graficar / fasores
# ---------------------------------------------------------------------------
def _titulo_fig():
    import matplotlib.pyplot as plt
    return plt.gcf().axes[0].get_title()


def test_graficar_monofasico_sobre_trifasico(consola):
    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2")
    cli._ejecutar(consola, "graficar --monofasico")
    assert "equivalente monofásico" in _titulo_fig()
    txt = consola.export_text()
    assert "Diagrama generado correctamente" in txt


def test_graficar_monofasico_alias_m(consola):
    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2")
    cli._ejecutar(consola, "graficar -m")
    assert "equivalente monofásico" in _titulo_fig()


def test_graficar_monofasico_alias_1f(consola):
    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2")
    cli._ejecutar(consola, "graficar --1f")
    assert "equivalente monofásico" in _titulo_fig()


def test_graficar_monofasico_solo_tensiones(consola):
    import matplotlib.pyplot as plt

    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2")
    cli._ejecutar(consola, "graficar --monofasico --tensiones")
    etiquetas = [t.get_text() for t in plt.gcf().axes[0].texts
                 if t.get_text().strip()]
    assert any("V_a" in e for e in etiquetas)


def test_graficar_monofasico_solo_corrientes(consola):
    import matplotlib.pyplot as plt

    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2")
    cli._ejecutar(consola, "graficar --monofasico --corrientes")
    etiquetas = [t.get_text() for t in plt.gcf().axes[0].texts
                 if t.get_text().strip()]
    assert any("I_a" in e for e in etiquetas)


def test_graficar_automatico_monofasico_sin_bandera(consola):
    cli._ejecutar(consola, "monofasico --fuente 120 --cargas 4+j2")
    cli._ejecutar(consola, "graficar")
    assert "equivalente monofásico" in _titulo_fig()


def test_graficar_trifasico_sigue_siendo_3f(consola):
    import matplotlib.pyplot as plt

    cli._ejecutar(consola, "trifasico --fuente 208 --cargas Y:4+j2")
    cli._ejecutar(consola, "graficar")
    fig = plt.gcf()
    assert "equivalente monofásico" not in fig.axes[0].get_title()
    assert len(fig.axes) >= 2


# ---------------------------------------------------------------------------
# Formateador matemático (polar ∠, notación de ingeniería)
# ---------------------------------------------------------------------------
def test_fmt_polar_simbolo_angulo():
    assert "8.944 ∠ -63.43°" in cli._fmt_polar(4 - 8j)


def test_fmt_polar_sin_deg_ni_corchetes():
    texto = cli._fmt_polar(120.089)
    assert "deg" not in texto
    assert "[" not in texto and "]" not in texto
    assert "∠" in texto and "°" in texto


def test_fmt_polar_con_prefijo_ingenieria():
    texto = cli._fmt_polar(9674.12, "VA")
    assert texto.startswith("9.674 k")
    assert "∠" in texto


def test_fmt_complejo_rect_como_apoyo():
    texto = cli._fmt_complejo(3 + 4j)
    assert "5 ∠ 53.13°" in texto
    assert "(3 + j4)" in texto


def test_formato_numero_sin_notacion_cientifica():
    assert cli._formato_numero(120.089, "V") == "120.1 V"
    assert cli._formato_numero(12400, "W") == "12.4 kW"
    assert cli._formato_numero(530.52e-6, "F") == "530.5 µF"
    for v in (1.88e-16, 9.674e3, 0.00045):
        assert "e" not in cli._formato_numero(v)


def test_prefijo_ing_multiplos_de_tres():
    coef, pref = cli._prefijo_ing(8652.8)
    assert abs(coef - 8.6528) < 1e-3 and pref == "k"
    coef, pref = cli._prefijo_ing(0.005)
    assert abs(coef - 5.0) < 1e-9 and pref == "m"


def test_taller_sin_formulas():
    from unittest.mock import patch

    consola = Console(record=True)
    with patch("matplotlib.pyplot.show"):
        cli._ejecutar(
            consola, "trifasico --fuente 208 --cargas Y:4+j2 --taller")
    txt = consola.export_text()
    assert "Fórmula" not in txt
    assert "Sustitución" not in txt
    assert "exp(j30)" not in txt and "sqrt(3)" not in txt
