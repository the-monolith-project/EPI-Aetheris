"""Cabeceras Cache-Control (tarea de rendimiento: sin ellas el navegador no
reutiliza ninguna respuesta de solo lectura, aunque el dato no cambie hasta
la proxima corrida de ingesta). Mismo patron de deteccion de Postgres que
test_endpoints_analisis.py: se omite si la BD no esta arriba.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg2
import pytest
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


@pytest.fixture(scope="module")
def client():
    if not _db_disponible():
        pytest.skip("Postgres no disponible -- se omite la suite de cabeceras de cache.")
    return TestClient(app)


def test_health_no_store(client):
    # /health lo sondea Render continuamente -- cachear un "ok" viejo
    # derrotaria el proposito del chequeo.
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.headers.get("cache-control") == "no-store"


def test_casos_nacional_cache_historico(client):
    # Serie ya cargada en Postgres, solo cambia con una corrida de ingesta
    # nueva -- TTL largo (CACHE_TTL_HISTORICO).
    respuesta = client.get("/api/casos-nacional")
    assert respuesta.status_code == 200
    assert respuesta.headers.get("cache-control") == "public, max-age=3600"


def test_spatial_current_cache_computo(client):
    # Capa recalculada on-demand en cada request -- TTL mas corto
    # (CACHE_TTL_COMPUTO). Semana/anio con datos climaticos conocidos en el
    # seed (ver test_endpoints_analisis.py).
    respuesta = client.get("/api/v1/spatial/current", params={"week": 24, "year": 2019})
    assert respuesta.status_code == 200
    assert respuesta.headers.get("cache-control") == "public, max-age=900"
