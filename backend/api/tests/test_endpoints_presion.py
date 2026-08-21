"""Pruebas de los endpoints /api/v1/presion/current y
/api/v1/presion/temporal/{departamento_id} (Modulo 3 de "El Camino Ancho").

Usan FastAPI TestClient contra la base de datos real (Postgres ya cargado
con el seed de datos MINSAL desacumulados, ver ADR 0010) -- mismo patron
que test_endpoints_idoneidad.py: la suite se omite (no falla) si la base
no esta disponible, en vez de introducir mocks que ningun otro archivo de
pruebas usa.

Los valores esperados de los casos "con datos reales" (semana 24 de 2019 en
presion alta, semanas 51/52 insuficientes) se verificaron a mano contra la
base sembrada por db/seed/seed_datos_reales.sql el 2026-08-21 -- si el seed
se regenera con otra ventana de datos, revisar estos numeros.
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

load_dotenv(REPO_ROOT / ".env", override=False)
os.environ.setdefault("POSTGRES_HOST", "localhost")

sys.path.insert(0, str(BACKEND_DIR))

from api.main import app  # noqa: E402
from api.presion import NOTA_INSUFICIENTE  # noqa: E402
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


# M3 es descriptivo: nada de alertas binarias ni lenguaje predictivo.
CAMPOS_RETIRADOS = {
    "lead_time_weeks",
    "lead_time",
    "estimated_transmission_window_start",
    "season_shift_alert",
    "alerta",
    "alert",
    "riesgo",
    "etiqueta_predicha",
}


class PresionCurrentTest(unittest.TestCase):
    def setUp(self):
        if not _db_disponible():
            raise unittest.SkipTest(
                "Postgres no disponible en POSTGRES_HOST (esperado localhost:5432 via "
                "docker-compose) -- se omite la suite en vez de mockear la capa de datos."
            )
        self.client = TestClient(app)

    def test_respuesta_ok_y_forma_esperada(self):
        r = self.client.get("/api/v1/presion/current", params={"week": 24, "year": 2019})
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()

        self.assertEqual(cuerpo["semana_epi"], 24)
        self.assertEqual(cuerpo["anio"], 2019)
        self.assertIn("aviso", cuerpo)
        self.assertEqual(len(cuerpo["departamentos"]), 14)

        for depto in cuerpo["departamentos"]:
            self.assertIn("codigo", depto)
            self.assertIn("nombre", depto)
            # Dos series separadas, nunca fusionadas.
            for serie in ("probable", "confirmado"):
                celda = depto[serie]
                for campo in ("casos_observados", "percentil", "categoria",
                              "p50_baseline", "p75_baseline",
                              "n_obs_baseline", "anios_baseline"):
                    self.assertIn(campo, celda)
                if celda["percentil"] is not None:
                    self.assertGreaterEqual(celda["percentil"], 0.0)
                    self.assertLessEqual(celda["percentil"], 100.0)
                    self.assertIn(celda["categoria"], ("baja", "media", "alta"))
                else:
                    self.assertIn("nota", celda)
                self.assertFalse(CAMPOS_RETIRADOS & celda.keys())
            self.assertFalse(CAMPOS_RETIRADOS & depto.keys())

    def test_2019_semana_pico_tiene_presion_alta_real(self):
        # 2019 es el anio del pico historico nacional; en la semana 24 el
        # seed real trae p.ej. SV-SO con 39 casos probables (percentil 100
        # contra su propio baseline). Verificado a mano contra la base.
        r = self.client.get("/api/v1/presion/current", params={"week": 24, "year": 2019})
        cuerpo = r.json()
        por_codigo = {d["codigo"]: d for d in cuerpo["departamentos"]}

        sonsonate = por_codigo["SV-SO"]["probable"]
        self.assertEqual(sonsonate["categoria"], "alta")
        self.assertEqual(sonsonate["casos_observados"], 39.0)
        self.assertEqual(sonsonate["percentil"], 100.0)

        altas = [
            d["codigo"]
            for d in cuerpo["departamentos"]
            if d["probable"]["categoria"] == "alta"
        ]
        self.assertGreaterEqual(len(altas), 3)

    def test_celda_insuficiente_devuelve_null_con_nota(self):
        # Semana 52 de 2021, serie probable: 0 de los 4 anios leave-one-out
        # tienen observaciones en la ventana +-1 (verificado a mano) -- debe
        # salir null + nota, nunca un valor inventado.
        r = self.client.get("/api/v1/presion/current", params={"week": 52, "year": 2021})
        cuerpo = r.json()
        por_codigo = {d["codigo"]: d for d in cuerpo["departamentos"]}

        celda = por_codigo["SV-SS"]["probable"]
        self.assertIsNone(celda["percentil"])
        self.assertIsNone(celda["categoria"])
        self.assertEqual(celda["nota"], NOTA_INSUFICIENTE)

    def test_semana_invalida_devuelve_422(self):
        r = self.client.get("/api/v1/presion/current", params={"week": 0, "year": 2019})
        self.assertEqual(r.status_code, 422)
        r2 = self.client.get("/api/v1/presion/current", params={"week": 54, "year": 2019})
        self.assertEqual(r2.status_code, 422)

    def test_parametros_requeridos(self):
        r = self.client.get("/api/v1/presion/current")
        self.assertEqual(r.status_code, 422)


class PresionTemporalTest(unittest.TestCase):
    def setUp(self):
        if not _db_disponible():
            raise unittest.SkipTest(
                "Postgres no disponible en POSTGRES_HOST -- se omite la suite."
            )
        self.client = TestClient(app)

    def test_respuesta_ok_y_forma_esperada(self):
        r = self.client.get("/api/v1/presion/temporal/SV-SS", params={"anio": 2019})
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()

        self.assertEqual(cuerpo["departamento_codigo"], "SV-SS")
        self.assertEqual(cuerpo["anio"], 2019)
        self.assertIn("aviso", cuerpo)
        self.assertGreater(len(cuerpo["semanas"]), 0)
        for semana in cuerpo["semanas"]:
            self.assertIn("semana_epi", semana)
            self.assertIn("probable", semana)
            self.assertIn("confirmado", semana)

    def test_departamento_inexistente_devuelve_404(self):
        r = self.client.get("/api/v1/presion/temporal/SV-XX", params={"anio": 2019})
        self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
