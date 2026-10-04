"""Límite de intentos de ingreso por cuenta y por red, guardado en la base
para que sobreviva a los reinicios del servicio. La clave es un HMAC del
correo o de la IP, nunca el valor en claro."""

from __future__ import annotations

import hashlib
import hmac

from .config import ConfigCuentas


def clave(config: ConfigCuentas, tipo: str, valor: str) -> bytes:
    return hmac.new(config.pimienta_vigente, f"{tipo}|{valor.strip().lower()}".encode("utf-8"), hashlib.sha256).digest()


def segundos_de_espera(config: ConfigCuentas, conn, k: bytes) -> int:
    """Segundos que faltan para poder intentar de nuevo; 0 si puede."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(max(EXTRACT(EPOCH FROM (bloqueado_hasta - now()))), 0) "
            "FROM intentos_ingreso WHERE clave = %s AND bloqueado_hasta > now()",
            (k,),
        )
        return max(0, int(cur.fetchone()[0]))


def registrar_fallo(config: ConfigCuentas, conn, k: bytes) -> None:
    """Cuenta un fallo en la ventana vigente. Al pasar el máximo, bloquea con
    una espera que crece (30 s, 1 min, 2 min... hasta 15 min)."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO intentos_ingreso (clave, ventana_inicio, fallos) "
            "VALUES (%s, date_trunc('minute', now()), 1) "
            "ON CONFLICT (clave, ventana_inicio) DO UPDATE SET fallos = intentos_ingreso.fallos + 1",
            (k,),
        )
        cur.execute(
            "SELECT COALESCE(sum(fallos), 0) FROM intentos_ingreso "
            "WHERE clave = %s AND ventana_inicio > now() - make_interval(secs => %s)",
            (k, config.ventana_fallos_s),
        )
        total = int(cur.fetchone()[0])
        if total >= config.max_fallos_cuenta:
            exceso = total - config.max_fallos_cuenta
            espera = min(900, 30 * (2**exceso))
            cur.execute(
                "UPDATE intentos_ingreso SET bloqueado_hasta = now() + make_interval(secs => %s) "
                "WHERE clave = %s AND ventana_inicio = date_trunc('minute', now())",
                (espera, k),
            )


def limpiar(conn, k: bytes) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM intentos_ingreso WHERE clave = %s", (k,))
