"""Ventana climática A1 (ADR 0018): tope del archive y ANIOS_CLIMA.

No llama a Open-Meteo ni a Postgres. Importa la función real de
cargar_clima.py (fecha_fin_archivo) y la constante de idoneidad.py.
"""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
INGESTION_DIR = BACKEND_DIR / "ingestion"
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(INGESTION_DIR))

from api import idoneidad as api_iv  # noqa: E402
import cargar_clima as loader  # noqa: E402


class FechaFinArchivoTest(unittest.TestCase):
    def test_anio_cerrado_en_el_pasado_llega_al_31_de_diciembre(self):
        hoy = date(2026, 9, 8)
        self.assertEqual(loader.fecha_fin_archivo(2024, hoy=hoy), date(2024, 12, 31))
        self.assertEqual(loader.fecha_fin_archivo(2025, hoy=hoy), date(2025, 12, 31))

    def test_anio_en_curso_no_pide_diciembre_futuro(self):
        hoy = date(2026, 9, 8)
        self.assertEqual(loader.fecha_fin_archivo(2026, hoy=hoy), hoy)

    def test_anio_futuro_tambien_recorta_a_hoy(self):
        hoy = date(2026, 9, 8)
        self.assertEqual(loader.fecha_fin_archivo(2027, hoy=hoy), hoy)

    def test_rango_invertido_si_el_inicio_queda_despues_de_hoy(self):
        hoy = date(2026, 9, 8)
        with self.assertRaises(ValueError):
            loader.rango_archivo(2027, 2027, hoy=hoy)

    def test_rango_del_anio_en_curso_empieza_en_enero_y_corta_hoy(self):
        hoy = date(2026, 9, 8)
        inicio, fin = loader.rango_archivo(2026, 2026, hoy=hoy)
        self.assertEqual(inicio, date(2026, 1, 1))
        self.assertEqual(fin, hoy)

    def test_default_de_anio_fin_es_el_anio_en_curso(self):
        self.assertEqual(loader.ANIO_FIN_DEFAULT, date.today().year)


class AniosClimaTest(unittest.TestCase):
    def test_corpus_empieza_en_2014_y_llega_al_anio_actual(self):
        self.assertEqual(api_iv.ANIOS_CLIMA[0], 2014)
        self.assertEqual(api_iv.ANIOS_CLIMA[-1], date.today().year)
        self.assertEqual(
            api_iv.ANIOS_CLIMA, list(range(2014, date.today().year + 1))
        )


class MapaCapaClimaTest(unittest.TestCase):
    def test_iv_y_anomalia_pegan_a_spatial_current(self):
        fuente = (
            REPO_ROOT / "web/src/components/MapaDepartamentos.astro"
        ).read_text(encoding="utf-8")
        self.assertIn("/api/v1/spatial/current", fuente)
        self.assertIn("week=${SEMANA_ESPACIAL}", fuente)
        self.assertIn("year=${ANIO_ESPACIAL}", fuente)
        self.assertNotIn(
            "obtenerDatasetAnalitico(ANIO_ESPACIAL)",
            fuente.split("async function obtenerDatosEspaciales")[1].split(
                "async function obtenerDatosPresion"
            )[0],
        )


if __name__ == "__main__":
    unittest.main()
