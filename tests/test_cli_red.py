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
    """Limpia la pila de navegación entre pruebas (estado de módulo)."""
    cli._nav_reset()
    yield
    cli._nav_reset()


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


