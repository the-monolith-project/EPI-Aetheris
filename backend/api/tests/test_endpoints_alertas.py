"""Pruebas HTTP de /api/alertas (GET público, POST/PATCH autenticados).

Se omiten si Postgres no responde.
"""

from __future__ import annotations

import json
import os
import re
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

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

TOKEN_DUMMY = "dummy-alertas-token-test-no-secreto"
PREFIJO_FIXTURE = "TEST-ALERTAS-OPERABLES-"
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

    def tearDown(self):
        if not _db_disponible():
            return
        with _conexion() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM alertas WHERE titulo LIKE %s",
                    (PREFIJO_FIXTURE + "%",),
                )
            conn.commit()

    def _titulo_fixture(self, sufijo: str) -> str:
        return f"{PREFIJO_FIXTURE}{sufijo}-{uuid4().hex[:8]}"

    def _insertar(self, **campos) -> int:
        titulo = campos.pop("titulo", None) or self._titulo_fixture("fila")
        valores = {
            "tipo": "dengue",
            "nivel": "informativo",
            "titulo": titulo,
            "contexto": "Contexto de prueba para filtros de alertas.",
            "indicaciones": "- No actuar: fila de prueba.",
            "fuente": "Prueba automatizada, no usar en campo.",
            "autor": "suite de tests",
            "vigente_desde": date(2026, 9, 1),
            "vigente_hasta": None,
            "activa": True,
            "etiqueta": None,
        }
        valores.update(campos)
        columnas = list(valores.keys())
        placeholders = ", ".join(["%s"] * len(columnas))
        with _conexion() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO alertas ({", ".join(columnas)})
                    VALUES ({placeholders})
                    RETURNING id
                    """,
                    tuple(valores[c] for c in columnas),
                )
                (ident,) = cur.fetchone()
            conn.commit()
        return int(ident)

    def _contar_titulo(self, titulo: str) -> int:
        with _conexion() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT count(*) FROM alertas WHERE titulo = %s",
                    (titulo,),
                )
                (n,) = cur.fetchone()
        return int(n)

    def _titulos(self, params=None) -> set[str]:
        r = self.client.get("/api/alertas", params=params)
        self.assertEqual(r.status_code, 200)
        return {a["titulo"] for a in r.json()["alertas"]}

    def _auth(self, token: str = TOKEN_DUMMY) -> dict:
        return {"Authorization": f"Bearer {token}"}

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

    def test_etiqueta_test_ausente_del_get_por_defecto(self):
        titulo = self._titulo_fixture("test")
        self._insertar(titulo=titulo, etiqueta="test")
        self.assertNotIn(titulo, self._titulos())

    def test_etiquetadas_aparecen_con_flag_y_traen_etiqueta(self):
        titulo_test = self._titulo_fixture("test-flag")
        titulo_sim = self._titulo_fixture("simulacro")
        self._insertar(titulo=titulo_test, etiqueta="test")
        self._insertar(titulo=titulo_sim, etiqueta="simulacro")
        r = self.client.get(
            "/api/alertas", params={"incluir_etiquetadas": True}
        )
        self.assertEqual(r.status_code, 200)
        por_titulo = {a["titulo"]: a for a in r.json()["alertas"]}
        self.assertIn(titulo_test, por_titulo)
        self.assertEqual(por_titulo[titulo_test]["etiqueta"], "test")
        self.assertIn(titulo_sim, por_titulo)
        self.assertEqual(por_titulo[titulo_sim]["etiqueta"], "simulacro")
        self.assertNotIn(titulo_test, self._titulos())
        self.assertNotIn(titulo_sim, self._titulos())

    def test_post_sin_authorization_401_no_inserta(self):
        titulo = self._titulo_fixture("post-sin-auth")
        cuerpo = {
            "tipo": "dengue",
            "nivel": "informativo",
            "titulo": titulo,
            "contexto": "x",
            "indicaciones": "y",
            "fuente": "z",
            "autor": "suite",
            "vigente_desde": "2026-09-07",
        }
        with patch.dict(os.environ, {"ALERTAS_TOKEN": TOKEN_DUMMY}):
            r = self.client.post("/api/alertas", json=cuerpo)
        self.assertEqual(r.status_code, 401)
        self.assertEqual(self._contar_titulo(titulo), 0)

    def test_post_token_invalido_401_no_inserta(self):
        titulo = self._titulo_fixture("post-token-malo")
        cuerpo = {
            "tipo": "dengue",
            "nivel": "informativo",
            "titulo": titulo,
            "contexto": "x",
            "indicaciones": "y",
            "fuente": "z",
            "autor": "suite",
            "vigente_desde": "2026-09-07",
        }
        with patch.dict(os.environ, {"ALERTAS_TOKEN": TOKEN_DUMMY}):
            r = self.client.post(
                "/api/alertas", json=cuerpo, headers=self._auth("token-incorrecto")
            )
        self.assertEqual(r.status_code, 401)
        self.assertEqual(self._contar_titulo(titulo), 0)

    def test_post_token_valido_inserta_y_sale_en_get(self):
        titulo = self._titulo_fixture("post-ok")
        cuerpo = {
            "tipo": "dengue",
            "nivel": "informativo",
            "titulo": titulo,
            "contexto": "Contexto de alta autenticada.",
            "indicaciones": "- Revisar vigencia.",
            "fuente": "Prueba automatizada",
            "autor": "suite de tests",
            "vigente_desde": "2026-09-07",
        }
        with patch.dict(os.environ, {"ALERTAS_TOKEN": TOKEN_DUMMY}):
            r = self.client.post(
                "/api/alertas", json=cuerpo, headers=self._auth()
            )
        self.assertEqual(r.status_code, 201)
        creado = r.json()
        self.assertIn("id", creado)
        self.assertEqual(creado["titulo"], titulo)
        self.assertIn(titulo, self._titulos())

    def test_patch_desactiva_y_sigue_en_archivo(self):
        titulo = self._titulo_fixture("patch-activa")
        ident = self._insertar(titulo=titulo, activa=True)
        self.assertIn(titulo, self._titulos())
        with patch.dict(os.environ, {"ALERTAS_TOKEN": TOKEN_DUMMY}):
            r = self.client.patch(
                f"/api/alertas/{ident}",
                json={"activa": False},
                headers=self._auth(),
            )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["activa"])
        self.assertNotIn(titulo, self._titulos())
        self.assertIn(
            titulo, self._titulos(params={"incluir_inactivas": True})
        )

    def test_patch_sin_authorization_401_no_modifica(self):
        titulo = self._titulo_fixture("patch-sin-auth")
        ident = self._insertar(titulo=titulo, activa=True)
        with patch.dict(os.environ, {"ALERTAS_TOKEN": TOKEN_DUMMY}):
            r = self.client.patch(
                f"/api/alertas/{ident}", json={"activa": False}
            )
        self.assertEqual(r.status_code, 401)
        self.assertIn(titulo, self._titulos())

    def test_patch_sin_alertas_token_503(self):
        titulo = self._titulo_fixture("patch-503")
        ident = self._insertar(titulo=titulo, activa=True)
        with patch.dict(os.environ, {"ALERTAS_TOKEN": ""}):
            r = self.client.patch(
                f"/api/alertas/{ident}",
                json={"activa": False},
                headers=self._auth(),
            )
        self.assertEqual(r.status_code, 503)
        self.assertIn(titulo, self._titulos())

    def test_filtros_inactiva_y_etiquetada_son_and(self):
        titulo = self._titulo_fixture("and-flags")
        self._insertar(titulo=titulo, activa=False, etiqueta="test")
        self.assertNotIn(titulo, self._titulos())
        self.assertNotIn(
            titulo, self._titulos(params={"incluir_inactivas": True})
        )
        self.assertNotIn(
            titulo, self._titulos(params={"incluir_etiquetadas": True})
        )
        self.assertIn(
            titulo,
            self._titulos(
                params={
                    "incluir_inactivas": True,
                    "incluir_etiquetadas": True,
                }
            ),
        )

    def test_escritura_sin_alertas_token_503(self):
        titulo = self._titulo_fixture("post-503")
        cuerpo = {
            "tipo": "dengue",
            "nivel": "informativo",
            "titulo": titulo,
            "contexto": "x",
            "indicaciones": "y",
            "fuente": "z",
            "autor": "suite",
            "vigente_desde": "2026-09-07",
        }
        with patch.dict(os.environ, {"ALERTAS_TOKEN": ""}):
            r = self.client.post(
                "/api/alertas", json=cuerpo, headers=self._auth()
            )
        self.assertEqual(r.status_code, 503)
        self.assertEqual(self._contar_titulo(titulo), 0)

    def test_post_cuerpo_malformado_422(self):
        with patch.dict(os.environ, {"ALERTAS_TOKEN": TOKEN_DUMMY}):
            r = self.client.post(
                "/api/alertas", json={"titulo": "no"}, headers=self._auth()
            )
        self.assertEqual(r.status_code, 422)

    def test_delete_no_existe(self):
        r = self.client.delete("/api/alertas/1")
        self.assertEqual(r.status_code, 405)

    def test_contenido_clinico_citado_por_tipo(self):
        r = self.client.get("/api/alertas")
        self.assertEqual(r.status_code, 200)
        por_tipo = {}
        for alerta in r.json()["alertas"]:
            por_tipo.setdefault(alerta["tipo"], alerta)
        dengue = por_tipo["dengue"]
        self.assertIn("VIGEPES", dengue["definicion_caso"])
        self.assertIn("Dengue sin signos de alarma", dengue["definicion_caso"])
        self.assertIn("Dolor abdominal intenso", dengue["signos_alarma"])
        self.assertIn("Se sugiere hospitalizar", dengue["criterios_referencia"])
        self.assertIn("VIGEPES-01", dengue["que_notificar"])
        self.assertIn("SIBASI", dengue["contacto_vigilancia"])
        self.assertIn("VIGEPES-01", dengue["contacto_vigilancia"])
        self.assertNotIn("@", dengue["contacto_vigilancia"])
        self.assertNotIn("[PENDIENTE]", dengue["contacto_vigilancia"])
        self.assertNotRegex(dengue["contacto_vigilancia"], r"\+503")
        self.assertNotRegex(
            dengue["contacto_vigilancia"].lower(), r"tel[eé]fono"
        )
        self.assertNotRegex(dengue["contacto_vigilancia"].lower(), r"correo")

        r_resp = self.client.get(
            "/api/alertas", params={"tipo": "respiratorio"}
        )
        self.assertEqual(r_resp.status_code, 200)
        resp = r_resp.json()["alertas"][0]
        self.assertIn("Neumonías", resp["definicion_caso"])
        self.assertIn("VIGEPES", resp["definicion_caso"])
        self.assertIn("IRAGI", resp["que_notificar"])
        self.assertIsNone(resp["signos_alarma"])
        self.assertIsNone(resp["criterios_referencia"])
        self.assertIn("SIBASI", resp["contacto_vigilancia"])
        self.assertNotIn("@", resp["contacto_vigilancia"])
        self.assertNotIn("[PENDIENTE]", resp["contacto_vigilancia"])
