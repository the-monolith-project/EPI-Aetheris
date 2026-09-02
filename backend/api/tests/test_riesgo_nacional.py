"""Degradacion elegante de /api/riesgo-nacional (issue #72).

Los artefactos del clasificador historico (dataset_modelado.csv + joblib +
metricas) estan en .gitignore y no se generan en el build de Render, asi que
faltan en produccion. El endpoint no debe responder 503: responde 200 con
disponible=false para que el frontend muestre un aviso explicito.
"""
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient  # noqa: E402

import api.main  # noqa: E402

_ARTEFACTOS_PRESENTES = (
    api.main.DATASET_RIESGO_PATH.exists() and api.main.MODELO_PATH.exists()
)


@pytest.fixture
def client():
    api.main._modelo_cache = None
    api.main._dataset_riesgo_cache = None
    return TestClient(api.main.app)


@pytest.mark.skipif(
    _ARTEFACTOS_PRESENTES,
    reason="Los artefactos del modelo existen en este checkout; no hay caso degradado que probar.",
)
def test_sin_artefactos_responde_200_disponible_false(client):
    respuesta = client.get("/api/riesgo-nacional")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["disponible"] is False
    assert "motivo" in cuerpo
    assert cuerpo["aviso"]


@pytest.mark.skipif(
    not _ARTEFACTOS_PRESENTES,
    reason="Los artefactos del modelo no existen en este checkout.",
)
def test_con_artefactos_responde_disponible_true(client):
    respuesta = client.get("/api/riesgo-nacional")
    assert respuesta.status_code == 200
    assert respuesta.json()["disponible"] is True
