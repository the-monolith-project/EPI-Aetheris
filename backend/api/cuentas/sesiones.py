"""Sesiones de servidor con identificador opaco.

La cookie lleva 256 bits aleatorios; en la base solo está su SHA-256, así que
una copia de la tabla no sirve para entrar. El identificador se rota en cada
cambio de privilegio (ingreso, segundo factor, reautenticación, cambio de rol).
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime

from .config import ConfigCuentas


def _hash(token: str) -> bytes:
    return hashlib.sha256(token.encode("ascii", errors="ignore")).digest()


@dataclass(frozen=True)
class Sesion:
    id: str
    usuario_id: str
    nivel: str
    metodos: tuple[str, ...]
    roles: frozenset[str]
    correo: str
    nombre_visible: str
    autenticacion_reciente_en: datetime | None
    creada_en: datetime

    @property
    def es_administrador(self) -> bool:
        return "administrador" in self.roles

    @property
    def usa_llave(self) -> bool:
        return "webauthn" in self.metodos


def _limites(config: ConfigCuentas, es_admin: bool, nivel: str) -> tuple[int, int]:
    """(inactividad, vida absoluta) en segundos."""
    if nivel != "completo":
        return config.sesion_segundo_factor_s, config.sesion_segundo_factor_s
    if es_admin:
        return config.inactividad_admin_s, config.absoluta_admin_s
    return config.inactividad_publica_s, config.absoluta_publica_s


def crear(
    conn,
    config: ConfigCuentas,
    *,
    usuario_id: str,
    nivel: str,
    metodos: list[str],
    agente: str | None = None,
    red: str | None = None,
    reciente: bool = False,
) -> tuple[str, str]:
    """Devuelve (token en claro, id de sesión). Respeta el máximo de sesiones
    completas por persona cerrando las más antiguas."""
    token = secrets.token_urlsafe(32)
    es_admin = _es_admin(conn, usuario_id)
    _, absoluta = _limites(config, es_admin, nivel)
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO sesiones (token_hash, usuario_id, creada_en, caduca_absoluta_en, nivel, metodos, "
            "agente_resumen, red_truncada, autenticacion_reciente_en) "
            "VALUES (%s, %s, clock_timestamp(), now() + make_interval(secs => %s), %s, %s, %s, %s, "
            "CASE WHEN %s THEN now() ELSE NULL END) RETURNING id",
            (_hash(token), usuario_id, absoluta, nivel, metodos, (agente or "")[:200] or None, red, reciente),
        )
        sesion_id = str(cur.fetchone()[0])
        cur.execute(
            "UPDATE sesiones SET revocada_en = now(), revocada_motivo = 'limite_de_sesiones' "
            "WHERE id IN (SELECT id FROM sesiones WHERE usuario_id = %s AND revocada_en IS NULL "
            "AND nivel = 'completo' ORDER BY creada_en DESC OFFSET %s)",
            (usuario_id, config.max_sesiones),
        )
    return token, sesion_id


def _es_admin(conn, usuario_id: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM usuarios_roles WHERE usuario_id = %s AND rol = 'administrador' AND revocado_en IS NULL",
            (usuario_id,),
        )
        return cur.fetchone() is not None


def obtener(conn, config: ConfigCuentas, token: str | None) -> Sesion | None:
    """Sesión vigente para el token de la cookie, o None. Aplica inactividad,
    vida absoluta y estado de la cuenta, y renueva la última actividad."""
    if not token:
        return None
    with conn.cursor() as cur:
        cur.execute(
            "SELECT s.id, s.usuario_id, s.nivel, s.metodos, s.autenticacion_reciente_en, s.creada_en, "
            "       s.ultima_actividad_en, s.caduca_absoluta_en, u.correo, u.nombre_visible, "
            "       COALESCE(array_agg(r.rol) FILTER (WHERE r.rol IS NOT NULL), '{}') "
            "FROM sesiones s JOIN usuarios u ON u.id = s.usuario_id "
            "LEFT JOIN usuarios_roles r ON r.usuario_id = u.id AND r.revocado_en IS NULL "
            "WHERE s.token_hash = %s AND s.revocada_en IS NULL AND (u.estado = 'activo' OR (s.nivel = 'alta_pendiente' AND u.estado = 'invitado')) "
            "GROUP BY s.id, u.id",
            (_hash(token),),
        )
        fila = cur.fetchone()
        if fila is None:
            return None
        (sid, uid, nivel, metodos, reciente, creada, ultima, absoluta, correo, nombre, roles) = fila
        cur.execute(
            "SELECT now() > %s, EXTRACT(EPOCH FROM (now() - %s))", (absoluta, ultima)
        )
        vencida, inactiva_s = cur.fetchone()
        roles = frozenset(roles)
        inactividad, _ = _limites(config, "administrador" in roles, nivel)
        if vencida or inactiva_s > inactividad:
            cur.execute(
                "UPDATE sesiones SET revocada_en = now(), revocada_motivo = %s WHERE id = %s",
                ("caducada" if vencida else "inactividad", sid),
            )
            return None
        cur.execute("UPDATE sesiones SET ultima_actividad_en = now() WHERE id = %s", (sid,))
    return Sesion(
        id=str(sid),
        usuario_id=str(uid),
        nivel=nivel,
        metodos=tuple(metodos),
        roles=roles,
        correo=correo,
        nombre_visible=nombre,
        autenticacion_reciente_en=reciente,
        creada_en=creada,
    )


def rotar(
    conn,
    config: ConfigCuentas,
    sesion_id: str,
    *,
    nivel: str | None = None,
    agregar_metodo: str | None = None,
    reautenticar: bool = False,
) -> str:
    """Cambia el identificador de la sesión y, si se pide, su nivel y métodos.
    Devuelve el nuevo token; el anterior deja de valer."""
    token = secrets.token_urlsafe(32)
    with conn.cursor() as cur:
        cur.execute("SELECT usuario_id FROM sesiones WHERE id = %s AND revocada_en IS NULL", (sesion_id,))
        fila = cur.fetchone()
        if fila is None:
            raise LookupError("sesión inexistente o revocada")
        es_admin = _es_admin(conn, str(fila[0]))
        _, absoluta = _limites(config, es_admin, nivel or "completo")
        cur.execute(
            "UPDATE sesiones SET token_hash = %s, "
            "nivel = COALESCE(%s, nivel), "
            "metodos = CASE WHEN %s::text IS NULL OR %s::text = ANY(metodos) THEN metodos "
            "          ELSE array_append(metodos, %s::text) END, "
            "autenticacion_reciente_en = CASE WHEN %s THEN now() ELSE autenticacion_reciente_en END, "
            "ultima_actividad_en = now(), "
            "caduca_absoluta_en = CASE WHEN %s::text IS NOT NULL "
            "   THEN creada_en + make_interval(secs => %s) ELSE caduca_absoluta_en END "
            "WHERE id = %s",
            (
                _hash(token), nivel, agregar_metodo, agregar_metodo, agregar_metodo,
                reautenticar, nivel, absoluta, sesion_id,
            ),
        )
    return token


def revocar(conn, sesion_id: str, motivo: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE sesiones SET revocada_en = now(), revocada_motivo = %s WHERE id = %s AND revocada_en IS NULL",
            (motivo, sesion_id),
        )


def revocar_todas(conn, usuario_id: str, motivo: str, *, excepto: str | None = None) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE sesiones SET revocada_en = now(), revocada_motivo = %s "
            "WHERE usuario_id = %s AND revocada_en IS NULL AND (%s::uuid IS NULL OR id <> %s::uuid)",
            (motivo, usuario_id, excepto, excepto),
        )
        return cur.rowcount


def reautenticada(sesion: Sesion, config: ConfigCuentas, ahora: datetime) -> bool:
    if sesion.autenticacion_reciente_en is None:
        return False
    return (ahora - sesion.autenticacion_reciente_en).total_seconds() <= config.reautenticacion_s
