"""Pruebas HTTP de GET /api/alertas. Se omiten si Postgres no responde."""

from __future__ import annotations

import json
import os
import re
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

from api.alertas import (  # noqa: E402
    AVISO_HONESTIDAD_ALERTAS,
    consultar_alertas_publicas,
    listar_alertas_activas,
)
from api.main import _conexion, app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

CAMPOS_ALERTA = (
    "id",
    "tipo",
    "nivel",
    "titulo",
    "contexto",
    "indicaciones",
    "fuente",
    "autor",
    "vigente_desde",
    "vigente_hasta",
    "activa",
)

# Campos clínicos opcionales (ADR 0014). Siempre presentes en el JSON, pero
# pueden venir en null mientras el equipo no los llene con fuente oficial.
CAMPOS_CLINICOS_OPCIONALES = (
    "signos_alarma",
    "criterios_referencia",
    "que_notificar",
    "definicion_caso",
    "contacto_vigilancia",
)

TITULO_DENGUE_ACTIVA = (
    "Casos probables de dengue por encima de años comparables en 2023"
)
TITULO_RESPIRATORIO_ACTIVA = (
    "IRA y detecciones virales por encima de años comparables en 2023"
)
TITULO_INACTIVA = "Vigilancia rutinaria de dengue (cerrada el 31/08/2026)"

LENGUAJE_PREDICTIVO = re.compile(r"va a haber brote|predic", re.IGNORECASE)

# Catálogo de indicaciones (INDICACIONES_ALERTAS.md §5) para el tipo/nivel
# de las filas demo activas. El GET público debe devolver exactamente esas
# viñetas en `indicaciones`; no se regeneran desde M1–M3.
CATALOGO_INDICACIONES = {
    ("dengue", "atencion"): (
        "Aplicar la definición de caso sospechoso a todo paciente febril sin foco aparente; no esperar signos de alarma para notificar.",
        "Registrar y notificar en las primeras 24 h de la consulta.",
        "A todo caso probable: hemograma basal y clasificación (dengue sin signos de alarma / con signos de alarma / grave) según guía MINSAL vigente.",
        "Entregar hoja de signos de alarma al paciente y su acompañante; citar a control en 24-48 h durante la fase febril y al cese de la fiebre.",
        "Reportar al SIBASI la sospecha de aumento para que valore inspección entomológica y control de foco en la zona de residencia de los casos.",
        "No indicar AINE ni intramusculares en febriles sin diagnóstico.",
    ),
    ("respiratorio", "atencion"): (
        "Aplicar clasificación de IRA y buscar activamente signos de dificultad respiratoria en menores de 5 años (tiraje, taquipnea, incapacidad de beber).",
        "Usar oximetría de pulso en todo paciente con dificultad respiratoria; documentar SatO2.",
        "Reforzar criterios de neumonía y de referencia según guía MINSAL vigente.",
        "Indicar medidas de higiene respiratoria en sala de espera (ventilación, separación de sintomáticos, mascarilla al sintomático).",
        "Notificar al SIBASI el incremento de consultas por IRA para valoración.",
    ),
}


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


def _texto_plano(valor) -> str:
    if isinstance(valor, dict):
        return json.dumps(valor, ensure_ascii=False)
    if isinstance(valor, list):
        return json.dumps(valor, ensure_ascii=False)
    return str(valor)


