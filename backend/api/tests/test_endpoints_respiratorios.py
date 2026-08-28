"""Pruebas HTTP de /api/neumonias/* y /api/respiratorios/*. Se omiten si Postgres no responde."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

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
        import psycopg2
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


class NeumoniasApiTest(unittest.TestCase):
    def setUp(self):
        if not _db_disponible():
            raise unittest.SkipTest("Postgres no disponible")
        self.client = TestClient(app)

    def test_departamental_tiene_aviso_y_14_deptos(self):
        r = self.client.get("/api/neumonias/departamental")
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()
        self.assertIn("aviso", cuerpo)
        self.assertIn("MINSAL", cuerpo["aviso"])
        self.assertEqual(len(cuerpo["departamentos"]), 14)
        self.assertNotIn("riesgo", cuerpo["aviso"].lower())

    def test_temporal_san_salvador(self):
        r = self.client.get("/api/neumonias/temporal/SV-SS")
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()
        self.assertEqual(cuerpo["unidad"], "conteo_notificado")
        self.assertIn("2018", cuerpo["series"])
        self.assertEqual(cuerpo["series"]["2018"][0][0], 3)  # primer corte semanal usable SE3

    def test_temporal_codigo_invalido(self):
        r = self.client.get("/api/neumonias/temporal/XX-ZZ")
        self.assertEqual(r.status_code, 404)


class VirusApiTest(unittest.TestCase):
    def setUp(self):
        if not _db_disponible():
            raise unittest.SkipTest("Postgres no disponible")
        self.client = TestClient(app)

    def test_catalogo_distingue_unidades(self):
        r = self.client.get("/api/respiratorios/virus")
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()
        self.assertEqual(cuerpo["granularidad"], "nacional")
        unidades = {s["unidad"] for s in cuerpo["series"]}
        self.assertIn("conteo", unidades)
        self.assertIn("porcentaje", unidades)

    def test_temporal_vsr_detecciones(self):
        r = self.client.get("/api/respiratorios/temporal", params={"virus": "vsr", "metrica": "detecciones"})
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()
        self.assertEqual(cuerpo["unidad"], "conteo")
        self.assertEqual(cuerpo["metrica"], "detecciones")
        self.assertIn("causalidad", cuerpo["aviso"])

    def test_semana_nacional(self):
        r = self.client.get("/api/respiratorios/semana/2023/25")
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()
        metricas = {o["metrica"] for o in cuerpo["observaciones"]}
        self.assertTrue(metricas <= {"muestras_analizadas", "muestras_positivas", "detecciones", "positividad"})
