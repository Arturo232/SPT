"""Pruebas de resolución de rutas de exportación."""

import json
import os
from pathlib import Path

import pytest

from analizador.config import export_dir, project_root
from analizador.services import service_analizar_carga
from analizador.utils import export_results, resolve_export_path


@pytest.fixture
def base_tmp(monkeypatch, tmp_path):
    """Configura SEP_EXPORT_DIR a un directorio temporal para los tests."""
    monkeypatch.setenv("SEP_EXPORT_DIR", str(tmp_path / "exports"))
    return tmp_path / "exports"


def test_project_root_existe():
    raiz = project_root()
    assert (raiz / "pyproject.toml").is_file()


def test_export_dir_por_defecto_es_absoluta():
    d = export_dir()
    assert isinstance(d, Path)
    assert d.is_absolute()


def test_resolve_export_path_nombre_simple(base_tmp):
    ruta = resolve_export_path("mi_circuito")
    assert ruta == base_tmp / "mi_circuito"


def test_resolve_export_path_subcarpeta(base_tmp):
    ruta = resolve_export_path("sub/prueba")
    assert ruta == base_tmp / "sub" / "prueba"
    assert ruta.parent.is_dir()


def test_resolve_export_path_absoluta_se_respeta(base_tmp, tmp_path):
    absoluta = tmp_path / "directo" / "archivo.json"
    ruta = resolve_export_path(str(absoluta))
    assert ruta == absoluta
    assert ruta.parent.is_dir()


def test_export_results_guarda_en_carpeta_base(base_tmp):
    result = service_analizar_carga("PF", 250e3, 0.9, "inductiva")

    f_json = export_results(result, "reporte", "json")
    assert f_json == str(base_tmp / "reporte.json")
    assert os.path.isfile(f_json)
    with open(f_json, encoding="utf-8") as fh:
        datos = json.load(fh)
    assert "P" in datos

    f_csv = export_results(result, "sub/reporte_csv", "csv")
    assert f_csv == str(base_tmp / "sub" / "reporte_csv.csv")
    assert os.path.isfile(f_csv)


def test_export_results_ruta_absoluta(base_tmp, tmp_path):
    result = service_analizar_carga("PF", 250e3, 0.9, "inductiva")
    destino = str(tmp_path / "absoluto.json")
    f_json = export_results(result, destino)
    assert f_json == destino
    assert os.path.isfile(f_json)


def test_export_dir_desde_variable_entorno(monkeypatch, tmp_path):
    custom = str(tmp_path / "custom_exports")
    monkeypatch.setenv("SEP_EXPORT_DIR", custom)
    assert export_dir() == Path(custom)


def test_export_dir_relativa_se_resuelve_contra_raiz(monkeypatch, tmp_path):
    # Limpiamos variable de entorno para que use config por defecto
    monkeypatch.delenv("SEP_EXPORT_DIR", raising=False)
    d = export_dir()
    assert d == project_root() / "resultados"
