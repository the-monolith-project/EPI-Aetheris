import sys
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

# Add backend/ingestion to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cargar_opendengue import leer_serie_nacional_semanal


def test_leer_serie_nacional_semanal_happy_path():
    csv_content = """ADM0_NAME,S_res,T_res,calendar_start_date,case_definition_standardised,dengue_total
El Salvador,Admin0,Week,2018-01-01,Total,10
El Salvador,Admin0,Week,2018-01-08,Total,20
El Salvador,Admin1,Week,2018-01-01,Total,5
El Salvador,Admin0,Month,2018-01-01,Total,30
"""
    with patch("builtins.open", mock_open(read_data=csv_content)):
        filas = leer_serie_nacional_semanal(Path("dummy.csv"))

    assert len(filas) == 2
    assert filas[0] == ("2018-01-01", 10)
    assert filas[1] == ("2018-01-08", 20)


def test_leer_serie_nacional_semanal_unexpected_case_definition():
    csv_content = """ADM0_NAME,S_res,T_res,calendar_start_date,case_definition_standardised,dengue_total
El Salvador,Admin0,Week,2018-01-01,Confirmed,10
"""
    with patch("builtins.open", mock_open(read_data=csv_content)):
        with pytest.raises(
            ValueError, match="case_definition_standardised inesperado: 'Confirmed'"
        ):
            leer_serie_nacional_semanal(Path("dummy.csv"))
