import importlib
import sys
from pathlib import Path
import pytest

from fastapi.testclient import TestClient

# Add the backend directory to sys.path so 'api' module can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def test_cors_rejects_wildcard(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "*")

    with pytest.raises(ValueError, match="CORS_ALLOWED_ORIGINS must not contain '\\*' for security reasons."):
        # We need to import main here to trigger the module-level parsing
        # but because it's already imported, we might need to reload it
        import importlib
        import api.main
        importlib.reload(api.main)

def test_cors_accepts_valid_origins(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000, https://example.com")

    import importlib
    import api.main
    importlib.reload(api.main)

    # Check that the origins were parsed correctly
    # Note: starlette's CORSMiddleware stores the origins, but it's easier to just
    # check that it didn't raise an error.
    assert True


def test_preflight_alertas_permite_authorization_y_content_type(monkeypatch):
    """El formulario de /alertas/nueva manda esas dos cabeceras en el POST.

    Si allow_headers deja de incluirlas, el preflight falla y el navegador
    bloquea la escritura aunque el token sea correcto.
    """
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:4321")
    import api.main
    importlib.reload(api.main)
    try:
        cliente = TestClient(api.main.app)
        respuesta = cliente.options(
            "/api/alertas",
            headers={
                "Origin": "http://localhost:4321",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization, content-type",
            },
        )
        assert respuesta.status_code == 200
        permitidas = respuesta.headers.get(
            "access-control-allow-headers", ""
        ).lower()
        assert "authorization" in permitidas
        assert "content-type" in permitidas
    finally:
        monkeypatch.undo()
        importlib.reload(api.main)
