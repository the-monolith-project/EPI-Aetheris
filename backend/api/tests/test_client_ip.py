"""key_func del rate limiter: de que valor de X-Forwarded-For sale la IP (issue #67).

El edge de Render ANEXA la IP real del cliente al final de X-Forwarded-For.
Tomar el primer valor deja que el cliente se bucketice como una IP distinta en
cada request (mandando la cabecera ya seteada) y evada el rate limiter.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from starlette.requests import Request  # noqa: E402

import api.main  # noqa: E402


def _request(xff: str | None = None) -> Request:
    headers = []
    if xff is not None:
        headers.append((b"x-forwarded-for", xff.encode()))
    return Request({"type": "http", "headers": headers, "client": ("10.9.9.9", 5555)})


def test_toma_el_ultimo_hop():
    assert api.main._client_ip(_request("1.2.3.4, 200.0.0.1")) == "200.0.0.1"


def test_un_primer_valor_falsificado_no_cambia_el_bucket():
    a = api.main._client_ip(_request("1.1.1.1, 200.0.0.1"))
    b = api.main._client_ip(_request("9.9.9.9, 200.0.0.1"))
    assert a == b == "200.0.0.1"


def test_sin_cabecera_cae_a_la_ip_del_socket():
    assert api.main._client_ip(_request()) == "10.9.9.9"


def test_cabecera_vacia_cae_a_la_ip_del_socket():
    assert api.main._client_ip(_request("   ")) == "10.9.9.9"
