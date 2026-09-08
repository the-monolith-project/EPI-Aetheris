"""Cabeceras de SecurityHeadersMiddleware.

No hace falta recargar el modulo: las cabeceras se escriben en cada
respuesta y no dependen de env leido en import.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient  # noqa: E402

import api.main  # noqa: E402

CABECERAS_ESPERADAS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "x-xss-protection": "1; mode=block",
    "strict-transport-security": "max-age=31536000; includeSubDomains",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "geolocation=(), camera=(), microphone=(), payment=()",
}


def test_respuesta_trae_cabeceras_de_seguridad():
    # /openapi.json no toca la BD ni esta exento; basta una respuesta 200.
    cliente = TestClient(api.main.app)
    respuesta = cliente.get("/openapi.json")
    assert respuesta.status_code == 200
    for nombre, valor in CABECERAS_ESPERADAS.items():
        assert respuesta.headers.get(nombre) == valor, nombre
    assert "content-security-policy" in respuesta.headers
    csp = respuesta.headers["content-security-policy"]
    assert "default-src 'self'" in csp
