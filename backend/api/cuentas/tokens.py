"""Tokens de un solo uso: invitación, restablecer contraseña, verificar correo.

El token tiene 256 bits y solo se guarda su SHA-256. Se consume con un único
UPDATE condicionado, de modo que dos peticiones simultáneas con el mismo token
no pueden ganar las dos.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass


def generar() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> bytes:
    return hashlib.sha256(token.encode("ascii", errors="ignore")).digest()


@dataclass(frozen=True)
class TokenConsumido:
    id: str
    usuario_id: str
    correo_destino: str | None


def emitir(conn, *, proposito: str, usuario_id: str, caduca_s: int, correo_destino: str | None = None) -> str:
    """Crea un token nuevo y deja sin efecto los anteriores del mismo
    propósito para esa persona. Devuelve el token en claro, que solo existe
    aquí y en el correo."""
    token = generar()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE tokens_un_solo_uso SET usado_en = now() "
            "WHERE usuario_id = %s AND proposito = %s AND usado_en IS NULL",
            (usuario_id, proposito),
        )
        cur.execute(
            "INSERT INTO tokens_un_solo_uso (proposito, usuario_id, correo_destino, token_hash, caduca_en) "
            "VALUES (%s, %s, %s, %s, now() + make_interval(secs => %s))",
            (proposito, usuario_id, correo_destino, hash_token(token), caduca_s),
        )
    return token


def consumir(conn, *, proposito: str, token: str) -> TokenConsumido | None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE tokens_un_solo_uso SET usado_en = now() "
            "WHERE token_hash = %s AND proposito = %s AND usado_en IS NULL AND caduca_en > now() "
            "RETURNING id, usuario_id, correo_destino",
            (hash_token(token), proposito),
        )
        fila = cur.fetchone()
    if fila is None:
        return None
    return TokenConsumido(id=str(fila[0]), usuario_id=str(fila[1]), correo_destino=fila[2])
