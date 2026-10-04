"""Protección contra CSRF: SameSite=Strict, comprobación de Origin y un token
derivado de la sesión que el navegador manda en `X-CSRF-Token`."""

from __future__ import annotations

import hashlib
import hmac

from .config import ConfigCuentas

METODOS_SEGUROS = frozenset({"GET", "HEAD", "OPTIONS"})


def token_para_sesion(config: ConfigCuentas, sesion_id: str) -> str:
    return hmac.new(config.pimienta_vigente, b"csrf|" + sesion_id.encode("ascii"), hashlib.sha256).hexdigest()


def origen_valido(config: ConfigCuentas, origen: str | None) -> bool:
    # Sin Origin no se acepta: un navegador lo manda en toda petición que no sea GET.
    return origen is not None and origen.rstrip("/") == config.origen_canonico


def token_valido(config: ConfigCuentas, sesion_id: str, recibido: str | None) -> bool:
    return bool(recibido) and hmac.compare_digest(token_para_sesion(config, sesion_id), recibido)
