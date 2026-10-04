"""CUENTAS_HABILITADAS monta o no las rutas de cuentas en la API (ADR 0024).

Como API_DOCS_ENABLED, se lee al importar api.main: cada prueba recarga el
módulo y el finally lo deja como estaba."""
import base64
import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

CLAVE = base64.urlsafe_b64encode(b"\x07" * 32).decode()


def _recargar(monkeypatch, habilitadas, *, con_claves=False):
    monkeypatch.setenv("CUENTAS_HABILITADAS", habilitadas)
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://epi-aetheris.dev")
    for nombre in ("AUTH_PEPPERS", "AUTH_CLAVES_CIFRADO"):
        if con_claves:
            monkeypatch.setenv(nombre, f"1:{CLAVE}")
        else:
            monkeypatch.delenv(nombre, raising=False)
    import api.main

    return importlib.reload(api.main)


def _restaurar(monkeypatch):
    monkeypatch.undo()
    import api.main

    importlib.reload(api.main)


def _preflight(modulo, ruta="/api/cuenta/ingresar"):
    return TestClient(modulo.app).options(
        ruta,
        headers={
            "origin": "https://epi-aetheris.dev",
            "access-control-request-method": "POST",
            "access-control-request-headers": "content-type,x-csrf-token",
        },
    )


def test_apagadas_no_hay_rutas_de_cuentas_ni_credenciales_en_cors(monkeypatch):
    modulo = _recargar(monkeypatch, "false")
    try:
        cliente = TestClient(modulo.app)
        assert cliente.post("/api/cuenta/ingresar", json={}).status_code in (404, 405)
        assert cliente.get("/api/admin/usuarios").status_code == 404
        r = _preflight(modulo, "/api/alertas")
        assert "access-control-allow-credentials" not in r.headers
        assert "x-csrf-token" not in r.headers.get("access-control-allow-headers", "").lower()
    finally:
        _restaurar(monkeypatch)


def test_habilitadas_sin_claves_responden_503_y_la_api_arranca(monkeypatch):
    modulo = _recargar(monkeypatch, "true")
    try:
        cliente = TestClient(modulo.app)
        r = cliente.post("/api/cuenta/ingresar", headers={"origin": "https://epi-aetheris.dev"}, json={"correo": "a@b.org", "contrasena": "x"})
        assert r.status_code == 503
        assert cliente.get("/health").status_code in (200, 503)
    finally:
        _restaurar(monkeypatch)


def test_habilitadas_cors_con_credenciales_y_csrf_solo_para_el_origen_canonico(monkeypatch):
    modulo = _recargar(monkeypatch, "true", con_claves=True)
    try:
        r = _preflight(modulo)
        assert r.status_code == 200
        assert r.headers["access-control-allow-credentials"] == "true"
        assert r.headers["access-control-allow-origin"] == "https://epi-aetheris.dev"
        assert "x-csrf-token" in r.headers["access-control-allow-headers"].lower()
        ajeno = TestClient(modulo.app).options(
            "/api/cuenta/ingresar",
            headers={"origin": "https://evil.example", "access-control-request-method": "POST"},
        )
        assert ajeno.status_code == 400 or "access-control-allow-origin" not in ajeno.headers
    finally:
        _restaurar(monkeypatch)


def test_la_sesion_anonima_responde_con_claves(monkeypatch):
    modulo = _recargar(monkeypatch, "true", con_claves=True)
    try:
        r = TestClient(modulo.app).get("/api/cuenta/sesion")
        assert r.status_code == 200 and r.json() == {"autenticada": False}
        assert r.headers["x-content-type-options"] == "nosniff"
    finally:
        _restaurar(monkeypatch)
