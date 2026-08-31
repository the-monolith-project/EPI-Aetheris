"""Rate limiting de la API (issue #61).

Mismo idiom que test_cors.py: se reactiva el rate limiting vía monkeypatch de
variables de entorno + importlib.reload(api.main), porque el módulo lee la
configuración a nivel de import y conftest.py lo desactiva para el resto de la
suite.
"""
import importlib
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def client_con_limite(monkeypatch):
    """TestClient con rate limiting activo y límites diminutos."""
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_DEFAULT", "3/minute")
    monkeypatch.setenv("RATE_LIMIT_HEAVY", "2/minute")

    import api.main
    importlib.reload(api.main)
    try:
        yield TestClient(api.main.app)
    finally:
        # Deja el módulo en el estado por defecto (sin límite) para no
        # contaminar a otros tests que importen api.main después.
        monkeypatch.undo()
        importlib.reload(api.main)


def test_limite_global_devuelve_429(client_con_limite):
    # /openapi.json es una ruta real (no exenta, sin decorador) y no toca la BD.
    codigos = [client_con_limite.get("/openapi.json").status_code for _ in range(6)]
    assert codigos[:3] == [200, 200, 200]
    assert 429 in codigos[3:]


def test_health_esta_exento(client_con_limite):
    # Render sondea /health continuamente; nunca debe recibir 429.
    codigos = {client_con_limite.get("/health").status_code for _ in range(10)}
    assert 429 not in codigos


def test_429_conserva_cabeceras_cors(client_con_limite):
    origin = "http://localhost:4321"
    respuesta = None
    for _ in range(6):
        respuesta = client_con_limite.get("/openapi.json", headers={"Origin": origin})
    assert respuesta.status_code == 429
    # Si SlowAPIMiddleware quedara por fuera de CORSMiddleware, la 429 no
    # llevaría esta cabecera y el frontend Astro vería un error de red opaco.
    assert respuesta.headers.get("access-control-allow-origin") == origin


def test_endpoint_pesado_tiene_umbral_propio(client_con_limite):
    # Límite HEAVY = 2/min, más estricto que el global (3/min). No depende de
    # que la BD esté arriba: el chequeo de rate limit corre antes del handler.
    # Los endpoints decorados lanzan RateLimitExceeded y lo maneja
    # ExceptionMiddleware (ruta distinta a la del middleware global), así que
    # verificamos también que esa 429 conserva las cabeceras CORS.
    origin = "http://localhost:4321"
    respuestas = [
        client_con_limite.get(
            "/api/v1/spatial/current",
            params={"week": 30, "year": 2023},
            headers={"Origin": origin},
        )
        for _ in range(4)
    ]
    codigos = [r.status_code for r in respuestas]
    assert codigos.count(429) >= 2
    assert 429 not in codigos[:2]
    respuesta_429 = next(r for r in respuestas if r.status_code == 429)
    assert respuesta_429.headers.get("access-control-allow-origin") == origin
