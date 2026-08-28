"""
Cobertura de leer_serie_nacional_semanal (cargar_opendengue.py): el filtro
del CSV crudo de OpenDengue a resolucion nacional/semanal y el rechazo
explicito de un case_definition_standardised no visto en el corpus.

Fixture de texto minimo escrito a un archivo temporal -- no toca el CSV
real (data/raw/ esta fuera del repo) ni Postgres.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from cargar_opendengue import leer_serie_nacional_semanal  # noqa: E402


CABECERA = "S_res,T_res,case_definition_standardised,calendar_start_date,dengue_total"


def _csv(tmp_path: Path, filas: list[str]) -> Path:
    ruta = tmp_path / "opendengue.csv"
    ruta.write_text("\n".join([CABECERA, *filas]) + "\n", encoding="utf-8")
    return ruta


def test_filtra_a_admin0_week_total(tmp_path):
    ruta = _csv(
        tmp_path,
        [
            "Admin0,Week,Total,2018-01-01,10",
            "Admin0,Week,Total,2018-01-08,20",
            "Admin1,Week,Total,2018-01-01,5",       # otra resolucion espacial
            "Admin0,Month,Total,2018-01-01,99",     # otra resolucion temporal
        ],
    )

    assert leer_serie_nacional_semanal(ruta) == [
        ("2018-01-01", 10),
        ("2018-01-08", 20),
    ]


def test_case_definition_inesperado_es_error(tmp_path):
    ruta = _csv(tmp_path, ["Admin0,Week,Confirmed,2018-01-01,10"])

    with pytest.raises(ValueError, match="case_definition_standardised inesperado: 'Confirmed'"):
        leer_serie_nacional_semanal(ruta)
