"""Escritura en la auditoría encadenada. El hash lo calcula el disparador de
la migración 0016; aquí solo se agregan filas. Nunca va un secreto en `detalle`."""

from __future__ import annotations

import ipaddress
import json

CATEGORIAS = ("seguridad", "administracion", "contenido", "sistema")
_CAMPOS_PROHIBIDOS = ("contrasena", "clave", "token", "codigo", "secreto", "pimienta")


def _sin_secretos(detalle: dict) -> dict:
    for llave in detalle:
        if any(p in llave.lower() for p in _CAMPOS_PROHIBIDOS):
            raise ValueError(f"El detalle de auditoría no puede incluir '{llave}'")
    return detalle


def registrar(
    conn,
    *,
    categoria: str,
    accion: str,
    actor_tipo: str = "usuario",
    actor_id: str | None = None,
    sesion_id: str | None = None,
    objeto_tipo: str | None = None,
    objeto_id: str | None = None,
    detalle: dict | None = None,
    red_truncada: str | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO auditoria (categoria, actor_tipo, actor_id, sesion_id, accion, "
            "objeto_tipo, objeto_id, detalle, red_truncada) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)",
            (
                categoria,
                actor_tipo,
                actor_id,
                sesion_id,
                accion,
                objeto_tipo,
                objeto_id,
                json.dumps(_sin_secretos(detalle or {}), ensure_ascii=False, sort_keys=True),
                red_truncada,
            ),
        )


def verificar_cadena(conn) -> int | None:
    """Id de la primera fila que no cuadra, o None si la cadena es íntegra."""
    with conn.cursor() as cur:
        cur.execute("SELECT auditoria_verificar()")
        return cur.fetchone()[0]


def truncar_red(ip: str | None) -> str | None:
    """Guarda la red, no la dirección: /24 en IPv4 y /48 en IPv6."""
    if not ip:
        return None
    try:
        direccion = ipaddress.ip_address(ip)
    except ValueError:
        return None
    prefijo = 24 if direccion.version == 4 else 48
    return str(ipaddress.ip_network(f"{direccion}/{prefijo}", strict=False))
