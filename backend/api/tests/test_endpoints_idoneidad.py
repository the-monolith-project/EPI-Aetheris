"""Pruebas de los endpoints /api/v1/spatial/current y
/api/v1/temporal/{departamento_id} (Modulos 1 y 2 de "El Camino Ancho" v3).

Usan FastAPI TestClient contra la base de datos real (Postgres ya cargado
con clima ERA5-Land/ERA5 2014-2024, ver CLAUDE.md) -- no hay mocks de la
capa de datos en este repositorio todavia, y estos endpoints no cambian
nada en Postgres (solo SELECT). Igual que
backend/ingestion/tests/test_validar_via_cero.py, la suite se omite (no
falla) si la base de datos no esta disponible, en vez de forzar un mock
nuevo que ningun otro archivo de pruebas usa.

Requiere POSTGRES_HOST=localhost (puerto publicado por docker-compose) y
las credenciales de .env -- se cargan aqui via python-dotenv, igual que
backend/ingestion/db.py, sin introducir una segunda convencion.
"""

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

# No pisar variables ya definidas explicitamente en el entorno (p.ej.
# POSTGRES_HOST=localhost pasado a mano al correr pytest).
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


CAMPOS_RETIRADOS = {
    "lead_time_weeks",
    "lead_time",
    "estimated_transmission_window_start",
    "season_shift_alert",
    "alerta",
    "alert",
}


class SpatialCurrentTest(unittest.TestCase):
    def setUp(self):
        if not _db_disponible():
            raise unittest.SkipTest(
                "Postgres no disponible en POSTGRES_HOST (esperado localhost:5432 via "
                "docker-compose) -- se omite la suite en vez de mockear la capa de datos."
            )
        self.client = TestClient(app)

    def test_respuesta_ok_y_forma_esperada(self):
        r = self.client.get("/api/v1/spatial/current", params={"week": 20, "year": 2019})
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()

        self.assertEqual(cuerpo["semana_epi"], 20)
        self.assertEqual(cuerpo["anio"], 2019)
        self.assertIn("aviso", cuerpo)
        self.assertIn("departamentos", cuerpo)
        self.assertEqual(len(cuerpo["departamentos"]), 14)

        for depto in cuerpo["departamentos"]:
            self.assertIn("codigo", depto)
            self.assertIn("nombre", depto)
            self.assertIn("iv", depto)
            self.assertIn("anomaly_sigma", depto)
            if depto["iv"] is not None:
                self.assertGreaterEqual(depto["iv"], 0.0)
                self.assertLessEqual(depto["iv"], 1.0)
            # Sin campos de lead time / alerta binaria: esa tesis quedo
            # retirada tras la validacion empirica (ver idoneidad.py).
            self.assertFalse(CAMPOS_RETIRADOS & depto.keys())

        self.assertFalse(CAMPOS_RETIRADOS & cuerpo.keys())

    def test_semana_invalida_devuelve_422(self):
        r = self.client.get("/api/v1/spatial/current", params={"week": 0, "year": 2019})
        self.assertEqual(r.status_code, 422)
        r2 = self.client.get("/api/v1/spatial/current", params={"week": 54, "year": 2019})
        self.assertEqual(r2.status_code, 422)

    def test_parametros_requeridos(self):
        r = self.client.get("/api/v1/spatial/current")
        self.assertEqual(r.status_code, 422)


class TemporalDepartamentoTest(unittest.TestCase):
    def setUp(self):
        if not _db_disponible():
            raise unittest.SkipTest(
                "Postgres no disponible en POSTGRES_HOST -- se omite la suite."
            )
        self.client = TestClient(app)

    def test_respuesta_ok_y_forma_esperada(self):
        r = self.client.get("/api/v1/temporal/SV-SS", params={"anio": 2019})
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()

        self.assertEqual(cuerpo["departamento_codigo"], "SV-SS")
        self.assertEqual(cuerpo["anio"], 2019)
        self.assertIn("aviso", cuerpo)
        self.assertGreater(len(cuerpo["semanas"]), 0)
        self.assertFalse(CAMPOS_RETIRADOS & cuerpo.keys())

        for fila in cuerpo["semanas"]:
            self.assertIn("semana_epi", fila)
            self.assertIn("iv_real", fila)
            self.assertIn("p25_baseline", fila)
            self.assertIn("mediana_baseline", fila)
            self.assertIn("p75_baseline", fila)
            self.assertIn("anomaly_sigma", fila)
            self.assertFalse(CAMPOS_RETIRADOS & fila.keys())

            if fila["p25_baseline"] is not None and fila["p75_baseline"] is not None:
                self.assertLessEqual(fila["p25_baseline"], fila["p75_baseline"])
            if fila["mediana_baseline"] is not None and fila["p25_baseline"] is not None:
                self.assertLessEqual(fila["p25_baseline"], fila["mediana_baseline"])

    def test_departamento_inexistente_devuelve_404(self):
        r = self.client.get("/api/v1/temporal/XX-NO-EXISTE", params={"anio": 2019})
        self.assertEqual(r.status_code, 404)

    def test_falta_anio_devuelve_422(self):
        r = self.client.get("/api/v1/temporal/SV-SS")
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main()
