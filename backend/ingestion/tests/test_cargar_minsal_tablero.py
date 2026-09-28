"""
Cobertura de la lectura de capturas HAR del tablero de MINSAL
(cargar_minsal_tablero.py): que reconozca solo las series previstas, lea el
anio de la consulta, rechace formatos dudosos y combine capturas quedandose
con la mas reciente.

Los HAR son minimos y se escriben a un archivo temporal -- no tocan las
capturas reales (data/raw/ esta fuera del repo) ni Postgres.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from cargar_minsal_tablero import combinar, huecos, leer_captura  # noqa: E402

SQL = "SELECT ... from public.diagnosticos_acumulados da where da.anio={anio} and cse.publicado is true"


def _entrada(diagnostico, filas, anio=2025, viz="echarts_timeseries_line", capturado="2026-09-27T05:42:00Z", lista=False):
    comparador = [diagnostico] if lista else diagnostico
    cuerpo = {
        "form_data": {
            "viz_type": viz,
            "adhoc_filters": [{"subject": "diagnostico", "comparator": comparador}],
        }
    }
    columna = f"Casos, {diagnostico}" if lista else "Casos"
    respuesta = {
        "result": [
            {
                "query": SQL.format(anio=anio),
                "colnames": ["semana_mes", columna],
                "data": [{"semana_mes": s, columna: v} for s, v in filas],
            }
        ]
    }
    return {
        "startedDateTime": capturado,
        "request": {
            "method": "POST",
            "url": "https://boletin.salud.gob.sv/api/v1/chart/data?form_data=%7B%7D",
            "postData": {"text": json.dumps(cuerpo)},
        },
        "response": {"status": 200, "content": {"text": json.dumps(respuesta)}},
    }


def _har(tmp_path: Path, nombre: str, entradas: list[dict]) -> Path:
    ruta = tmp_path / nombre
    har = {"log": {"pages": [{"title": "https://boletin.salud.gob.sv/superset/dashboard/10/"}], "entries": entradas}}
    ruta.write_text(json.dumps(har), encoding="utf-8")
    return ruta


def test_lee_series_previstas_con_anio_de_la_consulta(tmp_path):
    ruta = _har(
        tmp_path,
        "a.har",
        [
            _entrada("Casos Sospechosos de Dengue", [("01-Ene", 75.0), ("02-Ene", 83.0)]),
            _entrada("Casos confirmados de Dengue", [("01-Ene", 1.0)], lista=True),
            _entrada("Infección  Respiratoria\xa0Aguda", [("01-Ene", 26049.0)]),
            _entrada("Fiebre Tifoidea", [("01-Ene", 4.0)]),  # serie que no se carga
            _entrada("Casos Sospechosos de Dengue", [("01-Ene", 9.0)], viz="big_number_total"),
        ],
    )
    puntos = leer_captura(ruta)
    assert {(p.evento, p.clasificacion, p.anio, p.semana, p.conteo) for p in puntos} == {
        ("dengue", "sospechoso", 2025, 1, 75),
        ("dengue", "sospechoso", 2025, 2, 83),
        ("dengue", "confirmado", 2025, 1, 1),
        ("ira", "notificado", 2025, 1, 26049),
    }


def test_omite_semanas_sin_valor(tmp_path):
    ruta = _har(tmp_path, "a.har", [_entrada("Neumonías", [("01-Ene", 416.0), ("02-Ene", None)])])
    assert [p.semana for p in leer_captura(ruta)] == [1]


@pytest.mark.parametrize(
    "filas, anio",
    [
        ([("01-Ene", 7.5)], 2025),  # valor no entero
        ([("01-Ene", 1.0), ("01-Ene", 2.0)], 2025),  # semana repetida
        ([("54-Dic", 1.0)], 2025),  # semana fuera de rango
        ([("Ene", 1.0)], 2025),  # etiqueta sin numero de semana
    ],
)
def test_rechaza_formatos_dudosos(tmp_path, filas, anio):
    ruta = _har(tmp_path, "a.har", [_entrada("Neumonías", filas, anio=anio)])
    with pytest.raises(ValueError):
        leer_captura(ruta)


def test_rechaza_consulta_sin_anio_unico(tmp_path):
    entrada = _entrada("Neumonías", [("01-Ene", 1.0)])
    respuesta = json.loads(entrada["response"]["content"]["text"])
    respuesta["result"][0]["query"] = "where da.anio=2025 or da.anio=2026"
    entrada["response"]["content"]["text"] = json.dumps(respuesta)
    with pytest.raises(ValueError):
        leer_captura(_har(tmp_path, "a.har", [entrada]))


def test_combinar_gana_la_captura_mas_reciente_e_informa_revisiones(tmp_path):
    vieja = _har(
        tmp_path,
        "vieja.har",
        [_entrada("Neumonías", [("01-Ene", 10.0), ("02-Ene", 20.0)], capturado="2026-09-01T00:00:00Z")],
    )
    nueva = _har(
        tmp_path,
        "nueva.har",
        [_entrada("Neumonías", [("01-Ene", 10.0), ("02-Ene", 25.0)], capturado="2026-09-27T00:00:00Z")],
    )
    elegidos, diferencias = combinar(leer_captura(nueva) + leer_captura(vieja))
    assert elegidos[("neumonia", "notificado", 2025, 2)].conteo == 25
    assert elegidos[("neumonia", "notificado", 2025, 1)].conteo == 10
    assert len(diferencias) == 1 and "20 (vieja.har) -> 25 (nueva.har)" in diferencias[0]


def test_huecos_dentro_de_lo_publicado(tmp_path):
    ruta = _har(tmp_path, "a.har", [_entrada("Neumonías", [("01-Ene", 1.0), ("03-Ene", 1.0)])])
    elegidos, _ = combinar(leer_captura(ruta))
    assert huecos(elegidos) == ["neumonia/notificado 2025: faltan [2]"]
