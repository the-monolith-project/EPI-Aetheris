"""Códigos de recuperación: diez códigos de un solo uso que reemplazan al
segundo factor si se pierde. Se muestran una vez y se guardan como SHA-256;
con 80 bits de entropía no hace falta un hash lento."""

from __future__ import annotations

import hashlib
import secrets
import uuid

CANTIDAD = 10
# Sin 0, O, 1, I ni L, para que se puedan copiar a mano sin confusión.
_ALFABETO = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def _nuevo() -> str:
    letras = "".join(secrets.choice(_ALFABETO) for _ in range(16))
    return "-".join(letras[i : i + 4] for i in range(0, 16, 4))


def normalizar(codigo: str) -> str:
    return "".join(c for c in codigo.upper() if c.isalnum())


def hash_codigo(codigo: str) -> bytes:
    return hashlib.sha256(normalizar(codigo).encode("ascii", errors="ignore")).digest()


def generar_lote(conn, usuario_id: str) -> list[str]:
    """Invalida los códigos anteriores y devuelve los nuevos en claro."""
    lote = str(uuid.uuid4())
    codigos = [_nuevo() for _ in range(CANTIDAD)]
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE codigos_recuperacion SET usado_en = now() WHERE usuario_id = %s AND usado_en IS NULL",
            (usuario_id,),
        )
        for codigo in codigos:
            cur.execute(
                "INSERT INTO codigos_recuperacion (usuario_id, hash, lote) VALUES (%s, %s, %s)",
                (usuario_id, hash_codigo(codigo), lote),
            )
    return codigos


def consumir(conn, usuario_id: str, codigo: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE codigos_recuperacion SET usado_en = now() "
            "WHERE usuario_id = %s AND hash = %s AND usado_en IS NULL RETURNING id",
            (usuario_id, hash_codigo(codigo)),
        )
        return cur.fetchone() is not None


def restantes(conn, usuario_id: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM codigos_recuperacion WHERE usuario_id = %s AND usado_en IS NULL",
            (usuario_id,),
        )
        return cur.fetchone()[0]
