"""Equivalencia del dataset analitico con los endpoints vigentes de M1/M2/M3."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

API_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = API_DIR.parent
REPO_ROOT = BACKEND_DIR.parent

load_dotenv(REPO_ROOT / ".env", override=False)
os.environ.setdefault("POSTGRES_HOST", "localhost")

sys.path.insert(0, str(BACKEND_DIR))

from api.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def _db_disponible() -> bool:
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            connect_timeout=3,
        )
        conn.close()
        return True
    except Exception:
        return False


class DatasetAnaliticoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not _db_disponible():
            raise unittest.SkipTest("Postgres no disponible -- se omite la suite de integracion.")
        cls.client = TestClient(app)
        respuesta = cls.client.get("/api/v1/analisis/dengue", params={"year": 2019})
        if respuesta.status_code != 200:
            raise AssertionError(respuesta.text)
        cls.cuerpo = respuesta.json()

    def test_forma_anual_y_departamentos_esperados(self):
        self.assertEqual(self.cuerpo["anio"], 2019)
        self.assertEqual(self.cuerpo["anios_disponibles"], [2018, 2019, 2021, 2022, 2023])
        self.assertEqual(self.cuerpo["series"], ["probable", "confirmado"])
        self.assertEqual(len(self.cuerpo["departamentos"]), 14)

        for departamento in self.cuerpo["departamentos"]:
            self.assertEqual(
                [fila["semana_epi"] for fila in departamento["semanas"]],
                list(range(1, 54)),
            )

    def test_equivalencia_con_endpoints_originales(self):
        por_codigo = {d["codigo"]: d for d in self.cuerpo["departamentos"]}

        for semana in (24, 52):
            espacial = self.client.get(
                "/api/v1/spatial/current", params={"week": semana, "year": 2019}
            ).json()
            presion = self.client.get(
                "/api/v1/presion/current", params={"week": semana, "year": 2019}
            ).json()

            espacial_codigo = {d["codigo"]: d for d in espacial["departamentos"]}
            presion_codigo = {d["codigo"]: d for d in presion["departamentos"]}

            for codigo, departamento in por_codigo.items():
                fila = departamento["semanas"][semana - 1]
                self.assertEqual(fila["iv"], espacial_codigo[codigo]["iv"])
                self.assertEqual(
                    fila["anomaly_sigma"], espacial_codigo[codigo]["anomaly_sigma"]
                )
                self.assertEqual(fila["presion_probable"], presion_codigo[codigo]["probable"])
                self.assertEqual(
                    fila["presion_confirmado"], presion_codigo[codigo]["confirmado"]
                )
                self.assertEqual(
                    fila["probable"], fila["presion_probable"]["casos_observados"]
                )
                self.assertEqual(
                    fila["confirmado"], fila["presion_confirmado"]["casos_observados"]
                )

    def test_huecos_permanecen_null(self):
        celdas = [
            fila
            for departamento in self.cuerpo["departamentos"]
            for fila in departamento["semanas"]
        ]
        huecos = [
            fila
            for fila in celdas
            if fila["probable"] is None or fila["confirmado"] is None
        ]
        self.assertGreater(len(huecos), 0)
        for fila in huecos:
            if fila["probable"] is None:
                self.assertIsNone(fila["presion_probable"]["percentil"])
            if fila["confirmado"] is None:
                self.assertIsNone(fila["presion_confirmado"]["percentil"])

    def test_2020_no_se_ofrece_como_anio_departamental(self):
        respuesta = self.client.get("/api/v1/analisis/dengue", params={"year": 2020})
        self.assertEqual(respuesta.status_code, 422)

    def test_casos_nacional_agrega_semana_sin_romper_campos_previos(self):
        respuesta = self.client.get("/api/casos-nacional")
        self.assertEqual(respuesta.status_code, 200)
        filas = respuesta.json()
        self.assertGreater(len(filas), 0)
        for fila in filas:
            self.assertIn("semana_inicio", fila)
            self.assertIn("anio", fila)
            self.assertIn("conteo", fila)
            self.assertIn("semana_epi", fila)
            self.assertGreaterEqual(fila["semana_epi"], 1)
            self.assertLessEqual(fila["semana_epi"], 53)

    def test_procedencia_de_observacion_conserva_fuente_y_boletin(self):
        departamento = self.cuerpo["departamentos"][0]
        fila = next(
            semana
            for semana in departamento["semanas"]
            if semana["probable"] is not None
        )
        respuesta = self.client.get(
            "/api/v1/analisis/dengue/procedencia",
            params={
                "year": self.cuerpo["anio"],
                "week": fila["semana_epi"],
                "dept": departamento["codigo"],
                "serie": "probable",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertTrue(cuerpo["disponible"])
        self.assertEqual(cuerpo["conteo_observado"], fila["probable"])
        self.assertGreater(len(cuerpo["registros"]), 0)
        registro = cuerpo["registros"][0]
        self.assertEqual(registro["fuente"]["codigo"], "minsal_pdf")
        self.assertIsNotNone(registro["boletin"])
        self.assertTrue(registro["boletin"]["nombre_archivo"])
        self.assertTrue(registro["fecha_ingesta"])

    def test_procedencia_no_inventa_registro_para_hueco(self):
        departamento = self.cuerpo["departamentos"][0]
        fila = next(
            semana
            for semana in departamento["semanas"]
            if semana["probable"] is None
        )
        respuesta = self.client.get(
            "/api/v1/analisis/dengue/procedencia",
            params={
                "year": self.cuerpo["anio"],
                "week": fila["semana_epi"],
                "dept": departamento["codigo"],
                "serie": "probable",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertFalse(cuerpo["disponible"])
        self.assertIsNone(cuerpo["conteo_observado"])
        self.assertEqual(cuerpo["registros"], [])

    def test_procedencia_rechaza_seleccion_invalida(self):
        casos = (
            ({"year": 2020, "week": 1, "dept": "SV-SS", "serie": "probable"}, 422),
            ({"year": 2019, "week": 0, "dept": "SV-SS", "serie": "probable"}, 422),
            ({"year": 2019, "week": 1, "dept": "SV-SS", "serie": "total"}, 422),
            ({"year": 2019, "week": 1, "dept": "SV-X", "serie": "probable"}, 404),
        )
        for parametros, esperado in casos:
            with self.subTest(parametros=parametros):
                respuesta = self.client.get(
                    "/api/v1/analisis/dengue/procedencia",
                    params=parametros,
                )
                self.assertEqual(respuesta.status_code, esperado)


if __name__ == "__main__":
    unittest.main()
