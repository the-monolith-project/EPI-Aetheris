"""
Cobertura de formatear_recall_alto (entrenar_clasificador.py): el formateo
de la metrica de recall de la clase 'alto' para el panel.

El clasificador esta retirado (pivote 'Camino Ancho') pero su codigo sigue
en el repo como referencia historica; esta prueba solo fija el contrato de
presentacion. Se salta si sklearn no esta instalado (el modulo lo importa
a nivel de modulo), igual que las pruebas con Postgres se saltan sin DB.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("sklearn")

sys.path.insert(0, str(Path(__file__).parent.parent))

from entrenar_clasificador import formatear_recall_alto  # noqa: E402


def test_none_devuelve_nota_de_soporte():
    assert formatear_recall_alto(None, 42) == (
        "N/A -- 0 casos reales de 'alto' en el conjunto evaluado (42 soporte)"
    )


def test_valores_se_formatean_a_tres_decimales():
    assert formatear_recall_alto(0.0, 10) == "0.000"
    assert formatear_recall_alto(1.0, 10) == "1.000"
    assert formatear_recall_alto(0.52341, 10) == "0.523"
    assert formatear_recall_alto(0.9999, 10) == "1.000"