class AlertasApiTest(unittest.TestCase):
    def setUp(self):
        if not _db_disponible():
            raise unittest.SkipTest("Postgres no disponible")
        self.client = TestClient(app)

    def test_lista_incluye_alertas_activas_sembradas(self):
        r = self.client.get("/api/alertas")
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()
        self.assertEqual(cuerpo["aviso"], AVISO_HONESTIDAD_ALERTAS)
        self.assertIsNotNone(cuerpo["ultima_revision"])
        titulos = {a["titulo"] for a in cuerpo["alertas"]}
        self.assertIn(TITULO_DENGUE_ACTIVA, titulos)
        self.assertIn(TITULO_RESPIRATORIO_ACTIVA, titulos)
        for alerta in cuerpo["alertas"]:
            for campo in CAMPOS_ALERTA:
                self.assertIn(campo, alerta)
            self.assertTrue(alerta["activa"])
            self.assertIn(alerta["tipo"], ("dengue", "respiratorio"))
            self.assertIn(
                alerta["nivel"], ("informativo", "atencion", "intensificacion")
            )
            self.assertTrue(alerta["fuente"])
            self.assertTrue(alerta["autor"])
            self.assertTrue(alerta["vigente_desde"])
            self.assertTrue(alerta["contexto"])
            self.assertTrue(alerta["indicaciones"])

    def test_campos_clinicos_opcionales_siempre_presentes(self):
        """Contenedores del ADR 0014: la clave existe aunque el valor sea null.

        El frontend decide mostrar u ocultar cada bloque según el valor; que
        la clave falte sería un cambio de contrato, no un campo vacío.
        """
        r = self.client.get("/api/alertas")
        self.assertEqual(r.status_code, 200)
        alertas = r.json()["alertas"]
        self.assertGreaterEqual(len(alertas), 1)
        for alerta in alertas:
            for campo in CAMPOS_CLINICOS_OPCIONALES:
                self.assertIn(campo, alerta)
                self.assertIsInstance(alerta[campo], (str, type(None)))

    def test_filtro_tipo_no_mezcla_dengue_con_respiratorio(self):
        r = self.client.get("/api/alertas", params={"tipo": "dengue"})
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()
        self.assertGreaterEqual(len(cuerpo["alertas"]), 1)
        tipos = {a["tipo"] for a in cuerpo["alertas"]}
        self.assertEqual(tipos, {"dengue"})
        titulos = {a["titulo"] for a in cuerpo["alertas"]}
        self.assertIn(TITULO_DENGUE_ACTIVA, titulos)
        self.assertNotIn(TITULO_RESPIRATORIO_ACTIVA, titulos)

        r2 = self.client.get("/api/alertas", params={"tipo": "respiratorio"})
        self.assertEqual(r2.status_code, 200)
        tipos2 = {a["tipo"] for a in r2.json()["alertas"]}
        self.assertEqual(tipos2, {"respiratorio"})
        self.assertIn(
            TITULO_RESPIRATORIO_ACTIVA,
            {a["titulo"] for a in r2.json()["alertas"]},
        )

    def test_inactivas_no_aparecen(self):
        r = self.client.get("/api/alertas")
        self.assertEqual(r.status_code, 200)
        titulos = {a["titulo"] for a in r.json()["alertas"]}
        self.assertNotIn(TITULO_INACTIVA, titulos)
        r_dengue = self.client.get("/api/alertas", params={"tipo": "dengue"})
        titulos_dengue = {a["titulo"] for a in r_dengue.json()["alertas"]}
        self.assertNotIn(TITULO_INACTIVA, titulos_dengue)

    def test_indicaciones_siguen_catalogo_del_nivel(self):
        r = self.client.get("/api/alertas")
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()
        vistos = {(a["tipo"], a["nivel"]) for a in cuerpo["alertas"]}
        self.assertIn(("dengue", "atencion"), vistos)
        self.assertIn(("respiratorio", "atencion"), vistos)
        for alerta in cuerpo["alertas"]:
            viñetas = CATALOGO_INDICACIONES.get((alerta["tipo"], alerta["nivel"]))
            if viñetas is None:
                continue
            for viñeta in viñetas:
                self.assertIn(viñeta, alerta["indicaciones"])

    def test_payload_sin_lenguaje_de_prediccion(self):
        r = self.client.get("/api/alertas")
        self.assertEqual(r.status_code, 200)
        plano = _texto_plano(r.json())
        self.assertIsNone(LENGUAJE_PREDICTIVO.search(plano))

    def test_consulta_unitaria_coincide_con_http(self):
        r = self.client.get("/api/alertas", params={"tipo": "dengue"})
        self.assertEqual(r.status_code, 200)
        with _conexion() as conn:
            directo = consultar_alertas_publicas(conn, tipo="dengue")
            solo_activas = listar_alertas_activas(conn, tipo="dengue")
        self.assertEqual(r.json()["alertas"], directo["alertas"])
        self.assertEqual(r.json()["alertas"], solo_activas)
        self.assertTrue(all(a["activa"] for a in solo_activas))
        self.assertTrue(all(a["tipo"] == "dengue" for a in solo_activas))

    def test_tipo_invalido_422(self):
        r = self.client.get("/api/alertas", params={"tipo": "otro"})
        self.assertEqual(r.status_code, 422)

    def test_no_hay_alta_por_http(self):
        r = self.client.post("/api/alertas", json={"titulo": "no"})
        self.assertEqual(r.status_code, 405)
