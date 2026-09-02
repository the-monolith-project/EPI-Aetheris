"""Pruebas de los loaders respiratorios sin tocar Postgres."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cargar_neumonias import leer_filas_seguras  # noqa: E402
from cargar_vigilancia_respiratoria import construir_filas_carga  # noqa: E402


def test_neumonias_loader_omite_filas_con_nota(tmp_path, monkeypatch):
    csv_path = tmp_path / "desacumulado_neumonias.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anio", "departamento", "semana", "valor", "nota"])
        w.writerow(["2018", "San Salvador", "3", "87", ""])
        w.writerow(["2018", "San Salvador", "2", "172", "primer corte del anio en SE2: acumulado SE1-SE2"])
        w.writerow(["2018", "San Salvador", "4", "", "hueco entre cortes"])
        w.writerow(["2023", "Cuscatlán", "41", "", "correccion retroactiva: diff=-17"])
    import cargar_neumonias as mod
    monkeypatch.setattr(mod, "CSV_PATH", csv_path)
    filas = leer_filas_seguras()
    assert filas == [(2018, "San Salvador", 3, 87)]


def test_virus_usa_columna_semana_y_no_desacumula_positividad():
    inventario = [
        {
            "estado": "ok", "anio": "2018", "semana_corte": "2",
            "metrica": "muestras_analizadas", "anio_actual": "45", "semana": "26",
        },
        {
            "estado": "ok", "anio": "2018", "semana_corte": "2",
            "metrica": "positividad_virus", "anio_actual": "2", "semana": "4",
        },
        {
            "estado": "ok", "anio": "2023", "semana_corte": "25",
            "metrica": "covid_19", "anio_actual": "10", "semana": "2",
        },
        {
            "estado": "revision_manual", "anio": "2018", "semana_corte": "47",
            "metrica": "muestras_analizadas", "anio_actual": "1577", "semana": "39",
        },
    ]
    filas = construir_filas_carga(inventario)
    muestras = [f for f in filas if f[3] == "muestras_analizadas"]
    assert muestras == [(2018, 2, "todos", "muestras_analizadas", 26.0, "conteo")]
    pos = [f for f in filas if f[3] == "positividad"]
    assert pos == [(2018, 2, "todos", "positividad", 2.0, "porcentaje")]
    covid = [f for f in filas if f[2] == "covid_19"]
    assert covid == [(2023, 25, "covid_19", "detecciones", 2.0, "conteo")]


def test_virus_desacumula_cuando_no_hay_columna_semana():
    inventario = [
        {
            "estado": "ok", "anio": "2023", "semana_corte": "1",
            "metrica": "vsr", "anio_actual": "1", "semana": "",
        },
        {
            "estado": "ok", "anio": "2023", "semana_corte": "2",
            "metrica": "vsr", "anio_actual": "4", "semana": "",
        },
        {
            "estado": "ok", "anio": "2023", "semana_corte": "3",
            "metrica": "vsr", "anio_actual": "3", "semana": "",
        },
    ]
    filas = construir_filas_carga(inventario)
    vsr = sorted(f for f in filas if f[2] == "vsr")
    assert vsr[0] == (2023, 1, "vsr", "detecciones", 1.0, "conteo")
    assert vsr[1] == (2023, 2, "vsr", "detecciones", 3.0, "conteo")
    assert len(vsr) == 2  # SE3 diff negativo excluido


def test_virus_deduplica_misma_llave_natural():
    inventario = [
        {
            "estado": "ok", "anio": "2018", "semana_corte": "2",
            "metrica": "vsr", "anio_actual": "0", "semana": "1",
        },
        {
            "estado": "ok", "anio": "2018", "semana_corte": "2",
            "metrica": "vsr", "anio_actual": "0", "semana": "0",
        },
    ]
    filas = construir_filas_carga(inventario)
    vsr = [f for f in filas if f[2] == "vsr"]
    assert len(vsr) == 1
    assert vsr[0][4] == 0.0
