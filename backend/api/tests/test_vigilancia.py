"""Pruebas del motor de integridad de vigilancia (Modulo 4).

Solo logica pura -- no toca Postgres. Los numeros son insumos sinteticos
para verificar completitud, cuadre y antiguedad, NO datos epidemiologicos
reales: la verificacion contra la base vive en test_endpoints_vigilancia.py.
"""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from api import vigilancia  # noqa: E402
from epiweeks import Week  # noqa: E402


CATALOGO = [
    ("SV-AH", "Ahuachapán"),
    ("SV-CA", "Cabañas"),
    ("SV-CH", "Chalatenango"),
    ("SV-CU", "Cuscatlán"),
    ("SV-LI", "La Libertad"),
    ("SV-PA", "La Paz"),
    ("SV-SA", "Santa Ana"),
    ("SV-SM", "San Miguel"),
    ("SV-SO", "Sonsonate"),
    ("SV-SS", "San Salvador"),
    ("SV-SV", "San Vicente"),
    ("SV-UN", "La Unión"),
    ("SV-US", "Usulután"),
    ("SV-MO", "Morazán"),
]


class CompletitudSemanaTest(unittest.TestCase):
    def test_catorce_de_catorce(self):
        presentes = {codigo for codigo, _ in CATALOGO}
        resultado = vigilancia.completitud_semana(CATALOGO, presentes)
        self.assertEqual(resultado["n"], 14)
        self.assertEqual(resultado["esperado"], 14)
        self.assertEqual(resultado["ratio"], 1.0)
        self.assertTrue(all(d["presente"] for d in resultado["departamentos"]))

    def test_hueco_no_es_cero(self):
        # 12 departamentos con fila; los 2 ausentes quedan presente=False,
        # no se fabrican como conteo 0.
        presentes = {codigo for codigo, _ in CATALOGO if codigo not in ("SV-SS", "SV-MO")}
        resultado = vigilancia.completitud_semana(CATALOGO, presentes)
        self.assertEqual(resultado["n"], 12)
        self.assertEqual(resultado["esperado"], 14)
        self.assertEqual(resultado["ratio"], round(12 / 14, 4))
        por_codigo = {d["codigo"]: d["presente"] for d in resultado["departamentos"]}
        self.assertFalse(por_codigo["SV-SS"])
        self.assertFalse(por_codigo["SV-MO"])
        self.assertTrue(por_codigo["SV-AH"])

    def test_catalogo_vacio_no_divide_por_cero(self):
        resultado = vigilancia.completitud_semana([], set())
        self.assertEqual(resultado["n"], 0)
        self.assertEqual(resultado["esperado"], 0)
        self.assertIsNone(resultado["ratio"])


class CompletitudAnualTest(unittest.TestCase):
    def test_cuenta_semanas_completas_sin_inventar_huecos(self):
        # 3 semanas con 14/14, 1 semana con 10/14, el resto del año no
        # aparece -- no se rellenan como n=0.
        semanas_n = {1: 14, 2: 14, 3: 10, 10: 14}
        resultado = vigilancia.completitud_anual(semanas_n)
        self.assertEqual(resultado["semanas_completas"], 3)
        self.assertEqual(resultado["semanas_con_dato"], 4)
        self.assertEqual(resultado["semanas_nominales"], 52)

    def test_anio_sin_filas(self):
        resultado = vigilancia.completitud_anual({})
        self.assertEqual(resultado["semanas_completas"], 0)
        self.assertEqual(resultado["semanas_con_dato"], 0)


class CuadreTest(unittest.TestCase):
    def test_discrepancia_es_suma_menos_publicado(self):
        self.assertEqual(vigilancia.discrepancia(384, 386), -2)
        self.assertEqual(vigilancia.discrepancia(88, 89), -1)
        self.assertEqual(vigilancia.discrepancia(100, 100), 0)

    def test_discrepancia_none_si_falta_un_lado(self):
        self.assertIsNone(vigilancia.discrepancia(None, 10))
        self.assertIsNone(vigilancia.discrepancia(10, None))
        self.assertIsNone(vigilancia.discrepancia(None, None))

    def test_boletin_ausente_no_se_marca_como_no_cuadra(self):
        resultado = vigilancia.cuadre_boletin(None)
        self.assertIsNone(resultado["cuadra"])
        self.assertIsNone(resultado["estado"])
        self.assertIsNone(resultado["probable"]["discrepancia"])
        self.assertIsNone(resultado["confirmado"]["discrepancia"])

    def test_expone_bandera_y_magnitud_sin_recalcular(self):
        boletin = {
            "nombre_archivo": "Boletin_epidemiologico_SE302019_v2.pdf",
            "estado": "ok",
            "validacion_cuadra": False,
            "suma_departamental_probable": 384,
            "total_nacional_publicado_probable": 386,
            "suma_departamental_confirmado": 88,
            "total_nacional_publicado_confirmado": 89,
        }
        resultado = vigilancia.cuadre_boletin(boletin)
        self.assertIs(resultado["cuadra"], False)
        self.assertEqual(resultado["estado"], "ok")
        self.assertEqual(resultado["nombre_archivo"], boletin["nombre_archivo"])
        self.assertEqual(resultado["probable"]["discrepancia"], -2)
        self.assertEqual(resultado["confirmado"]["discrepancia"], -1)


class AntiguedadTest(unittest.TestCase):
    def test_semanas_desde_ultima_se_con_fecha_fija(self):
        # 8 de septiembre de 2026 cae en SE36/2026 (PAHO/CDC).
        hoy = date(2026, 9, 8)
        self.assertEqual(Week.fromdate(hoy), Week(2026, 36))
        resultado = vigilancia.antiguedad_serie((2023, 52), hoy)
        esperado = (Week(2026, 36).startdate() - Week(2023, 52).startdate()).days // 7
        self.assertEqual(resultado["ultima_anio"], 2023)
        self.assertEqual(resultado["ultima_semana_epi"], 52)
        self.assertEqual(resultado["semanas"], esperado)

    def test_misma_semana_es_cero(self):
        hoy = date(2023, 12, 24)  # SE52/2023
        self.assertEqual(Week.fromdate(hoy), Week(2023, 52))
        resultado = vigilancia.antiguedad_serie((2023, 52), hoy)
        self.assertEqual(resultado["semanas"], 0)

    def test_serie_sin_filas_no_se_convierte_en_cero(self):
        resultado = vigilancia.antiguedad_serie(None, date(2026, 9, 8))
        self.assertIsNone(resultado["ultima_anio"])
        self.assertIsNone(resultado["ultima_semana_epi"])
        self.assertIsNone(resultado["semanas"])

    def test_usa_calendario_paho_no_iso(self):
        # 1 de enero de 2023 es SE01/2023 en PAHO/CDC y semana ISO distinta
        # segun el calendario: el resultado debe coincidir con epiweeks.
        hoy = date(2023, 1, 1)
        resultado = vigilancia.antiguedad_serie((2022, 52), hoy)
        esperado = (
            Week.fromdate(hoy).startdate() - Week(2022, 52).startdate()
        ).days // 7
        self.assertEqual(resultado["semanas"], esperado)


class AvisoTest(unittest.TestCase):
    def test_aviso_niega_transmision_y_riesgo(self):
        texto = vigilancia.AVISO_HONESTIDAD_VIGILANCIA.lower()
        self.assertIn("calidad", texto)
        self.assertIn("no la transmisión ni el riesgo", texto)
        self.assertIn("no hay un índice compuesto", texto)


if __name__ == "__main__":
    unittest.main()
