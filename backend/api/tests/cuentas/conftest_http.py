"""Aplicación de pruebas con solo el router de cuentas.

Comparte una conexión con la prueba y convierte commit/rollback en no-ops: el
fixture `conn` deshace todo al terminar. Así las pruebas HTTP no dejan filas en
la base aunque las rutas confirmen sus transacciones."""

from __future__ import annotations

from contextlib import contextmanager

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from api.cuentas import correo, rutas


class ConexionCompartida:
    def __init__(self, real):
        self._real = real

    def commit(self):  # lo deshace el fixture
        pass

    def rollback(self):
        pass

    def __getattr__(self, nombre):
        return getattr(self._real, nombre)


def crear_app(conn, config, *, limite_auth="1000/minute", limiter_activo=False):
    remitente = correo.RemitenteEnMemoria()
    limiter = Limiter(key_func=get_remote_address, enabled=limiter_activo)
    compartida = ConexionCompartida(conn)

    @contextmanager
    def abrir():
        yield compartida

    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    app.include_router(
        rutas.crear_router(
            limiter=limiter, abrir_conexion=abrir, limite_auth=limite_auth,
            config_fn=lambda: config, remitente=remitente, ip_fn=get_remote_address,
        )
    )
    return app, remitente
