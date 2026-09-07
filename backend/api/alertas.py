"""Consulta pública de alertas de campo (ADR 0013).

Las filas las redacta el equipo de vigilancia. Este módulo solo las lee.
No calcula nivel desde M1/M2/M3 ni desde el clasificador retirado.
"""

from __future__ import annotations

from datetime import date

TIPOS_ALERTA = ("dengue", "respiratorio")
NIVELES_ALERTA = ("informativo", "atencion", "intensificacion")

AVISO_HONESTIDAD_ALERTAS = (
    "Herramienta académica en desarrollo (INSAMT, Equipo 4). Las alertas y sus "
    "indicaciones las redacta manualmente el equipo de vigilancia del proyecto a "
    "partir de datos públicos históricos (MINSAL, OpenDengue, Open-Meteo). No "
    "sustituyen los lineamientos oficiales del MINSAL ni el criterio clínico. No "
    "son tiempo real. La coexistencia temporal de eventos no demuestra causalidad."
)

_COLUMNAS = (
    "id, tipo, nivel, titulo, contexto, indicaciones, fuente, autor, "
    "vigente_desde, vigente_hasta, activa"
)


def _iso(valor: date | None) -> str | None:
    if valor is None:
        return None
    return valor.isoformat()


def _fila_publica(fila: tuple) -> dict:
    (
        ident,
        tipo,
        nivel,
        titulo,
        contexto,
        indicaciones,
        fuente,
        autor,
        vigente_desde,
        vigente_hasta,
        activa,
    ) = fila
    return {
        "id": int(ident),
        "tipo": tipo,
        "nivel": nivel,
        "titulo": titulo,
        "contexto": contexto,
        "indicaciones": indicaciones,
        "fuente": fuente,
        "autor": autor,
        "vigente_desde": _iso(vigente_desde),
        "vigente_hasta": _iso(vigente_hasta),
        "activa": bool(activa),
    }


def listar_alertas_activas(conn, tipo: str | None = None) -> list[dict]:
    """Filas con activa=TRUE, opcionalmente de un solo tipo.

    El filtro de `activa` vive aquí — no se reimplementa en el handler ni
    en los tests. `tipo` ya debe ser None o un valor de TIPOS_ALERTA.
    """
    sql = f"""
        SELECT {_COLUMNAS}
        FROM alertas
        WHERE activa = TRUE
    """
    params: tuple = ()
    if tipo is not None:
        sql += " AND tipo = %s"
        params = (tipo,)
    sql += " ORDER BY vigente_desde DESC, id DESC"

    with conn.cursor() as cur:
        cur.execute(sql, params)
        filas = cur.fetchall()
    return [_fila_publica(fila) for fila in filas]


def leer_ultima_revision(conn) -> str | None:
    """Fecha de la revisión más reciente del equipo (incluye inactivas)."""
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(vigente_desde) FROM alertas")
        (valor,) = cur.fetchone()
    return _iso(valor)


def consultar_alertas_publicas(conn, tipo: str | None = None) -> dict:
    """Cuerpo del GET público: aviso, última revisión y lista activa."""
    return {
        "aviso": AVISO_HONESTIDAD_ALERTAS,
        "ultima_revision": leer_ultima_revision(conn),
        "alertas": listar_alertas_activas(conn, tipo=tipo),
    }
