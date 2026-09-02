"""
Endpoints de vigilancia laboratorial de virus respiratorios (ADR 0012).

Nacional, no departamental. Distingue muestras / detecciones / positividad.
No convierte porcentajes en casos. No afirma causalidad.
"""

from __future__ import annotations

from collections import defaultdict

AVISO_HONESTIDAD_VIRUS = (
    "Vigilancia centinela/laboratorial MINSAL, nivel NACIONAL: muestras analizadas, "
    "detecciones por virus y positividad publicada por la fuente. No son casos "
    "clínicos ni se desagregan por departamento -- no hay mapa. La positividad no se "
    "recalcula. SARS-CoV-2 aparece como 'covid_19' solo en 2023. Huecos = semanas "
    "sin fila. Coexistencia temporal con IRA/Neumonías no demuestra causalidad."
)


def listar_virus(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT virus, metrica, unidad, min(anio), max(anio), count(*)
            FROM vigilancia_virus_respiratorios
            GROUP BY virus, metrica, unidad
            ORDER BY virus, metrica
            """
        )
        filas = cur.fetchall()
    return [
        {
            "virus": virus,
            "metrica": metrica,
            "unidad": unidad,
            "primer_anio": primer,
            "ultimo_anio": ultimo,
            "semanas_con_dato": int(n),
        }
        for virus, metrica, unidad, primer, ultimo, n in filas
    ]


def serie_virus(conn, virus: str, metrica: str) -> tuple[dict[int, dict[int, float]], str | None]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT anio, semana_epi, valor, unidad
            FROM vigilancia_virus_respiratorios
            WHERE virus = %s AND metrica = %s
            ORDER BY anio, semana_epi
            """,
            (virus, metrica),
        )
        filas = cur.fetchall()
    serie: dict[int, dict[int, float]] = defaultdict(dict)
    unidad = None
    for anio, semana, valor, uni in filas:
        serie[anio][semana] = float(valor)
        unidad = uni
    return dict(serie), unidad


def semana_virus(conn, anio: int, semana: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT virus, metrica, valor, unidad
            FROM vigilancia_virus_respiratorios
            WHERE anio = %s AND semana_epi = %s
            ORDER BY virus, metrica
            """,
            (anio, semana),
        )
        filas = cur.fetchall()
    return [
        {"virus": v, "metrica": m, "valor": float(val), "unidad": u}
        for v, m, val, u in filas
    ]
