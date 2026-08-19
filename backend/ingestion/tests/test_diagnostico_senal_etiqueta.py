"""Pruebas unitarias del diagnostico auditable, sin Postgres ni red."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from sklearn.dummy import DummyClassifier

sys.path.insert(0, str(Path(__file__).parent.parent))

from diagnostico_senal_etiqueta_auditable import (  # noqa: E402
    ANIOS_BASE,
    CLASES,
    _retroceder,
    etiquetar_canal,
    evaluar,
    percentil,
)


class DiagnosticoSenalEtiquetaTest(unittest.TestCase):
    def test_percentil_interpola_linealmente(self):
        self.assertAlmostEqual(percentil([0.0, 10.0], 0.75), 7.5)

    def test_etiqueta_usa_ventana_mas_menos_uno_y_excluye_anio_objetivo(self):
        serie = {}
        for anio in ANIOS_BASE:
            serie[anio] = {9: 10.0, 10: 10.0, 11: 10.0}

        # Estos extremos pertenecen al propio anio objetivo y no deben alterar
        # su pool. Los otros cuatro anios aportan 3 observaciones cada uno.
        serie[2018] = {9: 10_000.0, 10: 11.0, 11: 10_000.0}

        etiquetas = etiquetar_canal(serie)

        self.assertEqual(etiquetas[(2018, 10)], "alto")

    def test_retroceso_climatico_cruza_el_limite_de_anio_real(self):
        clima = {(2020, semana): {} for semana in range(1, 54)}
        clima[(2021, 1)] = {}

        self.assertEqual(_retroceder(2021, 1, 1, clima), (2020, 53))
        self.assertEqual(_retroceder(2021, 1, 2, clima), (2020, 52))

    def test_anio_sin_alto_conserva_f1_macro_de_tres_clases_y_recall_na(self):
        filas = [
            {"anio": 2018, "semana": 1, "casos": 1.0, "etiqueta": "bajo", "x": 0.0},
            {"anio": 2018, "semana": 2, "casos": 1.0, "etiqueta": "bajo", "x": 0.0},
            {"anio": 2019, "semana": 1, "casos": 1.0, "etiqueta": "bajo", "x": 0.0},
            {"anio": 2019, "semana": 2, "casos": 1.0, "etiqueta": "bajo", "x": 0.0},
        ]

        resultado = evaluar(
            filas,
            anio_prueba=2019,
            cols=["x"],
            modelo=DummyClassifier(strategy="most_frequent"),
        )

        self.assertIsNone(resultado["recall_alto_modelo"])
        self.assertEqual(resultado["soporte_alto"], 0)
        self.assertAlmostEqual(resultado["f1_macro_modelo"], 1 / len(CLASES))
        self.assertAlmostEqual(resultado["f1_macro_base"], 1 / len(CLASES))


if __name__ == "__main__":
    unittest.main()
